from django.db import models
from django.contrib.postgres import fields
from django import forms
from django.db.models import BooleanField, CharField, IntegerField
# Create your models here.

class Energymodel(models.Model):
    id_name = models.CharField(max_length=20, primary_key=True)
    full_name = models.CharField(max_length=200, unique=True)
    acronym = models.CharField(max_length=200, null=True, blank=True)
    author_intitution = fields.ArrayField(models.CharField(max_length=200))
    authors = fields.ArrayField(models.CharField(max_length=200))
    current_contact_persons = fields.ArrayField(models.CharField(max_length=200))
    contact_email_address = models.EmailField(max_length=200)
    website = models.CharField(max_length=200, null=True, blank=True)
    logo = models.ImageField(null=True, blank=True)
    short_description = models.CharField(max_length=200)
    support = BooleanField()
    documentation_user = BooleanField()
    documentation_code = BooleanField()
    documentation_cooperation = BooleanField() # = forms.ChoiceField(choices=("user","code","cooperation"))
    documentation_quality_user = BooleanField()
    documentation_quality_code = BooleanField()
    documentation_quality_cooperation = BooleanField()
    source_of_funding = models.CharField(max_length=200, null=True, blank=True)

    open_source = BooleanField()
    license = forms.ChoiceField(choices=("Apache","GPL"))
    source_downloadable = BooleanField()
    github = BooleanField()
    link_to_source = models.CharField(max_length=200, null=True, blank=True)
    data_provided = forms.ChoiceField(choices=("None","Some","All"))
    open_up = BooleanField()
    cooperative_programming = BooleanField()
    technical_data = CharField(max_length=200, null=True, blank=True)
    
    modelling_software = CharField(max_length=200, null=True, blank=True)
    internal_data = BooleanField()
    external_optimizer = BooleanField()
    additional_software  = CharField(max_length=200, null=True, blank=True)
    gui = BooleanField()
    post_processing_facility = CharField(max_length=200, null=True, blank=True)
    
    for sector in ["mobility","electricy","heat"]:
        exec("modeled_energy_sectors{0} = BooleanField()".format(sector))
    for carrier in ["gas","oil","electricy"]:    
        exec("modelled_energy_carrier_{0} = BooleanField()".format(carrier)) 
    for tech in ["renewable","conventional", "CHP", "dispatch"]:
        exec("components_generation_{0} = BooleanField()".format(tech))
    for tech in ["heat","electric","gas"]:
        exec("components_transfer_{0} = BooleanField()".format(tech))
    user_behaviour = BooleanField()
    user_behaviour_text = CharField(max_length=200, null=True, blank=True)
    modeled_efficiency = CharField(max_length=200, null=True, blank=True)
    market_models = BooleanField()
    market_models_text = CharField(max_length=200, null=True, blank=True)
    for tech in ["AC_load_flow", "DC_load_flow", "net_transfer_capacities"]:
        exec("network_coverage_{0} = BooleanField()".format(tech))
    for tech in ["global","continental","national","regions","municipalities","districts","households"]:
        exec("typical_geographic_regions_covered_{0} = BooleanField()".format(tech))
    for tech in ["global","continental","national","regions","municipalities","districts","households"]:
        exec("typical_geographic_resolution_{0} = BooleanField()".format(tech))
    for tech in ["anual","hour","15_min", "1_min", "other"]:
        exec("typical_time_resolution_{0} = BooleanField()".format(tech))
    typical_time_resolution_text = CharField(max_length=200, null=True, blank=True)
    for tech in ["ecological","economic","social","miscellaneous"]:
        exec("Additional_dimensions_{0} = BooleanField()".format(tech))
    additional_dimensions_text = CharField(max_length=200, null=True, blank=True)
    for tech in ["LP","MLP","non_linear","Optimisation", "Simulation", "Agent_based", "Other"]:
        exec("model_type_{0} = BooleanField()".format(tech))

    model_type_text = CharField(max_length=200, null=True, blank=True)
    short_description_mathematical_model = CharField(max_length=200, null=True, blank=True)
    math_objective = CharField(max_length=200, null=True, blank=True)
    approach_to_uncertainity = CharField(max_length=200, null=True, blank=True)
    many_scenarios = BooleanField()
    number_variables = IntegerField(null=True, blank=True)
    typical_computation_time_minutes = IntegerField(null=True, blank=True)
    typical_computation_time_hardware = CharField(max_length=200, null=True, blank=True)
    new_equations = CharField(max_length=200, null=True, blank=True)
    
    citation_reference = CharField(max_length=200, null=True, blank=True)
    citation_doi = CharField(max_length=200, null=True, blank=True)
    references_to_reports = CharField(max_length=200, null=True, blank=True)
    example_research_questions = CharField(max_length=200, null=True, blank=True)
    who_uses_this = CharField(max_length=200, null=True, blank=True)
    where_used = CharField(max_length=200, null=True, blank=True)
    how_validated = CharField(max_length=200, null=True, blank=True)
    
    model_specific_properties = CharField(max_length=200, null=True, blank=True)
    

    

    
    

