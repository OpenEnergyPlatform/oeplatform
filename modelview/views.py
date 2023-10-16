import csv
import datetime
import json
import os
import re
from collections import OrderedDict

import matplotlib
import matplotlib.pyplot as plt
import numpy
import urllib3
from django.conf import settings as djangoSettings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.fields import ArrayField
from django.contrib.staticfiles import finders
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    JsonResponse,
)  # noqa
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View
from django.views.decorators.cache import never_cache
from scipy import stats
from sqlalchemy.orm import sessionmaker

from api.actions import _get_engine
from dataedit.structures import Tag

from .forms import (
    EnergyframeworkForm,
    EnergymodelForm,
    EnergyscenarioForm,
    EnergystudyForm,
)
from .models import Energyframework, Energymodel, Energyscenario, Energystudy
from .rdf import connection, factory, namespace

_factory_mappings = {"study": factory.Study, "scenario": factory.Scenario}


def getClasses(sheettype):
    """
    Returns the model and form class w.r.t sheettype.
    """
    if sheettype == "model":
        c = Energymodel
        f = EnergymodelForm
    elif sheettype == "framework":
        c = Energyframework
        f = EnergyframeworkForm
    elif sheettype == "scenario":
        c = Energyscenario
        f = EnergyscenarioForm
    elif sheettype == "studie":
        c = Energystudy
        f = EnergystudyForm
    return c, f


def overview(request):
    return render(request, "modelview/overview.html")


def load_tags():
    engine = _get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    tags = list(session.query(Tag))
    d = {
        tag.id: {
            "id": tag.id,
            "name": tag.name,
            "color": "#" + format(tag.color, "06X"),
            "usage_count": tag.usage_count,
            "usage_tracked_since": tag.usage_tracked_since,
        }
        for tag in tags
    }
    session.close()
    return d


def listsheets(request, sheettype):
    """
    Lists all available model, framework or scenario factsheet objects.
    """
    c, _ = getClasses(sheettype)
    tags = []
    fields = {}
    defaults = set()
    if sheettype == "scenario":
        models = [(m.pk, m.name_of_scenario) for m in c.objects.all()]
    elif sheettype == "studie":
        raise Http404
    else:
        fields = (
            FRAMEWORK_VIEW_PROPS if sheettype == "framework" else MODEL_VIEW_PROPS # noqa
        )
        defaults = (
            FRAMEWORK_DEFAULT_COLUMNS
            if sheettype == "framework"
            else MODEL_DEFAULT_COLUMNS
        )
        d = load_tags()
        tags = sorted(d.values(), key=lambda d: d["name"])
        models = []

        for model in c.objects.all():
            model.tags = [d[tag_id] for tag_id in model.tags]
            models.append(model)
    if sheettype == "scenario":
        label = "Scenario"
    elif sheettype == "studie":
        label = "Study"
    elif sheettype == "framework":
        label = "Framework"
    else:
        label = "Model"
    return render(
        request,
        "modelview/modellist.html",
        {
            "models": models,
            "label": label,
            "tags": tags,
            "fields": fields,
            "default": defaults,
        },
    )


@never_cache
def show(request, sheettype, model_name):
    """
    Loads the requested factsheet
    """
    c, _ = getClasses(sheettype)
    model = get_object_or_404(c, pk=model_name)
    model_study = []
    if sheettype == "scenario":
        c_study, _ = getClasses("studie")
        model_study = get_object_or_404(c_study, pk=model.study.pk)
    else:
        d = load_tags()
        model.tags = [d[tag_id] for tag_id in model.tags]

    user_agent = {"user-agent": "oeplatform"}
    urllib3.PoolManager(headers=user_agent)
    org = None
    repo = None
    if sheettype != "scenario" and sheettype != "studie":
        if model.gitHub and model.link_to_source_code:
            try:
                match = re.match(
                    r".*github\.com\/(?P<org>[^\/]+)\/(?P<repo>[^\/]+)(\/.)*",
                    model.link_to_source_code,
                )
                org = match.group("org")
                repo = match.group("repo")
                _handle_github_contributions(org, repo)
            except Exception:
                org = None
                repo = None
    return render(
        request,
        ("modelview/{0}.html".format(sheettype)),
        {
            "model": model,
            "model_study": model_study,
            "gh_org": org,
            "gh_repo": repo,
            "displaySheetType": sheettype.capitalize(),
        },
    )


def printable(model, field):
    if field == "tags":
        tags = []
        engine = _get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        for tag_id in getattr(model, field):
            tag = session.query(Tag).get(tag_id)
            tags.append(tag.name)
        session.close()
        return tags
    else:
        return getattr(model, field)


def model_to_csv(request, sheettype):
    tags = []
    tag_ids = request.GET.get("tags")
    if tag_ids:
        for label in tag_ids.split(","):
            match = re.match(r"^select_(?P<tid>\d+)$", label)
            tags.append(int(match.group("tid")))
    c, f = getClasses(sheettype)
    header = list(
        field.attname
        for field in c._meta.get_fields()
        if hasattr(field, "attname")  # noqa
    )

    response = HttpResponse(content_type="text/csv")
    response[
        "Content-Disposition"
    ] = 'attachment; filename="{filename}s.csv"'.format(  # noqa
        filename=c.__name__
    )

    writer = csv.writer(response, quoting=csv.QUOTE_ALL)
    writer.writerow(header)
    for model in c.objects.all().order_by("id"):
        if all(tid in model.tags for tid in tags):
            writer.writerow([printable(model, col) for col in header])
    return response


def processPost(post, c, f, files=None, pk=None, key=None):
    """
    Returns the form according to a post request
    """
    fields = {k: post[k] for k in post}
    if "new" in fields and fields["new"] == "True":
        fields["study"] = key
    for field in c._meta.get_fields():
        if type(field) == ArrayField: # noqa
            parts = []
            for fi in fields.keys():
                if (
                    re.match(r"^{}_\d$".format(field.name), str(fi)) and fields[fi] # noqa
                ):
                    parts.append(fi)
            parts.sort()
            fields[field.name] = ",".join(
                fields[k].replace(",", ";") for k in parts
            )  # noqa
            for fi in parts:
                del fields[fi]
        else:
            if field.name in fields:
                fields[field.name] = fields[field.name]
    if pk:
        model = get_object_or_404(c, pk=pk)
        return f(fields, files, instance=model)
    else:
        return f(fields, files)


@login_required
@never_cache
def editModel(request, model_name, sheettype):
    """
    Constructs a form accoring to existing model
    """
    c, f = getClasses(sheettype)

    model = get_object_or_404(c, pk=model_name)

    tags = []
    if sheettype in ["scenario", "studie"]:
        pass
    else:
        d = load_tags()
        tags = [d[tag_id] for tag_id in model.tags]

    form = f(instance=model)

    return render(
        request,
        "modelview/edit{}.html".format(sheettype),
        {"form": form, "name": model_name, "method": "update", "tags": tags},
    )


class FSAdd(LoginRequiredMixin, View):
    def get(self, request, sheettype, method="add"):
        c, f = getClasses(sheettype)
        if method == "add":
            form = f()
            if sheettype == "scenario":
                _c_study, f_study = getClasses("studie")
                formstudy = f_study()
                return render(
                    request,
                    "modelview/new{}.html".format(sheettype),
                    {"form": form, "formstudy": formstudy, "method": method},
                )
            else:
                return render(
                    request,
                    "modelview/edit{}.html".format(sheettype),
                    {"form": form, "method": method},
                )
        else:
            raise NotImplementedError()  # FIXME: model_name not defined
            # model = get_object_or_404(c, pk=model_name)
            # form = f(instance=model)
            # return render(
            #     request,
            #     "modelview/edit{}.html".format(sheettype),
            #     {"form": form, "name": model.pk, "method": method},
            # )

    def post(self, request, sheettype, method="add", pk=None):
        c, f = getClasses(sheettype)
        form = processPost(request.POST, c, f, files=request.FILES, pk=pk)

        if form.is_valid():
            model = form.save()
            if hasattr(model, "license") and model.license:
                if model.license != "Other":
                    model.license_other_text = None
            ids = {
                int(field[len("tag_"):])
                for field in request.POST
                if field.startswith("tag_")
            }

            if sheettype == "scenario":
                pass
            else:
                model.tags = sorted(list(ids))
                model.save()
            return redirect(
                "/factsheets/{sheettype}s/{model}".format(
                    sheettype=sheettype, model=model.pk
                )
            )
        else:
            errors = []
            for field in form.errors:
                e = form.errors[field]
                error = e[0]
                field = form.fields[field].label
                errors.append((field, str(error)))

            return render(
                request,
                "modelview/edit{}.html".format(sheettype),
                {
                    "form": form,
                    "name": pk,
                    "method": method,
                    "errors": errors,
                },  # noqa
            )


def _handle_github_contributions(org, repo, timedelta=3600, weeks_back=8):
    """
    This function returns the url of an image of recent GitHub contributions
    If the image is not present or outdated it will be reconstructed
    """
    path = "GitHub_{0}_{1}_Contribution.png".format(org, repo)
    full_path = os.path.join(djangoSettings.MEDIA_ROOT, path)

    # We have to replot the image
    # Set plot font
    font = {"family": "normal"}
    matplotlib.rc("font", **font)

    # Query GitHub API for contributions
    user_agent = {"user-agent": "oeplatform"}
    http = urllib3.PoolManager(headers=user_agent)
    try:
        reply = http.request(
            "GET",
            "https://api.github.com/repos/{0}/{1}/stats/commit_activity".format(  # noqa
                org, repo
            ),
        ).data.decode("utf8")
    except Exception:
        pass

    reply = json.loads(reply)

    if not reply:
        return None

    # If there are more weeks than nessecary, truncate
    if weeks_back < len(reply):
        reply = reply[-weeks_back:]

    # GitHub API returns a JSON dict with w: weeks, c: contributions
    (times, commits) = zip(
        *[
            (
                datetime.datetime.fromtimestamp(int(week["week"])).strftime(
                    "%m-%d"
                ),  # noqa
                sum(map(int, week["days"])),
            )
            for week in reply
        ]
    )
    max_c = max(commits)

    # generate a distribution wrt. to the commit numbers
    commits_ids = [i for i in range(len(commits)) for _ in range(commits[i])]

    # transform the contribution distribution into a density function
    # using a gaussian kernel estimator
    if commits_ids:
        density = stats.kde.gaussian_kde(commits_ids, bw_method=0.2)
    else:
        # if there are no commits the density is a constant 0
        def density(x):
            return 0

    # plot this distribution
    x = numpy.arange(0.0, len(commits), 0.01)
    c_real_max = max(density(xv) for xv in x)
    plt.figure(figsize=(4, 2))  # facecolor='white',

    # replace labels by dates and numbers of commits
    ax1 = plt.axes(frameon=False)
    plt.fill_between(x, density(x), 0)
    ax1.set_frame_on(False)
    ax1.axes.get_xaxis().tick_bottom()
    ax1.axes.get_yaxis().tick_left()
    plt.yticks(
        numpy.arange(c_real_max - 0.001, c_real_max), [max_c], size="small"
    )  # noqa
    plt.xticks(numpy.arange(0.0, len(times)), times, size="small", rotation=45)

    # save the figure
    plt.savefig(full_path, transparent=True, bbox_inches="tight")
    url = finders.find(path)
    return url


class RDFFactoryView(View):
    _template = "modelview/display_rdf.html"

    def get(self, request, factory_id, identifier):
        format = request.GET.get("format", "html")
        if format == "json":
            try:
                fac = factory.get_factory(factory_id)
            except KeyError:
                raise Http404

            context = connection.ConnectionContext()
            # Build URI, assuming that this is part of this knowledge graph
            uri = getattr(namespace.OEO_KG, identifier)
            # TODO: Error handling:
            #  * What if it is not part of the ?
            #  * What if it is not of this class?
            #  * Probably: 404 in both cases!?
            obj = fac._load_one(uri, context)

            jsn = obj.to_json()
            return JsonResponse(jsn)
        else:
            return render(
                request,
                self._template,
                {
                    "iri": identifier,
                    "factory": factory_id,
                    "rdf_templates": json.dumps(
                        factory.get_factory_templates()
                    ),  # noqa
                },
            )

    def post(self, request, factory_id, identifier):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        context = connection.ConnectionContext()
        subject = f"<{getattr(namespace.OEO_KG, identifier)}>"
        query = json.loads(request.POST["query"])
        property = query["property"]

        if factory_id == "study" and identifier == "new":
            context.insert_new_study(property)

        try:
            fac = factory.get_factory(factory_id)
            pf = fac._fields[property]
        except KeyError:
            raise Http404

        old_value = None
        new_value = None

        print("=====query====")
        print(query)
        raw_old_value = query.get("oldValue")
        if raw_old_value:
            old_value = pf.process_data(raw_old_value)

        raw_new_value = query.get("newValue")
        if raw_new_value:
            new_value = pf.process_data(raw_new_value)

        if not old_value and not new_value:
            result = context.insert_new_instance(
                subject,
                pf.rdf_name,
                inverse=pf.inverse,
                new_name=raw_new_value["literal"],
            )
            result = dict(
                iri=str(
                    result.rpartition("/")[0] + "/" + raw_new_value["literal"]
                )  # noqa
            )
        else:
            context.update_property(
                subject, pf.rdf_name, old_value, new_value, inverse=pf.inverse
            )
            result = {}
        return JsonResponse(result)

    def add_study(self, name):
        # result = context.insert_new_study(name)
        # return JsonResponse(result)
        raise NotImplementedError()  # FIXME: context not defined


class RDFInstanceView(View):
    def get(self, request):
        context = connection.ConnectionContext()
        cls = request.GET.get("iri")
        if not cls:
            raise HttpResponse(status=400)
        subclass = request.GET.get("subclass", False)
        result = context.get_all_instances(cls, subclass=subclass)
        instances = [
            dict(iri=row["s"]["value"], label=row["l"]["value"])
            if row.get("l")
            else dict(iri=row["s"]["value"])
            for row in result["results"]["bindings"]
            if not row["s"]["type"] == "bnode"
        ]
        return JsonResponse(dict(instances=instances))


class RDFView(View):
    def get(self, request, factory_id=None):
        try:
            fac = factory.get_factory(factory_id)
        except KeyError:
            raise Http404
        context = connection.ConnectionContext()
        instances = fac.load_all_instances(context)
        return render(
            request,
            "modelview/list_rdf_instances.html",
            {"instances": instances},  # noqa
        )


BASE_VIEW_PROPS = OrderedDict(
    [
        (
            "Basic Information",
            OrderedDict(
                [
                    ("acronym", ["acronym"]),
                    ("institutions", ["institutions"]),
                    ("authors", ["authors"]),
                    ("current contact person", ["current_contact_person"]),
                    ("contact email", ["contact_email"]),
                    ("website", ["website"]),
                    ("logo", ["logo"]),
                    ("primary purpose", ["primary_purpose"]),
                    ("primary outputs", ["primary_outputs"]),
                    ("support", ["support"]),
                    ("framework", ["framework", "framework_yes_text"]),
                    ("user documentation", ["user_documentation"]),
                    ("code documentation", ["code_documentation"]),
                    ("documentation quality", ["documentation_quality"]),
                    ("source of funding", ["source_of_funding"]),
                    ("number of", ["number_of_devolopers", "number_of_users"]),
                ]
            ),
        ),
        (
            "Openness",
            OrderedDict(
                [
                    ("open source", ["open_source"]),
                    ("open up", ["open_up"]),
                    ("costs", ["costs"]),
                    ("license", ["license", "license_other_text"]),
                    (
                        "source code available",
                        [
                            "source_code_available",
                            "gitHub",
                            "link_to_source_code",
                        ],  # noqa
                    ),
                ]
            ),
        ),
        (
            "Software",
            OrderedDict(
                [
                    ("modelling software", ["modelling_software"]),
                    (
                        "interal data processing software",
                        ["interal_data_processing_software"],
                    ),
                    (
                        "external optimizer",
                        ["external_optimizer", "external_optimizer_yes_text"],
                    ),
                    ("additional software", ["additional_software"]),
                    ("gui", ["gui"]),
                ]
            ),
        ),
    ]
)

MODEL_VIEW_PROPS = OrderedDict(
    list(BASE_VIEW_PROPS.items())
    + [
        (
            "Coverage",
            OrderedDict(
                [
                    (
                        "energy sectors",
                        [
                            "energy_sectors_electricity",
                            "energy_sectors_heat",
                            "energy_sectors_others",
                            "energy_sectors_others_text",
                        ],
                    ),
                    (
                        "demand sectors",
                        [
                            "demand_sectors_households",
                            "demand_sectors_industry",
                            "demand_sectors_commercial_sector",
                            "demand_sectors_transport",
                        ],
                    ),
                    (
                        "energy carrier",
                        [
                            "energy_carrier_gas_natural_gas",
                            "energy_carrier_gas_biogas",
                            "energy_carrier_gas_hydrogen",
                            "energy_carrier_liquids_petrol",
                            "energy_carrier_liquids_diesel",
                            "energy_carrier_liquids_ethanol",
                            "energy_carrier_solid_hard_coal",
                            "energy_carrier_solid_hard_lignite",
                            "energy_carrier_solid_hard_uranium",
                            "energy_carrier_solid_hard_biomass",
                            "energy_carrier_renewables_sun",
                            "energy_carrier_renewables_wind",
                            "energy_carrier_renewables_hydro",
                            "energy_carrier_renewables_geothermal_heat",
                        ],
                    ),
                    (
                        "generation renewables",
                        [
                            "generation_renewables_PV",
                            "generation_renewables_wind",
                            "generation_renewables_hydro",
                            "generation_renewables_bio",
                            "generation_renewables_solar_thermal",
                            "generation_renewables_geothermal",
                            "generation_renewables_others",
                            "generation_renewables_others_text",
                        ],
                    ),
                    (
                        "generation conventional",
                        [
                            "generation_conventional_gas",
                            "generation_conventional_lignite",
                            "generation_conventional_hard_coal",
                            "generation_conventional_oil",
                            "generation_conventional_liquid_fuels",
                            "generation_conventional_nuclear",
                        ],
                    ),
                    ("generation CHP", ["generation_CHP"]),
                    (
                        "transfer electricity",
                        [
                            "transfer_electricity",
                            "transfer_electricity_distribution",
                            "transfer_electricity_transition",
                        ],
                    ),
                    (
                        "transfer gas",
                        [
                            "transfer_gas",
                            "transfer_gas_distribution",
                            "transfer_gas_transition",
                        ],
                    ),
                    (
                        "transfer heat",
                        [
                            "transfer_heat",
                            "transfer_heat_distribution",
                            "transfer_heat_transition",
                        ],
                    ),
                    (
                        "network coverage",
                        [
                            "network_coverage_AC",
                            "network_coverage_DC",
                            "network_coverage_TM",
                            "network_coverage_SN",
                            "network_coverage_other",
                        ],
                    ),
                    (
                        "storage electricity",
                        [
                            "storage_electricity_battery",
                            "storage_electricity_kinetic",
                            "storage_electricity_CAES",
                            "storage_electricity_PHS",
                            "storage_electricity_chemical",
                        ],
                    ),
                    ("storage heat", ["storage_heat"]),
                    ("storage gas", ["storage_gas"]),
                    (
                        "user behaviour",
                        ["user_behaviour", "user_behaviour_yes_text"],
                    ),  # noqa
                    ("changes in efficiency", ["changes_in_efficiency"]),
                    ("market models", ["market_models"]),
                    ("geographical coverage", ["geographical_coverage"]),
                    (
                        "geo resolution",
                        [
                            "geo_resolution_global",
                            "geo_resolution_continents",
                            "geo_resolution_national_states",
                            "geo_resolution_TSO_regions",
                            "geo_resolution_federal_states",
                            "geo_resolution_regions",
                            "geo_resolution_NUTS_3",
                            "geo_resolution_municipalities",
                            "geo_resolution_districts",
                            "geo_resolution_households",
                            "geo_resolution_power_stations",
                            "geo_resolution_others",
                            "geo_resolution_others_text",
                            "comment_on_geo_resolution",
                        ],
                    ),
                    (
                        "time resolution",
                        [
                            "time_resolution_anual",
                            "time_resolution_hour",
                            "time_resolution_15_min",
                            "time_resolution_1_min",
                            "time_resolution_other",
                            "time_resolution_other_text",
                        ],
                    ),
                    (
                        "observation period",
                        [
                            "observation_period_more_1_year",
                            "observation_period_less_1_year",
                            "observation_period_1_year",
                            "observation_period_other",
                            "observation_period_other_text",
                        ],
                    ),
                    (
                        "additional dimensions",
                        [
                            "additional_dimensions_sector_ecological",
                            "additional_dimensions_sector_ecological_text",
                            "additional_dimensions_sector_economic",
                            "additional_dimensions_sector_economic_text",
                            "additional_dimensions_sector_social",
                            "additional_dimensions_sector_social_text",
                            "additional_dimensions_sector_others",
                            "additional_dimensions_sector_others_text",
                        ],
                    ),
                ]
            ),
        ),
        (
            "Mathematical Properties",
            OrderedDict(
                [
                    (
                        "model class",
                        [
                            "model_class_optimization_LP",
                            "model_class_optimization_MILP",
                            "model_class_optimization_Nonlinear",
                            "model_class_optimization_LP_MILP_Nonlinear_text",
                            "model_class_simulation_Agentbased",
                            "model_class_simulation_System_Dynamics",
                            "model_class_simulation_Accounting_Framework",
                            "model_class_simulation_Game_Theoretic_Model",
                            "model_class_other",
                            "model_class_other_text",
                            "short_description_of_mathematical_model_class",
                        ],
                    ),
                    (
                        "mathematical objective",
                        [
                            "mathematical_objective_cO2",
                            "mathematical_objective_costs",
                            "mathematical_objective_rEshare",
                            "mathematical_objective_other",
                            "mathematical_objective_other_text",
                        ],
                    ),
                    (
                        "uncertainty deterministic",
                        ["uncertainty_deterministic"],
                    ),  # noqa
                    ("uncertainty Stochastic", ["uncertainty_Stochastic"]),
                    (
                        "uncertainty Other",
                        ["uncertainty_Other", "uncertainty_Other_text"],
                    ),
                    ("montecarlo", ["montecarlo"]),
                    (
                        "typical computation",
                        [
                            "typical_computation_time",
                            "typical_computation_hardware",
                        ],  # noqa
                    ),
                    (
                        "technical data anchored in the model",
                        ["technical_data_anchored_in_the_model"],
                    ),
                ]
            ),
        ),
        (
            "Model Integration",
            OrderedDict(
                [
                    ("interfaces", ["interfaces"]),
                    (
                        "model file",
                        ["model_file_format", "model_file_format_other_text"],
                    ),
                    ("model input", ["model_input", "model_input_other_text"]),
                    (
                        "model output",
                        ["model_output", "model_output_other_text"],
                    ),  # noqa
                    ("integrating models", ["integrating_models"]),
                    ("integrated models", ["integrated_models"]),
                ]
            ),
        ),
        (
            "References",
            OrderedDict(
                [
                    ("citation reference", ["citation_reference"]),
                    ("citation DOI", ["citation_DOI"]),
                    (
                        "reports produced",
                        ["references_to_reports_produced_using_the_model"],
                    ),
                    ("larger scale usage", ["larger_scale_usage"]),
                    (
                        "example research questions",
                        ["example_research_questions"],
                    ),
                    (
                        "model validation",
                        [
                            "validation_models",
                            "validation_measurements",
                            "validation_others",
                            "validation_others_text",
                        ],
                    ),
                    (
                        "model specific properties",
                        ["model_specific_properties"],
                    ),
                ]
            ),
        ),
    ]
)

FRAMEWORK_VIEW_PROPS = OrderedDict(
    list(BASE_VIEW_PROPS.items())
    + [
        (
            "Framework",
            OrderedDict(
                [
                    (
                        "model types",
                        [
                            "model_types_grid",
                            "model_types_demand_simulation",
                            "model_types_feed_in_simulation",
                            "model_types_other",
                            "model_types_other_text",
                        ],
                    ),
                    ("api doc", ["api_doc"]),
                    ("data api", ["data_api"]),
                    ("abstraction", ["abstraction"]),
                    ("used", ["used"]),
                ]
            ),
        )
    ]
)


MODEL_DEFAULT_COLUMNS = {
    "model_name",
    "acronym",
    "tags",
    "primary_purpose",
    "license",
    "open_source",
    #    'model_class_optimization_LP',
    #    'model_class_optimization_MILP',
    #    'model_class_optimization_Nonlinear',
    #    'model_class_optimization_LP_MILP_Nonlinear_text',
    #    'model_class_simulation_Agentbased',
    #    'model_class_simulation_System_Dynamics',
    #    'model_class_simulation_Accounting_Framework',
    #    'model_class_simulation_Game_Theoretic_Model',
    "short_description_of_mathematical_model_class",
    "comment_on_geo_resolution",
}

FRAMEWORK_DEFAULT_COLUMNS = {
    "model_name",
    "tags",
    "license",
    "support",
    "number_of_devolopers",
}
