from django.db import models
from django.contrib.postgres import fields
from django import forms
from django.contrib.postgres.fields import ArrayField
from django.forms import CharField, ImageField, BooleanField, IntegerField, URLField, ChoiceField
# Create your models here.

class Energymodel(models.Model):

    model_name = CharField(label='Model name', help_text='What is the full model name?') 
    acronym = CharField(label='Acronym', help_text='What is the abbreviation?') 
    institutions = CharField(label='Institution(s)', help_text='Which institutions develop(ed) the model?') 
    authors_institution_working_field_active_time_period = CharField(label='Author(s) (institution, working field, active time period)', help_text='Who are the authors? Where do / did they work, on which parts of the model, during which time period?') 
    current_contact_person = CharField(label='Current contact person', help_text='Who is the main contact person?') 
    contact_email = CharField(label='Contact (e-mail)', help_text='Please, fill in an e-mail address.') 
    website = CharField(label='Website') 
    logo = ImageField(label='Logo') 
    primary_purpose = CharField(label='Primary Purpose', help_text='What is the primary purpose the model?') 
    primary_outputs = CharField(label='Primary Outputs', help_text='What are the main outputs of the model?') 
    support = BooleanField(label='Support / Community / Forum') 

    framework = BooleanField(label='Framework', help_text='Is the model based on a framework? If yes, which?') 
    framework_yes_text = CharField() 

    user_documentation = URLField(label='User Documentation', help_text='Where is the user documentation publicly available?') 
    code_documentation = URLField(label='Developer/Code Documentation', help_text='Where is the code documentation publicly available?')
    documentation_quality = ChoiceField(label='Documentation quality', help_text='How is the quality of the documentations?', choices=[('expandable', 'expandable'), ('good', 'good'), ('excellent', 'excellent')]) 
    source_of_funding = CharField(label='Source of funding', help_text="What's the main source of funding?") 
    open_Source = BooleanField(label='Open Source') 
    open_up = BooleanField(label='Planned to open up in the future', help_text='Will the source code be available in future?') 
    costs = CharField(label='Costs') 
    license = ChoiceField(label='License', choices=[('Apache', 'Apache'), ('Other', 'Other')]) 
    license_other_text = CharField()
    source_code_available = BooleanField(label='Source code available', help_text='Is the source code directly downloadable?') 
    gitHub = BooleanField(label='GitHub', help_text='Is the model available on GitHub?') 
    link_to_source_code = URLField(label='Link to source code') 
    data_provided = ChoiceField(label='Data provided', help_text='Is the necessary data to run a scenario available?', choices=[('none', 'none'), ('some', 'some'), ('all', 'all')]) 
    cooperative_programming = BooleanField(label='Cooperative programming', help_text='Is it possible to join the coding group?') 
    number_of_devolopers = ChoiceField(label='Number of devolopers', help_text='How many people are involved in the model development?', choices=[('less than 10', 'less than 10'), (' less than 20', ' less than 20'), (' less than 50', ' less than 50'), (' more than 50', ' more than 50')]) 
    number_of_users_ = ChoiceField(label='Number of users ', help_text='How many people approximately use the model?', choices=[('less than 10', 'less than 10'), (' less than 100', ' less than 100'), (' less than 1000', ' less than 1000'), (' more than 1000', ' more than 1000')]) 
    modelling_software = ArrayField(models.CharField( help_text='What modelling software and which version is used?', max_length=50))
    interal_data_processing_software = ArrayField(models.CharField( help_text='Which data processing software is required?', max_length=50))

    external_optimizer = BooleanField(label='External optimizer', help_text='Which external optimizer can the model apply?') 
    external_optimizer_yes_text = ArrayField(models.CharField(max_length=50))

    additional_software = ArrayField(models.CharField(help_text='Which additional software is required to run the model?', max_length=50))
    gui = BooleanField(label='GUI', help_text='Is a graphical user interface available?') 

    energy_sectors_electricity = BooleanField(label='electricity') 
    energy_sectors_heat = BooleanField(label='heat') 
    energy_sectors_liquid_fuels = BooleanField(label='liquid fuels') 
    energy_sectors_gas = BooleanField(label='gas') 
    energy_sectors_oil = BooleanField(label='oil') 
    energy_sectors_others = BooleanField(label='others')
    energy_sectors_others_text = CharField()
     
    demand_sectors_households = BooleanField(label='Households') 
    demand_sectors_industry = BooleanField(label='Industry') 
    demand_sectors_commercial_sector = BooleanField(label='Commercial sector') 
    demand_sectors_transport = BooleanField(label='Transport')
     
    energy_carrier_gas_natural_gas = BooleanField(label='Natural gas') 
    energy_carrier_gas_biogas = BooleanField(label='Biogas') 
    energy_carrier_gas_hydrogen = BooleanField(label='Hydrogen') 

    energy_carrier_liquids_petrol = BooleanField(label='Petrol')
    energy_carrier_liquids_diesel = BooleanField(label='Diesel')
    energy_carrier_liquids_ethanol = BooleanField(label='Ethanol')

    energy_carrier_solid_hard_coal = BooleanField(label='Hard coal') 
    energy_carrier_solid_hard_lignite = BooleanField(label='Lignite') 
    energy_carrier_solid_hard_uranium = BooleanField(label='Uranium') 
    energy_carrier_solid_hard_biomass = BooleanField(label='Biomass') 

    energy_carrier_renewables_sun = BooleanField(label='Sun')
    energy_carrier_renewables_wind = BooleanField(label='Wind')
    energy_carrier_renewables_hydro = BooleanField(label='Hydro')
    energy_carrier_renewables_geothermal_heat = BooleanField(label='Geothermal heat')

    generation_renewables_PV = BooleanField(label='PV') 
    generation_renewables_wind = BooleanField(label='Wind') 
    generation_renewables_hydro = BooleanField(label='Hydro') 
    generation_renewables_biomass = BooleanField(label='Biomass') 
    generation_renewables_biogas = BooleanField(label='Biogas') 
    generation_renewables_solar_thermal = BooleanField(label='Solar thermal') 
    generation_renewables_others = BooleanField(label='Others')
    generation_renewables_others_text = CharField() 

    generation_conventional_gas = BooleanField(label='gas')
    generation_conventional_coal = BooleanField(label='coal')
    generation_conventional_oil = BooleanField(label='oil')
    generation_conventional_liquid_fuels = BooleanField(label='liquid fuels')
    generation_conventional_nuclear = BooleanField(label='nuclear')
     
    generation_CHP = BooleanField(label='CHP') 

    transfer_electricity = BooleanField(label="electricity") 
    transfer_electricity_distribution = BooleanField()
    transfer_electricity_transition = BooleanField()

    transfer_gas = BooleanField(label="gas") 
    transfer_gas_distribution = BooleanField()
    transfer_gas_transition = BooleanField()

    transfer_heat = BooleanField(label="heat") 
    transfer_heat_distribution = BooleanField()
    transfer_heat_transition = BooleanField()

    network_coverage_AC = BooleanField(label='AC load flow') 
    network_coverage_DC = BooleanField(label='DC load flow') 

    storage_electricity_battery = BooleanField(label='battery') 
    storage_electricity_kinetic = BooleanField(label='kinetic') 
    storage_electricity_CAES = BooleanField(label='CAES') 
    storage_electricity_PHS = BooleanField(label='PHS') 
    storage_electricity_chemical = BooleanField(label='chemical') 

    storage_heat = BooleanField(label='heat') 
    storage_gas = BooleanField(label='gas') 

    user_behaviour = BooleanField(label='User behaviour and demand side management', help_text='How can user behaviour changes and demand side management be considered?') 
    user_behaviour_yes_text = CharField() 

    market_models = BooleanField(label='Market models', help_text='Which / Is a market models are included?') 

    geographical_coverage = ArrayField(models.CharField(help_text='What regions are covered? Please, list the regions covered by the model. Leave blank, if the model and data are not limited to a specific region. Example input: USA, Canada, Mexico' , max_length=50))

    geo_resolution_global = BooleanField(label='global') 
    geo_resolution_continents = BooleanField(label='continents') 
    geo_resolution_national_states = BooleanField(label='national states') 
    geo_resolution_TSO_regions = BooleanField(label='TSO regions') 
    geo_resolution_federal_states = BooleanField(label='federal states') 
    geo_resolution_regions = BooleanField(label='regions') 
    geo_resolution_NUTS_3 = BooleanField(label='NUTS 3') 
    geo_resolution_municipalities = BooleanField(label='municipalities') 
    geo_resolution_districts = BooleanField(label='districts') 
    geo_resolution_households = BooleanField(label='households') 
    geo_resolution_power_stations = BooleanField(label='power stations') 
    geo_resolution_others = BooleanField(label='others') 
    geo_resolution_others_text = CharField()

    comment_on_geo_resolution = CharField(label='Comment on geographic (spatial) resolution', help_text='Feel free to explain the geographical resolution of the model e.g. with regard to the grid data.') 

    time_resolution_anual = BooleanField(label='anual') 
    time_resolution_hour = BooleanField(label='hour') 
    time_resolution_15_min = BooleanField(label='15 min') 
    time_resolution_1_min = BooleanField(label='1 min') 

    observation_period_1_year = BooleanField(label='>1 year') 
    observation_period_1_year = BooleanField(label='1 year') 

    time_resolution_other = BooleanField(label='other') 
    time_resolution_other_text = CharField()

    additional_dimensions_sector_ecological = BooleanField(label='ecological') 
    additional_dimensions_sector_ecological_text = CharField() 
    additional_dimensions_sector_economic = BooleanField(label='economic') 
    additional_dimensions_sector_economic_text = CharField()
    additional_dimensions_sector_social = BooleanField(label='social')
    additional_dimensions_sector_social_text = CharField()  
    additional_dimensions_sector_others = BooleanField(label='others') 
    additional_dimensions_sector_others_text = CharField()

    model_class_optimization_LP = BooleanField(label='LP') 
    model_class_optimization_MILP = BooleanField(label='MILP')
    model_class_optimization_Nonlinear = BooleanField(label='Nonlinear')
    model_class_optimization_LP_MILP_Nonlinear_text = CharField()

    model_class_simulation_Agentbased = BooleanField(label='Agent-based')
    model_class_simulation_System_Dynamics = BooleanField(label='System Dynamics') 
    model_class_simulation_Accounting_Framework = BooleanField(label='Accounting Framework') 
    model_class_simulation_Game_Theoretic_Model = BooleanField(label='Game Theoretic Model')

    model_class_other = BooleanField(label='Other') 
    model_class_other_text = BooleanField() 

    short_description_of_mathematical_model_class = CharField(label='Short description of mathematical model class') 

    mathematical_objective_cO2 = BooleanField(label='CO2') 
    mathematical_objective_costs = BooleanField(label='costs') 
    mathematical_objective_rEshare = BooleanField(label='RE-share') 
    mathematical_objective_other = BooleanField(label='other') 
    mathematical_objective_other_text = BooleanField()

    uncertainty_deterministic = BooleanField(label='Deterministic') 
    uncertainty_Stochastic = BooleanField(label='Stochastic')
    uncertainty_Other = BooleanField(label='Other')

    montecarlo = BooleanField(label='Suited for many scenarios / monte-carlo') 

    typical_computation_time_less_than_a_second = BooleanField(label='less than a second') 
    typical_computation_time_less_than_a_minute = BooleanField(label='less than a minute') 
    typical_computation_time_less_than_an_hour = BooleanField(label='less than an hour') 
    typical_computation_time_less_than_a_day = BooleanField(label='less than a day') 
    typical_computation_time_more_than_a_day = BooleanField(label='more than a day') 

    typical_computation_hardware = CharField(label='Typical computation hardware', help_text='Here you can specify which hardware was assumed to estimate above time (e.g. RAM, CPU, GPU, etc).') 
    technical_data_anchored_in_the_model = CharField(label='Technical data anchored in the model', help_text='If there is technical data already embedded (hard code) in the model and not part of the scenario, please make that transparent here.') 
    citation_reference = CharField(label='Citation reference', help_text='publications about the model')
    citation_DOI = CharField(label='Citation DOI', help_text='publications about the model') 
    references_to_reports_produced_using_the_model = CharField(label='References to reports produced using the model', help_text='Which studies have been calculated with this model?') 
    example_research_questions = CharField(label='Example research questions', help_text='What would be a good research question that could be answered with the model?') 
    larger_scale_usage = CharField(label='Larger scale usage', help_text='Is this model used on a larger scale? If so, who uses it?') 
    validation = CharField(label='Validation', help_text='How is the model validated?') 
    model_specific_properties = CharField(label='Model specific properties', help_text='What are main specific characteristics (strengths and weaknesses) of this model regarding the purpose of the recommendation?') 


"""class Energymodel(models.Model):
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
    
    model_specific_properties = CharField(max_length=200, null=True, blank=True)"""
    

    

    
    

