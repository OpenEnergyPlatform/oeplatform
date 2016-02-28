from django.db import models
from django.contrib.postgres import fields
from django import forms
from django.contrib.postgres.fields import ArrayField
from django.db.models import CharField, ImageField, BooleanField, IntegerField, URLField, CharField, EmailField, TextField
# Create your models here.

class BasicFactsheet(models.Model):
    model_name = CharField(max_length=100,verbose_name='Model name', help_text='What is the full model name?', null=False, unique=True) 
    acronym = CharField(max_length=20,verbose_name='Acronym', help_text='What is the abbreviation?', null=False) 
    institutions = CharField(max_length=100,verbose_name='Institution(s)', help_text='Which institutions develop(ed) the model?', null=False) 
    authors = CharField(max_length=300,verbose_name='Author(s) (institution, working field, active time period)', help_text='Who are the authors? Where do / did they work, on which parts of the model, during which time period?', null=False) 
    current_contact_person = CharField(max_length=100, verbose_name='Current contact person', help_text='Who is the main contact person?', null=True) 
    contact_email = EmailField(verbose_name='Contact (e-mail)', help_text='Please, fill in an e-mail address.', null=False) 
    website = URLField(verbose_name='Website', null=True) 
    logo = ImageField(verbose_name='Logo', null=True) 
    primary_purpose = CharField(max_length=100,verbose_name='Primary Purpose', help_text='What is the primary purpose the model?', null=True) 
    primary_outputs = CharField(max_length=100,verbose_name='Primary Outputs', help_text='What are the main outputs of the model?', null=True) 
    support = BooleanField(default=False,verbose_name='Support / Community / Forum') 

    framework = BooleanField(default=False,verbose_name='Framework', help_text='Is the model based on a framework? If yes, which?') 
    framework_yes_text = CharField(max_length=100,null=True) 

    user_documentation = URLField(verbose_name='User Documentation', help_text='Where is the user documentation publicly available?', null=False) 
    code_documentation = URLField(verbose_name='Developer/Code Documentation', help_text='Where is the code documentation publicly available?', null=False)
    documentation_quality = CharField(max_length=100,verbose_name='Documentation quality', help_text='How is the quality of the documentations?', choices=(('expandable', 'expandable'), ('good', 'good'), ('excellent', 'excellent')), default='expandable') 
    source_of_funding = CharField(max_length=200,verbose_name='Source of funding', help_text="What's the main source of funding?", null=True) 
    open_source = BooleanField(default=False,verbose_name='Open Source') 
    open_up = BooleanField(default=False,verbose_name='Planned to open up in the future', help_text='Will the source code be available in future?') 
    costs = CharField(max_length=100,verbose_name='Costs', null=True) 
    license = CharField(max_length=100,verbose_name='License', choices=(('Apache', 'Apache'), ('Other', 'Other')), default='Apache') 
    license_other_text = CharField(max_length=100,null=True)
    source_code_available = BooleanField(default=False,verbose_name='Source code available', help_text='Is the source code directly downloadable?') 
    gitHub = BooleanField(default=False,verbose_name='GitHub', help_text='Is the model available on GitHub?') 
    link_to_source_code = URLField(verbose_name='Link to source code', null=True) 
    data_provided = CharField(max_length=100,verbose_name='Data provided', help_text='Is the necessary data to run a scenario available?', choices=(('none', 'none'), ('some', 'some'), ('all', 'all')), default='none') 
    cooperative_programming = BooleanField(default=False,verbose_name='Cooperative programming', help_text='Is it possible to join the coding group?') 
    number_of_devolopers = CharField(max_length=100,verbose_name='Number of devolopers', help_text='How many people are involved in the model development?', choices=(('less than 10', 'less than 10'), (' less than 20', ' less than 20'), (' less than 50', ' less than 50'), (' more than 50', ' more than 50')), default='less than 10') 
    number_of_users = CharField(max_length=100,verbose_name='Number of users ', help_text='How many people approximately use the model?', choices=(('less than 10', 'less than 10'), (' less than 100', ' less than 100'), (' less than 1000', ' less than 1000'), (' more than 1000', ' more than 1000')), default='less than 10') 
    modelling_software = ArrayField(models.CharField(max_length=100, help_text='What modelling software and which version is used?'),default=list)
    interal_data_processing_software = ArrayField(models.CharField(max_length=100, help_text='Which data processing software is required?'),default=list)

    external_optimizer = BooleanField(default=False,verbose_name='External optimizer', help_text='Which external optimizer can the model apply?', null=False) 
    external_optimizer_yes_text = ArrayField(models.CharField(max_length=100),default=list)

    additional_software = ArrayField(models.CharField(max_length=100,help_text='Which additional software is required to run the model?'),default=list)
    gui = BooleanField(default=False,verbose_name='GUI', help_text='Is a graphical user interface available?', null=False) 

    citation_reference = CharField(max_length=1000,verbose_name='Citation reference', help_text='publications about the model', null=True)
    citation_DOI = CharField(max_length=1000,verbose_name='Citation DOI', help_text='publications about the model', null=True) 
    references_to_reports_produced_using_the_model = CharField(max_length=1000,verbose_name='References to reports produced using the model', help_text='Which studies have been calculated with this model?', null=True) 
    larger_scale_usage = CharField(max_length=1000,verbose_name='Larger scale usage', help_text='Is this model used on a larger scale? If so, who uses it?', null=True) 


class Energymodel(BasicFactsheet):
    energy_sectors_electricity = BooleanField(default=False,verbose_name='electricity') 
    energy_sectors_heat = BooleanField(default=False,verbose_name='heat') 
    energy_sectors_liquid_fuels = BooleanField(default=False,verbose_name='liquid fuels') 
    energy_sectors_gas = BooleanField(default=False,verbose_name='gas') 
    energy_sectors_oil = BooleanField(default=False,verbose_name='oil') 
    energy_sectors_others = BooleanField(default=False,verbose_name='others')
    energy_sectors_others_text = CharField(max_length=200,null=True)
     
    demand_sectors_households = BooleanField(default=False,verbose_name='Households') 
    demand_sectors_industry = BooleanField(default=False,verbose_name='Industry') 
    demand_sectors_commercial_sector = BooleanField(default=False,verbose_name='Commercial sector') 
    demand_sectors_transport = BooleanField(default=False,verbose_name='Transport')
     
    energy_carrier_gas_natural_gas = BooleanField(default=False,verbose_name='Natural gas') 
    energy_carrier_gas_biogas = BooleanField(default=False,verbose_name='Biogas') 
    energy_carrier_gas_hydrogen = BooleanField(default=False,verbose_name='Hydrogen') 

    energy_carrier_liquids_petrol = BooleanField(default=False,verbose_name='Petrol')
    energy_carrier_liquids_diesel = BooleanField(default=False,verbose_name='Diesel')
    energy_carrier_liquids_ethanol = BooleanField(default=False,verbose_name='Ethanol')

    energy_carrier_solid_hard_coal = BooleanField(default=False,verbose_name='Hard coal') 
    energy_carrier_solid_hard_lignite = BooleanField(default=False,verbose_name='Lignite') 
    energy_carrier_solid_hard_uranium = BooleanField(default=False,verbose_name='Uranium') 
    energy_carrier_solid_hard_biomass = BooleanField(default=False,verbose_name='Biomass') 

    energy_carrier_renewables_sun = BooleanField(default=False,verbose_name='Sun')
    energy_carrier_renewables_wind = BooleanField(default=False,verbose_name='Wind')
    energy_carrier_renewables_hydro = BooleanField(default=False,verbose_name='Hydro')
    energy_carrier_renewables_geothermal_heat = BooleanField(default=False,verbose_name='Geothermal heat')

    generation_renewables_PV = BooleanField(default=False,verbose_name='PV') 
    generation_renewables_wind = BooleanField(default=False,verbose_name='Wind') 
    generation_renewables_hydro = BooleanField(default=False,verbose_name='Hydro') 
    generation_renewables_biomass = BooleanField(default=False,verbose_name='Biomass') 
    generation_renewables_biogas = BooleanField(default=False,verbose_name='Biogas') 
    generation_renewables_solar_thermal = BooleanField(default=False,verbose_name='Solar thermal') 
    generation_renewables_others = BooleanField(default=False,verbose_name='Others')
    generation_renewables_others_text = CharField(max_length=200,null=True) 

    generation_conventional_gas = BooleanField(default=False,verbose_name='gas')
    generation_conventional_coal = BooleanField(default=False,verbose_name='coal')
    generation_conventional_oil = BooleanField(default=False,verbose_name='oil')
    generation_conventional_liquid_fuels = BooleanField(default=False,verbose_name='liquid fuels')
    generation_conventional_nuclear = BooleanField(default=False,verbose_name='nuclear')
     
    generation_CHP = BooleanField(default=False,verbose_name='CHP') 

    transfer_electricity = BooleanField(default=False,verbose_name="electricity") 
    transfer_electricity_distribution = BooleanField(default=False,)
    transfer_electricity_transition = BooleanField(default=False,)

    transfer_gas = BooleanField(default=False,verbose_name="gas") 
    transfer_gas_distribution = BooleanField(default=False,)
    transfer_gas_transition = BooleanField(default=False,)

    transfer_heat = BooleanField(default=False,verbose_name="heat") 
    transfer_heat_distribution = BooleanField(default=False,)
    transfer_heat_transition = BooleanField(default=False,)

    network_coverage_AC = BooleanField(default=False,verbose_name='AC load flow') 
    network_coverage_DC = BooleanField(default=False,verbose_name='DC load flow') 

    storage_electricity_battery = BooleanField(default=False,verbose_name='battery') 
    storage_electricity_kinetic = BooleanField(default=False,verbose_name='kinetic') 
    storage_electricity_CAES = BooleanField(default=False,verbose_name='CAES') 
    storage_electricity_PHS = BooleanField(default=False,verbose_name='PHS') 
    storage_electricity_chemical = BooleanField(default=False,verbose_name='chemical') 

    storage_heat = BooleanField(default=False,verbose_name='heat') 
    storage_gas = BooleanField(default=False,verbose_name='gas') 

    user_behaviour = BooleanField(default=False,verbose_name='User behaviour and demand side management', help_text='How can user behaviour changes and demand side management be considered?') 
    user_behaviour_yes_text = CharField(max_length=200,null=True) 

    market_models = BooleanField(default=False,verbose_name='Market models', help_text='Which / Is a market models are included?') 

    geographical_coverage = ArrayField(models.CharField(max_length=100,help_text='What regions are covered? Please, list the regions covered by the model. Leave blank, if the model and data are not limited to a specific region. Example input: USA, Canada, Mexico', default=""),default=list)

    geo_resolution_global = BooleanField(default=False,verbose_name='global') 
    geo_resolution_continents = BooleanField(default=False,verbose_name='continents') 
    geo_resolution_national_states = BooleanField(default=False,verbose_name='national states') 
    geo_resolution_TSO_regions = BooleanField(default=False,verbose_name='TSO regions') 
    geo_resolution_federal_states = BooleanField(default=False,verbose_name='federal states') 
    geo_resolution_regions = BooleanField(default=False,verbose_name='regions') 
    geo_resolution_NUTS_3 = BooleanField(default=False,verbose_name='NUTS 3') 
    geo_resolution_municipalities = BooleanField(default=False,verbose_name='municipalities') 
    geo_resolution_districts = BooleanField(default=False,verbose_name='districts') 
    geo_resolution_households = BooleanField(default=False,verbose_name='households') 
    geo_resolution_power_stations = BooleanField(default=False,verbose_name='power stations') 
    geo_resolution_others = BooleanField(default=False,verbose_name='others') 
    geo_resolution_others_text = CharField(max_length=200,null=True)

    comment_on_geo_resolution = CharField(max_length=200,verbose_name='Comment on geographic (spatial) resolution', help_text='Feel free to explain the geographical resolution of the model e.g. with regard to the grid data.', null=True) 

    time_resolution_anual = BooleanField(default=False,verbose_name='anual') 
    time_resolution_hour = BooleanField(default=False,verbose_name='hour') 
    time_resolution_15_min = BooleanField(default=False,verbose_name='15 min') 
    time_resolution_1_min = BooleanField(default=False,verbose_name='1 min') 

    observation_period_1_year = BooleanField(default=False,verbose_name='>1 year') 
    observation_period_1_year = BooleanField(default=False,verbose_name='1 year') 

    time_resolution_other = BooleanField(default=False,verbose_name='other') 
    time_resolution_other_text = CharField(max_length=200,null=True)

    additional_dimensions_sector_ecological = BooleanField(default=False,verbose_name='ecological') 
    additional_dimensions_sector_ecological_text = CharField(max_length=100,null=True) 
    additional_dimensions_sector_economic = BooleanField(default=False,verbose_name='economic') 
    additional_dimensions_sector_economic_text = CharField(max_length=100,null=True)
    additional_dimensions_sector_social = BooleanField(default=False,verbose_name='social')
    additional_dimensions_sector_social_text = CharField(max_length=100,null=True)  
    additional_dimensions_sector_others = BooleanField(default=False,verbose_name='others') 
    additional_dimensions_sector_others_text = CharField(max_length=100,null=True)

    model_class_optimization_LP = BooleanField(default=False,verbose_name='LP') 
    model_class_optimization_MILP = BooleanField(default=False,verbose_name='MILP')
    model_class_optimization_Nonlinear = BooleanField(default=False,verbose_name='Nonlinear')
    model_class_optimization_LP_MILP_Nonlinear_text = CharField(max_length=100,null=True)

    model_class_simulation_Agentbased = BooleanField(default=False,verbose_name='Agent-based')
    model_class_simulation_System_Dynamics = BooleanField(default=False,verbose_name='System Dynamics') 
    model_class_simulation_Accounting_Framework = BooleanField(default=False,verbose_name='Accounting Framework') 
    model_class_simulation_Game_Theoretic_Model = BooleanField(default=False,verbose_name='Game Theoretic Model')

    model_class_other = BooleanField(default=False,verbose_name='Other') 
    model_class_other_text = BooleanField(default=False,) 

    short_description_of_mathematical_model_class = CharField(max_length=100,verbose_name='Short description of mathematical model class', null=True) 

    mathematical_objective_cO2 = BooleanField(default=False,verbose_name='CO2') 
    mathematical_objective_costs = BooleanField(default=False,verbose_name='costs') 
    mathematical_objective_rEshare = BooleanField(default=False,verbose_name='RE-share') 
    mathematical_objective_other = BooleanField(default=False,verbose_name='other') 
    mathematical_objective_other_text = BooleanField(default=False,)

    uncertainty_deterministic = BooleanField(default=False,verbose_name='Deterministic') 
    uncertainty_Stochastic = BooleanField(default=False,verbose_name='Stochastic')
    uncertainty_Other = BooleanField(default=False,verbose_name='Other')

    montecarlo = BooleanField(default=False,verbose_name='Suited for many scenarios / monte-carlo') 

    typical_computation_time_less_than_a_second = BooleanField(default=False,verbose_name='less than a second') 
    typical_computation_time_less_than_a_minute = BooleanField(default=False,verbose_name='less than a minute') 
    typical_computation_time_less_than_an_hour = BooleanField(default=False,verbose_name='less than an hour') 
    typical_computation_time_less_than_a_day = BooleanField(default=False,verbose_name='less than a day') 
    typical_computation_time_more_than_a_day = BooleanField(default=False,verbose_name='more than a day') 

    typical_computation_hardware = CharField(max_length=1000,verbose_name='Typical computation hardware', help_text='Here you can specify which hardware was assumed to estimate above time (e.g. RAM, CPU, GPU, etc).', null=True) 
    technical_data_anchored_in_the_model = CharField(max_length=1000,verbose_name='Technical data anchored in the model', help_text='If there is technical data already embedded (hard code) in the model and not part of the scenario, please make that transparent here.', null=True) 
    
    example_research_questions = CharField(max_length=1000,verbose_name='Example research questions', help_text='What would be a good research question that could be answered with the model?', null=True) 

    validation = CharField(max_length=1000,verbose_name='Validation', help_text='How is the model validated?', null=True) 
    model_specific_properties = CharField(max_length=1000,verbose_name='Model specific properties', help_text='What are main specific characteristics (strengths and weaknesses) of this model regarding the purpose of the recommendation?', null=True)
    

    
class Energyframework(BasicFactsheet):
    model_types = CharField(max_length=20, choices=[(x,x) for x in ["Grid optimisation", "demand simulation", "feed-in simulation", "other + text"]], verbose_name="API to openmod database" , null=True)
    model_types_other_text = CharField(max_length=100, null=True)
    api_doc = URLField(verbose_name="Link to API documentation", null=True)
    data_api = BooleanField(verbose_name="API to openmod database")
    abstraction = TextField(verbose_name="Points/degree of abstraction", null=True)
    used = ArrayField(CharField(max_length=100), verbose_name="Models using this framework", default = list, null=True)

