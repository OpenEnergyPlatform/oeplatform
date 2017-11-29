from django.db import models
from django.contrib.postgres import fields
from django import forms
from django.contrib.postgres.fields import ArrayField
from django.db.models import CharField, ImageField, BooleanField, IntegerField, CharField, EmailField, TextField, ForeignKey, SmallIntegerField
# Create your models here.

class BasicFactsheet(models.Model):
    model_name = CharField(max_length=1000,verbose_name='Name', help_text='What is the full model name?', null=False, unique=True) 
    acronym = CharField(max_length=20,verbose_name='Acronym', help_text='What is the abbreviation?', null=False) 
    institutions = ArrayField(CharField(max_length=1000, help_text='Which institutions develop(ed) the model?') ,default=list, null=True, verbose_name='Institution(s)')
    authors = ArrayField(CharField(max_length=300, help_text='Who are the authors? Where do / did they work, on which parts of the model, during which time period?'),default=list, null=True,verbose_name='Author(s) (institution, working field, active time period)') 
    current_contact_person = CharField(max_length=1000, verbose_name='Current contact person', help_text='Who is the main contact person?', null=True) 
    contact_email = EmailField(verbose_name='Contact (e-mail)', help_text='Please, fill in an e-mail address.', null=False) 
    website = CharField(max_length=200,verbose_name='Website', null=True) 
    logo = ImageField(upload_to='logos',verbose_name='Logo', null=True)
    primary_purpose = TextField(verbose_name='Primary Purpose', help_text='What is the primary purpose the model?', null=True) 
    primary_outputs = TextField(verbose_name='Primary Outputs', help_text='What are the main outputs of the model?', null=True) 
    support = BooleanField(default=False,verbose_name='Support / Community / Forum') 

    framework = BooleanField(default=False,verbose_name='Framework', help_text='Is the model based on a framework? If yes, which?') 
    framework_yes_text = CharField(max_length=1000,null=True) 

    user_documentation = CharField(max_length=200,verbose_name='Link to User Documentation', help_text='Where is the user documentation publicly available?', null=True) 
    code_documentation = CharField(max_length=200,verbose_name='Link to Developer/Code Documentation', help_text='Where is the code documentation publicly available?', null=True)
    documentation_quality = CharField(max_length=1000,verbose_name='Documentation quality', help_text='How is the quality of the documentations?', choices=((x,x) for x in ['not available', 'expandable', 'good', 'excellent']), default='expandable') 
    source_of_funding = CharField(max_length=200,verbose_name='Source of funding', help_text='What is the main source of funding?', null=True)
    open_source = BooleanField(default=False,verbose_name='Open Source') 
    open_up = BooleanField(default=False,verbose_name='Planned to open up in the future', help_text='Will the source code be available in future?') 
    costs = CharField(max_length=1000,verbose_name='Costs', null=True) 
    license = CharField(max_length=20,verbose_name='License', choices=((x,x) for x in ['MIT Licence', 'Apache Licence', 'GNU GPL Licence', 'Other']), default='Apache Licence') 
    license_other_text = CharField(max_length=1000,null=True)
    source_code_available = BooleanField(default=False,verbose_name='Source code available', help_text='Is the source code directly downloadable?') 
    gitHub = BooleanField(default=False,verbose_name='GitHub', help_text='Is the model available on GitHub?') 
    link_to_source_code = CharField(max_length=200,verbose_name='Link to source code', null=True) 
    data_provided = CharField(max_length=1000,verbose_name='Data provided', help_text='Is the necessary data to run a scenario available?', choices=(('none', 'none'), ('some', 'some'), ('all', 'all')), default='none') 
    cooperative_programming = BooleanField(default=False,verbose_name='Cooperative programming', help_text='Is it possible to join the coding group?') 
    number_of_devolopers = CharField(max_length=1000,verbose_name='Number of devolopers', help_text='How many people are involved in the model development?', choices=(('less than 10', 'less than 10'), (' less than 20', ' less than 20'), (' less than 50', ' less than 50'), (' more than 50', ' more than 50')), null=True) 
    number_of_users = CharField(max_length=1000,verbose_name='Number of users ', help_text='How many people approximately use the model?', choices=(('less than 10', 'less than 10'), (' less than 100', ' less than 100'), (' less than 1000', ' less than 1000'), (' more than 1000', ' more than 1000')), null=True) 
    modelling_software = ArrayField(models.CharField(max_length=1000, help_text='What modelling software and which version is used?'),verbose_name='Modelling software ', default=list, null=False)
    interal_data_processing_software = ArrayField(models.CharField(max_length=1000, help_text='Which data processing software is required? Please list all software (packages) that are used for internal data processing'),verbose_name='Internal data processing software',default=list, null=True)

    external_optimizer = BooleanField(default=False,verbose_name='External optimizer', help_text='Which external optimizer can the model apply?', null=False) 
    external_optimizer_yes_text = ArrayField(models.CharField(max_length=1000),default=list, null=True)

    additional_software = ArrayField(models.CharField( max_length=1000,help_text='Which additional software is required to run the model?'),verbose_name='Additional software',default=list,null=True)
    gui = BooleanField(default=False,verbose_name='GUI', help_text='Is a graphical user interface available?', null=False) 

    citation_reference = CharField(max_length=10000,verbose_name='Citation reference', help_text='Please list publications about the model', null=True)
    citation_DOI = CharField(max_length=10000,verbose_name='Citation DOI', help_text='If  there are publications about the model that have a DOI please liste the DOIs', null=True) 
    references_to_reports_produced_using_the_model = CharField(max_length=10000,verbose_name='Please list references to reports produced using the model', help_text='Which studies have been calculated with this model?', null=True) 
    larger_scale_usage = CharField(max_length=10000,verbose_name='Larger scale usage', help_text='Is this model used on a larger scale? If so, who uses it?', null=True) 


class Energymodel(BasicFactsheet):
    energy_sectors_electricity = BooleanField(default=False,verbose_name='electricity') 
    energy_sectors_heat = BooleanField(default=False,verbose_name='heat') 
    energy_sectors_liquid_fuels = BooleanField(default=False,verbose_name='liquid fuels') 
    energy_sectors_gas = BooleanField(default=False,verbose_name='gas') 
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

    transfer_electricity = BooleanField(default=False,verbose_name='electricity') 
    transfer_electricity_distribution = BooleanField(default=False,verbose_name='distribution')
    transfer_electricity_transition = BooleanField(default=False,verbose_name='transmission')

    transfer_gas = BooleanField(default=False,verbose_name='gas') 
    transfer_gas_distribution = BooleanField(default=False,verbose_name='distribution')
    transfer_gas_transition = BooleanField(default=False,verbose_name='transmission')

    transfer_heat = BooleanField(default=False,verbose_name='heat') 
    transfer_heat_distribution = BooleanField(default=False,verbose_name='distribution')
    transfer_heat_transition = BooleanField(default=False,verbose_name='transmission')

    network_coverage_AC = BooleanField(default=False,verbose_name='AC load flow') 
    network_coverage_DC = BooleanField(default=False,verbose_name='DC load flow') 
    network_coverage_NT = BooleanField(default=False,verbose_name='net transfer capacities') 

    storage_electricity_battery = BooleanField(default=False,verbose_name='battery') 
    storage_electricity_kinetic = BooleanField(default=False,verbose_name='kinetic') 
    storage_electricity_CAES = BooleanField(default=False,verbose_name='compressed air') 
    storage_electricity_PHS = BooleanField(default=False,verbose_name='pump hydro') 
    storage_electricity_chemical = BooleanField(default=False,verbose_name='chemical') 

    storage_heat = BooleanField(default=False,verbose_name='heat') 
    storage_gas = BooleanField(default=False,verbose_name='gas') 

    user_behaviour = BooleanField(default=False,verbose_name='User behaviour and demand side management', help_text='How can user behaviour changes and demand side management be considered?') 
    user_behaviour_yes_text = TextField(null=True) 
    changes_in_efficiency = TextField(null=True, verbose_name='Changes in efficiency')
    
    market_models = CharField(max_length=20, verbose_name='Market models', choices=((x,x) for x in ['fundamental model', 'stochastic model']), null=True, help_text='Which / Is a market models are included?') 

    geographical_coverage = ArrayField(models.CharField(max_length=1000), help_text='What regions are covered? Please, list the regions covered by the model. Leave blank, if the model and data are not limited to a specific region. Example input: USA, Canada, Mexico' ,verbose_name='Geographical coverage', default=list, null=True)

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

    comment_on_geo_resolution = TextField(verbose_name='Comment on geographic (spatial) resolution', help_text='Feel free to explain the geographical resolution of the model e.g. with regard to the grid data.', null=True) 

    time_resolution_anual = BooleanField(default=False,verbose_name='anual') 
    time_resolution_hour = BooleanField(default=False,verbose_name='hour') 
    time_resolution_15_min = BooleanField(default=False,verbose_name='15 min') 
    time_resolution_1_min = BooleanField(default=False,verbose_name='1 min') 

    observation_period_more_1_year = BooleanField(default=False,verbose_name='>1 year') 
    observation_period_less_1_year = BooleanField(default=False,verbose_name='<1 year') 
    observation_period_1_year = BooleanField(default=False,verbose_name='1 year')
    observation_period_other = BooleanField(default=False,verbose_name='other')
    observation_period_other_text = CharField(max_length=200,null=True) 

    time_resolution_other = BooleanField(default=False,verbose_name='other') 
    time_resolution_other_text = CharField(max_length=200,null=True)

    additional_dimensions_sector_ecological = BooleanField(default=False,verbose_name='ecological') 
    additional_dimensions_sector_ecological_text = CharField(max_length=1000,null=True) 
    additional_dimensions_sector_economic = BooleanField(default=False,verbose_name='economic') 
    additional_dimensions_sector_economic_text = CharField(max_length=1000,null=True)
    additional_dimensions_sector_social = BooleanField(default=False,verbose_name='social')
    additional_dimensions_sector_social_text = CharField(max_length=1000,null=True)  
    additional_dimensions_sector_others = BooleanField(default=False,verbose_name='others') 
    additional_dimensions_sector_others_text = CharField(max_length=1000,null=True)

    model_class_optimization_LP = BooleanField(default=False,verbose_name='LP') 
    model_class_optimization_MILP = BooleanField(default=False,verbose_name='MILP')
    model_class_optimization_Nonlinear = BooleanField(default=False,verbose_name='Nonlinear')
    model_class_optimization_LP_MILP_Nonlinear_text = CharField(max_length=1000,null=True)

    model_class_simulation_Agentbased = BooleanField(default=False,verbose_name='Agent-based')
    model_class_simulation_System_Dynamics = BooleanField(default=False,verbose_name='System Dynamics') 
    model_class_simulation_Accounting_Framework = BooleanField(default=False,verbose_name='Accounting Framework') 
    model_class_simulation_Game_Theoretic_Model = BooleanField(default=False,verbose_name='Game Theoretic Model')

    model_class_other = BooleanField(default=False,verbose_name='Other') 
    model_class_other_text = CharField(max_length=1000,null=True) 

    short_description_of_mathematical_model_class = TextField(verbose_name='Short description of mathematical model class', null=True) 

    mathematical_objective_cO2 = BooleanField(default=False,verbose_name='CO2') 
    mathematical_objective_costs = BooleanField(default=False,verbose_name='costs') 
    mathematical_objective_rEshare = BooleanField(default=False,verbose_name='RE-share') 
    mathematical_objective_other = BooleanField(default=False,verbose_name='other') 
    mathematical_objective_other_text = CharField(max_length=200, null=True)

    uncertainty_deterministic = BooleanField(default=False,verbose_name='Deterministic') 
    uncertainty_Stochastic = BooleanField(default=False,verbose_name='Stochastic')
    uncertainty_Other = BooleanField(default=False,verbose_name='Other')
    uncertainty_Other_text = CharField(max_length=200,null=True,verbose_name='Other')

    montecarlo = BooleanField(default=False,verbose_name='Suited for many scenarios / monte-carlo') 

    typical_computation_time = CharField(max_length=30, choices=((x,x) for x in ['less than a second','less than a minute','less than an hour','less than a day','more than a day'])) 

    typical_computation_hardware = CharField(max_length=10000,verbose_name='Typical computation hardware', help_text='Here you can specify which hardware was assumed to estimate above time (e.g. RAM, CPU, GPU, etc).', null=True) 
    technical_data_anchored_in_the_model = CharField(max_length=10000,verbose_name='Technical data anchored in the model', help_text='If there is technical data already embedded (hard code) in the model and not part of the scenario, please make that transparent here.', null=True) 
    
    example_research_questions = CharField(max_length=10000,verbose_name='Example research questions', help_text='What would be good research questions that could be answered with the model?', null=True) 

    validation_models = BooleanField(verbose_name='cross-checked with other models', default=False)
    validation_measurements = BooleanField(verbose_name='checked with measurements (measured data)', default=False)
    validation_others = BooleanField(verbose_name='others', default=False)
    validation_others_text = CharField(max_length=1000, null=True)
    
    model_specific_properties = CharField(max_length=10000,verbose_name='Model specific properties', help_text='What are main specific characteristics (strengths and weaknesses) of this model regarding the purpose of the recommendation?', null=True)
    

    interfaces = TextField(verbose_name='Interfaces', help_text='Which APIs does the model have?', null=True)
    model_file_format = CharField(max_length=5, choices=map(lambda x:(x,x),('.exe','.gms','.py','.xls','Other')), verbose_name='Model file format', help_text='In which format is the model saved?', default='other', null=True)
    model_file_format_other_text = CharField(max_length=1000,null=True)
    model_input = CharField(max_length=5, choices=map(lambda x:(x,x),('.csv','.py','text','.xls','Other')), verbose_name='Input data file format', help_text='Of which file format are the input data?', default='other',null=True)
    model_input_other_text = CharField(max_length=1000,null=True)
    model_output = CharField(max_length=5, choices=map(lambda x:(x,x),('.csv','.py','text','.xls','Other')), verbose_name='Output data file format', help_text='Of which file format are the output data?', default='other',null=True)
    model_output_other_text = CharField(max_length=1000,null=True)
    integrating_models = ArrayField(TextField(), verbose_name='Integration with other models',help_text='With which models has this model been integrated into (providing a link)? Where is the combined model available?', null=True)
    integrated_models = ArrayField(TextField(), verbose_name='Integration of other models',help_text='Which models are integrated in the model? Where are these models available?', null=True)

    
class Energyframework(BasicFactsheet):
    def __init__(self, *args, **kwargs):
        super(BasicFactsheet, self).__init__(*args, **kwargs)
        for o in self._meta.fields:
            if 'help_text' in o.__dict__:
                o.help_text = o.help_text.replace('model', 'framework')       
    model_types_grid = BooleanField(default=False, verbose_name='Grid optimisation')
    model_types_demand_simulation = BooleanField(default=False, verbose_name='demand simulation')
    model_types_feed_in_simulation = BooleanField(default=False, verbose_name='feed-in simulation')
    model_types_other = BooleanField(default=False, verbose_name='Other')    
    model_types_other_text = CharField(max_length=1000, null=True)
    
    api_doc = CharField(max_length=200,verbose_name='Link to API documentation', null=True)
    data_api = BooleanField(verbose_name='API to openmod database')
    abstraction = TextField(verbose_name='Points/degree of abstraction', null=True)
    used = ArrayField(CharField(max_length=1000),verbose_name='Models using this framework', default = list, null=True)


class Energystudy(models.Model):
  

    def __str__(self):
      return self.name_of_the_study
    
    name_of_the_study = CharField(verbose_name='Name of the study', help_text='What is the name of the study?', max_length=1000) 
    author_Institution = CharField(verbose_name='Author, Institution', help_text='Who are the authors of the study and for which institution do they work?', max_length=1000) 
    client = CharField(verbose_name='Client', help_text='Who are the customers requesting the study?', max_length=1000, null=True) 
    funding_private = BooleanField(verbose_name='private') 
    funding_public = BooleanField(verbose_name='public') 
    funding_no_funding = BooleanField(verbose_name='no funding') 
    citation_reference = ArrayField(CharField(max_length=1000),verbose_name='Citation reference',  null=True)
    citation_doi = ArrayField(CharField(max_length=1000), verbose_name='Citation doi', null=True)
    aim = CharField(verbose_name='Aim', help_text='What is the purpose (hypothesis) and research question of the study?', max_length=1000, null=True) 
    new_aspects = CharField(verbose_name='New aspects', help_text='What is new? (beyond state of research)', max_length=1000, null=True) 
    spatial_Geographical_coverage = CharField(verbose_name='Spatial / Geographical coverage', help_text='Which geographical region is adressed in the study?', max_length=1000, null=True) 
    time_frame_2020 = BooleanField(verbose_name='2020') 
    time_frame_2030 = BooleanField(verbose_name='2030') 
    time_frame_2050 = BooleanField(verbose_name='2050') 
    time_frame_other = BooleanField(verbose_name='other')
    time_frame_other_text = CharField(max_length=1000, null=True)
     
    time_frame_2_target_year = BooleanField(verbose_name='target year') 
    time_frame_2_transformation_path = BooleanField(verbose_name='transformation path') 
    tools_models = ForeignKey(to='Energymodel', verbose_name='Tools', help_text='Which model(s) and other tools have been used?', null=True) 
    tools_other = CharField(verbose_name='Tools', help_text='Which model(s) and other tools have been used?' , max_length=1000, null=True)
    modeled_energy_sectors_electricity = BooleanField(verbose_name='electricity') 
    modeled_energy_sectors_heat = BooleanField(verbose_name='heat') 
    modeled_energy_sectors_liquid_fuels = BooleanField(verbose_name='liquid fuels') 
    modeled_energy_sectors_gas = BooleanField(verbose_name='gas')  
    modeled_energy_sectors_others = BooleanField(verbose_name='others') 
    modeled_energy_sectors_others_text = CharField(max_length=1000, null=True)
    
    modeled_demand_sectors_households = BooleanField(verbose_name='households') 
    modeled_demand_sectors_industry = BooleanField(verbose_name='industry') 
    modeled_demand_sectors_commercial_sector = BooleanField(verbose_name='commercial sector') 
    modeled_demand_sectors_transport = BooleanField(verbose_name='transport')
     
    economic_behavioral_perfect = BooleanField(verbose_name='single fictive decision-maker with perfect knowledge (perfect foresight optimization)') 

    economic_behavioral_myopic = BooleanField(verbose_name='single fictive decision-maker with myopic foresight (time-step optimization)') 
    economic_behavioral_qualitative = BooleanField(verbose_name='decisions simulated by modeller due to qualitative criteria (spread-sheet simulation)') 
    economic_behavioral_agentbased = BooleanField(verbose_name='representation of heterogenous decision rules for multiple agents (agent-based approach)') 
    economic_behavioral_other = BooleanField(verbose_name='other')
    economic_behavioral_other_text = CharField(max_length=1000, null=True) 

    renewables_PV = BooleanField(verbose_name='PV')
    renewables_wind = BooleanField(verbose_name='wind')
    renewables_hydro = BooleanField(verbose_name='hydro')
    renewables_biomass = BooleanField(verbose_name='biomass')
    renewables_biogas = BooleanField(verbose_name='biogas')
    renewables_solar = BooleanField(verbose_name='solar thermal')
    renewables_others = BooleanField(verbose_name='others')
    renewables_others_text = CharField(max_length=1000, null=True) 
     
    conventional_generation_gas = BooleanField(verbose_name='gas')
    conventional_generation_coal = BooleanField(verbose_name='coal')
    conventional_generation_oil = BooleanField(verbose_name='oil')
    conventional_generation_liquid = BooleanField(verbose_name='liquid fuels')
    conventional_generation_nuclear = BooleanField(verbose_name='nuclear')
     
    CHP = BooleanField(verbose_name='CHP')

    networks_electricity_gas_electricity = BooleanField(verbose_name='electricity') 
    networks_electricity_gas_gas = BooleanField(verbose_name='gas')
    networks_electricity_gas_heat = BooleanField(verbose_name='heat')

    storages_battery = BooleanField(verbose_name='battery')
    storages_kinetic = BooleanField(verbose_name='kinetic')
    storages_CAES = BooleanField(verbose_name='compressed air')
    storages_PHS = BooleanField(verbose_name='pump hydro') 
    storages_chemical = BooleanField(verbose_name='chemical')

    economic_focuses_included = CharField(verbose_name='Economic focuses included', help_text='Have there been economic focusses/sectors included?', max_length=1000, null=True) 
    social_focuses_included = CharField(verbose_name='Social focuses included', help_text='Have there been social focusses/sectors included? ', max_length=1000, null=True) 
    endogenous_variables = CharField(verbose_name='Endogenous variables', help_text='Which time series and variables are generated inside the model?', max_length=1000, null=True) 
    sensitivities = BooleanField(verbose_name='Sensitivities', help_text='Have there been sensitivities?') 
    time_steps_anual = BooleanField(verbose_name='anual') 
    time_steps_hour = BooleanField(verbose_name='hour') 
    time_steps_15_min = BooleanField(verbose_name='15 min') 
    time_steps_1_min = BooleanField(verbose_name='1 min') 
    time_steps_sec = BooleanField(verbose_name='sec') 
    time_steps_other = BooleanField(verbose_name='other') 
    time_steps_other_text = CharField(max_length=1000, null=True)
    

    
class Energyscenario(models.Model):
 
    study = ForeignKey('Energystudy', db_column='name_of_the_study_id', null=True, blank=True)
 
    exogenous_time_series_used_climate = BooleanField(verbose_name='climate') 
    exogenous_time_series_used_feedin = BooleanField(verbose_name='feed-in') 
    exogenous_time_series_used_loadcurves = BooleanField(verbose_name='load-curves') 
    exogenous_time_series_used_others = BooleanField(verbose_name='others')
    exogenous_time_series_used_others_text = CharField(max_length=1000, null=True) 

    technical_data = CharField(verbose_name='Technical data + usage', help_text='What kind of technical data(sets) are included /used? (heat-/powerplants; grid infrastructure;...) What were the data(sets) used for (e.g. model calibration)?', max_length=1000, null=True) 
    social_data = CharField(verbose_name='Social data', help_text='What kind of social data(sets) are included / were used / considered? (e.g. demographic changes, employment rate; social structure, ...) What were the data(sets) used for (e.g. model calibration)?', max_length=1000, null=True) 
    economical_data = CharField(verbose_name='Economical data', help_text='What kind of economical data(sets) are included / were used? (e.g. price structures, market settings,...) What were the data(sets) used for (e.g. model calibration)?', max_length=1000, null=True) 
    ecological_data = CharField(verbose_name='Ecological data', help_text='What kind of ecological data(sets) are included / were used? (e.g. landuse, CO2 emissions,...) What were the data(sets) used for (e.g. model calibration)?', max_length=1000, null=True) 
    preProcessing = CharField(verbose_name='Pre-Processing', help_text='Have the mentioned values been modified before being used for the modelling exercise or are they used directly? Please, describe what kind of modification have been made? Additionally, you can link to data processing scripts.', max_length=1000, null=True) 
    name_of_scenario = CharField(verbose_name='Name of the Scenario', help_text='What is the name of the scenario?', max_length=1000, unique=True) 

    energy_saving_amount = SmallIntegerField(verbose_name='Energy savings', help_text='development of energy savings or efficiency', null=True) 
    energy_saving_kind = CharField(max_length=15, choices=(('until','until'),('per','per'),('not estimated','not estimated')), default='not estimated', null=True) 
    energy_saving_year = SmallIntegerField(null=True) 

    potential_energy_savings_amount = SmallIntegerField(verbose_name='Potential energy saving', help_text='How was the potential of energy savings determined?', null=True) 
    potential_energy_savings_kind = CharField(max_length=15, choices=(('until','until'),('per','per'),('not estimated','not estimated')), default='not estimated', null=True) 
    potential_energy_savings_year = SmallIntegerField(null=True)  

    emission_reductions_amount = SmallIntegerField(verbose_name='Emission reductions', help_text='Development of emissions', null=True) 
    emission_reductions_kind = CharField(max_length=15, choices=(('until','until'),('per','per'),('not estimated','not estimated')), default='not estimated', null=True) 
    emission_reductions_year = SmallIntegerField(null=True) 

    share_RE_power_amount = SmallIntegerField(verbose_name='Share RE (power sector)', help_text='Development of renewable energy in the power sector', null=True) 
    share_RE_power_kind = CharField(max_length=15, choices=(('until','until'),('per','per'),('not estimated','not estimated')), default='not estimated', null=True) 
    share_RE_power_year = SmallIntegerField(null=True) 

    share_RE_heat_amount = SmallIntegerField(verbose_name='Share RE (heat sector)', help_text='development of renewable energy in the heat sector', null=True) 
    share_RE_heat_kind = CharField(max_length=15, choices=(('until','until'),('per','per'),('not estimated','not estimated')), default='not estimated', null=True) 
    share_RE_heat_year = SmallIntegerField(null=True) 

    share_RE_mobility_amount = SmallIntegerField(verbose_name='Share RE (mobility sector)', help_text='development of renewable energy in the mobility sector', null=True) 
    share_RE_mobility_kind = CharField(max_length=15, choices=(('until','until'),('per','per'),('not estimated','not estimated')), default='not estimated', null=True) 
    share_RE_mobility_year = SmallIntegerField(null=True) 
    
    share_RE_total_amount = SmallIntegerField(verbose_name='Share RE (total energy supply)', help_text='development of total renewable energy supply', null=True) 
    share_RE_total_kind = CharField(max_length=15, choices=(('until','until'),('per','per'),('not estimated','not estimated')), default='not estimated', null=True) 
    share_RE_total_year = SmallIntegerField(null=True) 

    cost_development_capex = BooleanField(verbose_name='capex') 
    cost_development_opex = BooleanField(verbose_name='opex') 
    cost_development_learning_curves = BooleanField(verbose_name='learning curves') 
    cost_development_constant = BooleanField(verbose_name='constant') 
    cost_development_rediscount = BooleanField(verbose_name='rediscount') 

    technological_innovations = CharField(verbose_name='Technological innovations', help_text='Have future technological innovations been regarded?', max_length=10000, null=True) 

    potential_wind_whole = BooleanField(verbose_name='whole') 
    potential_wind_technical = BooleanField(verbose_name='technical') 
    potential_wind_economical = BooleanField(verbose_name='economical') 
    potential_wind_ecological = BooleanField(verbose_name='ecological') 
    potential_wind_other = BooleanField(verbose_name='other') 
    potential_wind_other_text = CharField(max_length=1000, null=True)

    potential_solar_electric_whole = BooleanField(verbose_name='whole') 
    potential_solar_electric_technical = BooleanField(verbose_name='technical') 
    potential_solar_electric_economical = BooleanField(verbose_name='economical') 
    potential_solar_electric_ecological = BooleanField(verbose_name='ecological') 
    potential_solar_electric_other = BooleanField(verbose_name='other') 
    potential_solar_electric_other_text = CharField(max_length=1000, null=True)

    potential_solar_thermal_whole = BooleanField(verbose_name='whole') 
    potential_solar_thermal_technical = BooleanField(verbose_name='technical') 
    potential_solar_thermal_economical = BooleanField(verbose_name='economical') 
    potential_solar_thermal_ecological = BooleanField(verbose_name='ecological') 
    potential_solar_thermal_other = BooleanField(verbose_name='other') 
    potential_solar_thermal_other_text = CharField(max_length=1000, null=True)

    potential_biomass_whole = BooleanField(verbose_name='whole') 
    potential_biomass_technical = BooleanField(verbose_name='technical') 
    potential_biomass_economical = BooleanField(verbose_name='economical') 
    potential_biomass_ecological = BooleanField(verbose_name='ecological') 
    potential_biomass_other = BooleanField(verbose_name='other') 
    potential_biomass_other_text = CharField(max_length=1000, null=True)

    potential_geothermal_whole = BooleanField(verbose_name='whole') 
    potential_geothermal_technical = BooleanField(verbose_name='technical') 
    potential_geothermal_economical = BooleanField(verbose_name='economical') 
    potential_geothermal_ecological = BooleanField(verbose_name='ecological') 
    potential_geothermal_other = BooleanField(verbose_name='other')
    potential_geothermal_othertext = CharField(max_length=1000, null=True)

    potential_hydro_power_whole = BooleanField(verbose_name='whole') 
    potential_hydro_power_technical = BooleanField(verbose_name='technical') 
    potential_hydro_power_economical = BooleanField(verbose_name='economical') 
    potential_hydro_power_ecological = BooleanField(verbose_name='ecological') 
    potential_hydro_power_other = BooleanField(verbose_name='other')
    potential_hydro_power_other_text = CharField(max_length=1000, null=True)

    social_developement = CharField(verbose_name='Social developement', help_text='How are changes of social structure considered? (e.g. demographic changes, employment rate, ...)', max_length=1000, null=True) 
    economic_development = CharField(verbose_name='Economic development', help_text='e.g. price structures, market settings,..', max_length=1000, null=True) 
    development_of_environmental_aspects = CharField(verbose_name='Development of environmental aspects', help_text='e.g. landuse', max_length=1000, null=True) 
    postprocessing = BooleanField(verbose_name='Post-processing', help_text='Are the presented results directly taken from the models’ outcome or are they modified?') 
    further_assumptions_for_postprocessing = BooleanField(verbose_name='Further assumptions for post-processing', help_text='Are additional assumptions applied for this modification?') 
    further_assumptions_for_postprocessing_text = CharField(max_length=1000, null=True)
    uncertainty_assessment = CharField(verbose_name='Uncertainty assessment', help_text='How are the identified uncertain factors considered in the study?', max_length=1000, null=True) 
    robustness = CharField(verbose_name='Robustness', help_text='How is the robustness of the results proofed?', max_length=1000, null=True) 
    comparability_Validation = CharField(verbose_name='Comparability / Validation', help_text='How far do the modelling results fit in compared to similar scientific research?', max_length=1000, null=True) 
    conclusions = CharField(verbose_name='Conclusions', help_text='What political, social (or in another way) relevant conclusions are drawn from the scenario analysis? ', max_length=1000, null=True) 

