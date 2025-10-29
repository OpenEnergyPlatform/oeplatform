"""
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Tom Heimbrodt <https://github.com/tom-heimbrodt>
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 quentinpeyras <https://github.com/quentinpeyras>
SPDX-FileCopyrightText: 2025 Lara Christmann <https://github.com/solar-c> © Reiner Lemoine Institut
SPDX-License-Identifier: AGPL-3.0-or-later
"""  # noqa: 501

import re
from collections import OrderedDict
from typing import Type

from django.contrib.postgres.fields import ArrayField
from django.db.models import Model
from django.forms import ModelForm
from django.shortcuts import get_object_or_404

from modelview.forms import EnergyframeworkForm, EnergymodelForm
from modelview.models import Energyframework, Energymodel

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
                    ("number of", ["number_of_developers", "number_of_users"]),
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
    "number_of_developers",
}


def getClasses(sheettype: str) -> tuple[Type[Model] | None, Type[ModelForm] | None]:
    """
    Returns the model and form class w.r.t sheettype.
    """
    allowed_sheet_types = ["model", "framework"]
    cls = None
    frm = None

    if isinstance(sheettype, str):
        if sheettype in allowed_sheet_types:
            if sheettype == "model":
                cls = Energymodel
                frm = EnergymodelForm
            elif sheettype == "framework":
                cls = Energyframework
                frm = EnergyframeworkForm

    return cls, frm


def printable(model, field):
    return getattr(model, field)


def processPost(post, c, f, files=None, pk=None, key=None):
    """
    Returns the form according to a post request
    """
    fields = {k: post[k] for k in post}
    if "new" in fields and fields["new"] == "True":
        fields["study"] = key
    for field in c._meta.get_fields():
        if type(field) == ArrayField:  # noqa
            parts = []
            for fi in fields.keys():
                if (
                    re.match(r"^{}_\d$".format(field.name), str(fi))
                    and fields[fi]  # noqa
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
