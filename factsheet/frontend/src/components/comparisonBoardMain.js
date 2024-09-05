import React, { useState, useEffect, } from 'react';
import Chart from "chart.js/auto";
import { Bar } from "react-chartjs-2";
import ComparisonBoardItems from "./comparisonBoardItems";
// import { Box } from "@mui/system";
// import ComparisonControl from "./comparisonControl";
import Grid from '@mui/material/Grid';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { Link } from 'react-router-dom';
import Button from '@mui/material/Button';
import axios from 'axios';
import conf from "../conf.json";
// import ListAltOutlinedIcon from '@mui/icons-material/ListAltOutlined';
import Container from '@mui/material/Container';
import Checkbox from '@mui/material/Checkbox';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Toolbar from '@mui/material/Toolbar';
import { Tooltip, Box } from '@mui/material';
import ArrowRightIcon from '@mui/icons-material/ArrowRight';
import BreadcrumbsNavGrid from '../styles/oep-theme/components/breadcrumbsNavigation.js';
import OptionBox from '../styles/oep-theme/components/optionBox.js';
// import MultipleSelectChip from '../styles/oep-theme/components/multiselect.js';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import ManageSearchIcon from '@mui/icons-material/ManageSearch';
import EqualizerIcon from '@mui/icons-material/Equalizer';
import Typography from '@mui/material/Typography';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormControl from '@mui/material/FormControl';
import FormLabel from '@mui/material/FormLabel';
import 'chartjs-plugin-datalabels'
import CSRFToken from './csrfToken.js';
import CircularProgress from '@mui/material/CircularProgress';
import SendIcon from '@mui/icons-material/Send';
import LinearProgress from '@mui/material/LinearProgress';
import OutlinedInput from '@mui/material/OutlinedInput';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import ListItemText from '@mui/material/ListItemText';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import AddIcon from '@mui/icons-material/Add';
import { useRef } from 'react';
import Tabs, { tabsClasses } from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';

const ComparisonBoardMain = (props) => {

  const { params } = props;
  const [scenarios, setScenarios] = useState([]);
  const scenarios_uid = params.split('#');
  const scenarios_uid_json = JSON.stringify(scenarios_uid);
  const [selectedCriteria, setselectedCriteria] = useState(['Study descriptors', 'Scenario types', 'Study name']);
  const [alignment, setAlignment] = React.useState('Qualitative');
  const [sparqOutput, setSparqlOutput] = useState([]);
  const [scenarioYear, setScenarioYear] = React.useState([]);
  const [scenarioYears, setScenarioYears] = React.useState([]);
  const [chartData, setChartData] = React.useState([]);
  const [chartLabels, setChartLabels] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [showChart, setShowChart] = React.useState(false);
  const [categoryNames, setCategoryNames] = React.useState([]);
  const [gasesNames, setGasesNames] = React.useState([]);
  const [selectedCategories, setSelectedCategories] = React.useState([]);
  const [selectedGas, setSelectedGas] = React.useState([]);
  const [selectedScenarios, setSelectedScenarios] = React.useState([]);
  const [visualizationRows, addVisualizationRows] = React.useState(0);
  const [inputTableNames, setInputTableNames] = React.useState([]);
  const [outputTableNames, setoutputTableNames] = React.useState([]);
  const [selectedInputDatasets, setSelectedInputDatasets] = React.useState([]);
  const [selectedOutputDatasets, setSelectedOutputDatasets] = React.useState([]);
  const [scenariosNamesInTables, setScenariosNamesInTables] = React.useState([]);
  const [scenariosInTables, setScenariosInTables] = React.useState([]);
  const [barColors, setBarColors] = React.useState([]);
  const chartRef = useRef(null);
  const [openEmptyResultDialog, setOpenEmptyResultDialog] = React.useState(false);
  const [legendForGroupedStackedBarCharts, setLegendForGroupedStackedBarCharts] = React.useState([]);
  const [legendForStackedBarCharts, setLegendForStackedBarCharts] = React.useState([]);
  const [chartType, setChartType] = React.useState("");
  const [groupedBarChartsRandomColors, setGroupedBarChartsRandomColors] = React.useState([]);
  
  
  const category_disctionary = {
    "OEO_00010038" : "1 Energy",
    "OEO_00010039" : "1.A Fuel combustion",
    "OEO_00010040" : "1.A.1 Energy industries",
    "OEO_00010158" : "1.A.1.a Public electricity and heat production",
    "OEO_00010159" : "1.A.1.b Petroleum refining",
    "OEO_00010160" : "1.A.1.c Manufacture of solid fuels and other energy industries",
    "OEO_00010041" : "1.A.2 Manufacturing industries and construction",
    "OEO_00010042" : "1.A.3 Transport",
    "OEO_00010059" : "1.A.3.a Domestic aviation",
    "OEO_00010060" : "1.A.3.b Road transportation",
    "OEO_00010061" : "1.A.3.c Railways",
    "OEO_00010062" : "1.A.3.d Domestic navigation",
    "OEO_00010063" : "1.A.3.e Other transportation",
    "OEO_00010043" : "1.A.4 Other sectors",
    "OEO_00010052" : "1.A.4.a Commercial/Institutional",
    "OEO_00010053" : "1.A.4.b Residential",
    "OEO_00010054" : "1.A.4.c Agriculture/Forestry/Fishing",
    "OEO_00010044" : "1.A.5 Other",
    "OEO_00010057" : "1.B Fugitive emissions from fuels",
    "OEO_00010161" : "1.B.1 Solid fuels",
    "OEO_00010162" : "1.B.2 Oil and natural gas and other emissions from energy production",
    "OEO_00010058" : "1.C CO2 transport and storage",
    "OEO_00010046" : "2 Industrial processes",
    "OEO_00010164" : "2.A Mineral Industry",
    "OEO_00010165" : "2.A.1 Cement production",
    "OEO_00010166" : "2.B Chemical industry",
    "OEO_00010167" : "2.C Metal industry",
    "OEO_00010168" : "2.C.1 Iron and steel production",
    "OEO_00010169" : "2.D Non-energy products from fuels and solvent use",
    "OEO_00010170" : "2.E Electronics industry",
    "OEO_00010171" : "2.F Product uses as substitutes for ODS",
    "OEO_00010172" : "2.G Other product manufacture and use",
    "OEO_00010173" : "2.H Other",
    "OEO_00010047" : "3 Agriculture",
    "OEO_00010179" : "3.A Enteric fermentation",
    "OEO_00010180" : "3.B Manure management",
    "OEO_00010181" : "3.C Rice cultivation",
    "OEO_00010182" : "3.D Agricultural soils",
    "OEO_00010183" : "3.E Prescribed burning of savannahs",
    "OEO_00010184" : "3.F Field burning of agricultural residues",
    "OEO_00010185" : "3.G Liming",
    "OEO_00010186" : "3.H Urea application",
    "OEO_00010187" : "3.I Other carbon-containing fertilizers",
    "OEO_00010188" : "3.J Other",
    "OEO_00010048" : "4 Land Use, Land-Use Change and Forestry",
    "OEO_00010189" : "4.A Forest land",
  };

  const gas_dictionary = {
    "OEO_00000025" : "Methane (CH4)",
    "OEO_00000027" : "Nitrous_oxide (N2O2)",
    "OEO_00000026" : "Nitrogen Trifluoride (NF3)",
    "OEO_00000219" : "Hydrofluorocarbon (HFC)",
    "OEO_00000006"  : "Carbon dioxide (CO2)",
    "OEO_00000322"  : "Perfluorocarbon (PFC)",
    "OEO_00000038"  : "Sulphur hexafluoride (SF6)",
    "Total_GHGs"  : "Total GHGs",
    "Total_ESD_GHGs" : "Total ESD GHGs",
    "Total_ETS_GHGs"  : "Total ETS GHGs",
    "Total_ESR_GHGs" :"Total ESR GHGs"
  }

  const generateRandomColor = () => {
    return `#${Math.floor(Math.random() * 16777215).toString(16)}`;
  };
  const randomColors = Array.from({ length: Object.keys(category_disctionary).length }, generateRandomColor);

  const scenarios_disctionary = {
    "OEO_00020310" : "without measures scenario (WOM)",
    "OEO_00020311" : "with existing measures scenario (WEM)",
    "OEO_00020312" : "with additional measures scenario (WAM)"
  }
  const getScenarios = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_scenarios/`, { params: { scenarios_uid: scenarios_uid_json } });
    return data;
  };

  useEffect(() => {
    getScenarios().then((data) => {
      setScenarios(data);
      const ScenariosInputTableNames = data.map(obj => obj.data.input_datasets.map(elem => obj.acronym + ':' + elem[1].split('/').pop()));
      const allInputDatasets =  Array.from(new Set(ScenariosInputTableNames.flat()));

      setInputTableNames(allInputDatasets);
      
      const ScenariosOutputTableNames = data.map(obj => obj.data.output_datasets.map(elem => obj.acronym + ':' + elem[1].split('/').pop()));
      const allOutputDatasets = [].concat(...ScenariosOutputTableNames);
      setoutputTableNames(allOutputDatasets);

      setBarColors(randomColors);

    });
  }, []);

  const handleChangeView = (
    event: React.MouseEvent<HTMLElement>,
    newAlignment: string,
  ) => {
    newAlignment !== null && setAlignment(newAlignment);
  };
  
  // 'http://oevkg:8080/sparql'

  const Criteria = [
    'Scenario abstract',
    'Study name',
    'Study abstract',
    'Study descriptors',
    'Scenario types',
    'Regions',
    'Interacting regions',
    'Scenario years',
    'Input datasets',
    'Output datasets',
  ];

  const handleCriteria = (event) => {
    if (event.target.checked) {
      if (!selectedCriteria.includes(event.target.name)) {
        setselectedCriteria([...selectedCriteria, event.target.name]);
      }
    } else {
      const filteredCriteria = selectedCriteria.filter(i => i !== event.target.name);
      setselectedCriteria(filteredCriteria);
    }
  }

  const handleYearChange = (event: React.SyntheticEvent, newValue: number, index) => {
    setLoading(true);
   
    if (sparqOutput.length !== 0) {


      const distinctTables = [];
        sparqOutput.map((obj) => {
          if (!distinctTables.includes(obj.table_name.value)) {
            distinctTables.push(obj.table_name.value)
          }
        } );


      const categorieIDs = [];
      for (let key in category_disctionary) {
          if (selectedCategories.includes(category_disctionary[key])) {
            categorieIDs.push('http://openenergy-platform.org/ontology/oeo/' + key);
          }
      }

      if (distinctTables.length === 1) {
          setChartType("SingleDataTable");
          const distinctYears = [];
          sparqOutput.map((obj) => {
            if (!distinctYears.includes(obj.year.value)) {
              distinctYears.push(obj.year.value)
            }
          } );
      
          const newScenarioYears = scenarioYears;
          newScenarioYears[index] = distinctYears.sort();
          setScenarioYears(newScenarioYears);
    
    
          const newScenarioYear = scenarioYear;
          newScenarioYear[index] = scenarioYears[index][0].toString();
          setScenarioYear(newScenarioYear);

          const filtered_output = sparqOutput.filter(item => item.year.value == newValue);

          const StackedBarChartsLegend = [];
          const country_labels = [];
          const chart_data_category = categorieIDs.map((cat, index) => {
            const categorized =  {}
            categorized['label'] = selectedCategories[index];
            categorized['data'] = filtered_output.filter((obj) => obj.category.value === cat ).map(el => el.value.value );
            categorized['backgroundColor'] = barColors[index];

            country_labels[index] = filtered_output.filter((obj) => obj.category.value === cat ).map(el =>  el.country_code.value.split('/').pop());
            StackedBarChartsLegend.push([selectedCategories[index], barColors[index]]);
            return categorized
          });

          const newChartData = [...chartData];
          newChartData[index] = chart_data_category ;
          setChartData(newChartData);

          const newChartLabels = [...chartLabels];
          newChartLabels[index] = country_labels[index];
          setChartLabels(newChartLabels);

          setLegendForStackedBarCharts(StackedBarChartsLegend);
      }
      else if (distinctTables.length > 1) {
        setChartType("MultipleDataTable");
        const distinctYears = [];
        sparqOutput.map((obj) => {
          if (!distinctYears.includes(obj.year.value)) {
            distinctYears.push(obj.year.value)
          }
        } );
    
        const newScenarioYears = scenarioYears;
        newScenarioYears[index] = distinctYears.sort();
        setScenarioYears(newScenarioYears);

        const newScenarioYear = scenarioYear;
        newScenarioYear[index] = scenarioYears[index][0].toString();
        setScenarioYear(newScenarioYear);

        const filtered_output = sparqOutput.filter(item => item.year.value == newValue);
        const groupedItems = divideByTableNameValue(filtered_output);


        const groupedStackedBarChartsLegend = [];

        const transformGroupedItems = (groupedItems) => {
          const result = {};
          let mainIndex = 0;
          let colorIndex = 0;

          for (let group in groupedItems) {

            const filtered_output = groupedItems[group].sort((a, b) => {
              const countryA = a.country_code.value.split('/').pop();
              const countryB = b.country_code.value.split('/').pop();
              return countryA.localeCompare(countryB);
            });

            const country_labels = [];
            
            const chart_data_category = categorieIDs.map((cat, idx) => {
              const categorized = {};
              categorized['label'] = selectedCategories[index];
              categorized['data'] = filtered_output
                .filter((obj) => obj.category.value === cat)
                .map(el => el.value.value);
              categorized['backgroundColor'] = groupedBarChartsRandomColors[colorIndex];
              categorized['stack'] = mainIndex;
              
              country_labels[index] = filtered_output
                .filter((obj) => obj.category.value === cat)
                .map(el => el.country_code.value.split('/').pop());
              
              groupedStackedBarChartsLegend.push([group, category_disctionary[cat.split("/").pop()], cat,  groupedBarChartsRandomColors[colorIndex]]);
              colorIndex++;
              return categorized;
            });
            
            console.log(country_labels);

            result[group] = {
              chart_data_category: chart_data_category,
              country_labels: country_labels,
            };

            mainIndex++;
          }
        
          return result;
        };
        setLegendForGroupedStackedBarCharts(groupedStackedBarChartsLegend);

        const transformedGroupedItems = transformGroupedItems(groupedItems);

        const datasets = [];
        const labels = [];

        for (let group in transformedGroupedItems) {
          
          const { chart_data_category, country_labels } = transformedGroupedItems[group];

          chart_data_category.forEach((categoryData, catIndex) => {
            const dataset = {};
            dataset['label'] = group ;
            dataset['data'] = categoryData.data;
            dataset['backgroundColor'] = categoryData.backgroundColor;
            dataset['stack'] = categoryData.stack;
            datasets.push(dataset);
            labels.push(country_labels[catIndex]);
          });
        }
        
        const newChartData = [...chartData];
        newChartData[index] = datasets ;
        setChartData(newChartData);
    
        const newChartLabels = [...chartLabels];
        newChartLabels[index] = labels[0];
        setChartLabels(newChartLabels);

      }
        
      const newScenarioYear = scenarioYear;
      newScenarioYear[index] = newValue;
      setScenarioYear(newScenarioYear);

      setLoading(false);
      setShowChart(true);
    } else {
      setLoading(false);
      setShowChart(false);
      setOpenEmptyResultDialog(true);
    }
   
  };

  const ITEM_HEIGHT = 48;
  const ITEM_PADDING_TOP = 8;
  const MenuProps = {
    PaperProps: {
      style: {
        maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
        width: 250,
      },
    },
  };


  const handleScenariosChange = (event: SelectChangeEvent<typeof category>) => {
    const {
      target: { value },
    } = event;
    setSelectedScenarios(
      typeof value === 'string' ? value.split(',') : value,
    );
  };

  const handleCategoriesChange = (event: SelectChangeEvent<typeof category>) => {
    const {
      target: { value },
    } = event;
    setSelectedCategories(
      typeof value === 'string' ? value.split(',') : value,
    );
  };

  const handleGasChange = (event: SelectChangeEvent<typeof category>) => {
    const {
      target: { value },
    } = event;
    setSelectedGas(
      typeof value === 'string' ? value.split(',') : value,
    );
  };
  

  const sendGetScenariosQuery = async () => {
    setLoading(true);

    const get_scenarios_query = `PREFIX oeo: <http://openenergy-platform.org/ontology/oeo/>
              SELECT DISTINCT ?scenario WHERE {
              ?s oeo:OEO_00020226 ?scenario .
    }`  

    const response = await axios.post(
      conf.obdi, 
      get_scenarios_query,
      {
        headers: {
          'X-CSRFToken': CSRFToken(),
          'Accept': 'application/sparql-results+json',
          'Content-Type': 'application/sparql-query',
        },
      }
    ).then(response => {

      const scenariosObj = response.data.results.bindings;

      const scenarios = scenariosObj.map((obj) => obj.scenario.value.split('/').pop() );
      const scenarioNames = scenarios.map((elem) => scenarios_disctionary[elem]); 
      setScenariosInTables(scenarioNames);
      
      setLoading(false);


    }).catch(error => {
        console.error('API Error:', error.message);
    }).finally(() => {
    });
  }



  const sendGetCategoriesQuery = async () => {
    setLoading(true);

    //const data_tabels = [];
    // const data_tabels = [`"eu_leg_data_2023_eea"`, `"scenario_eu_leg_data_2021"`] ;
    const data_tabels = [`"eu_leg_data_2023_eea"`] ;

    selectedOutputDatasets.map(elem  => data_tabels.push('"' + elem.split(":")[1] + '"'));

    const get_categories_query = `PREFIX oeo: <http://openenergy-platform.org/ontology/oeo/>
    SELECT DISTINCT ?category ?table_name WHERE {
      ?s oeo:has_sector_division ?category .
      ?s oeo:OEO_00000504 ?table_name .
      FILTER(?table_name IN ( ${data_tabels} ) ).
    }`

    console.log(get_categories_query);

    const response = await axios.post(
      conf.obdi, 
      get_categories_query,
      {
        headers: {
          'X-CSRFToken': CSRFToken(),
          'Accept': 'application/sparql-results+json',
          'Content-Type': 'application/sparql-query',
        },
      }
    ).then(response => {

      const categoriesObj = response.data.results.bindings;

      const categoriesByTable = categoriesObj.reduce((acc, obj) => {
        const category = obj.category.value;
        const tableName = obj.table_name.value;
      
        if (!acc[tableName]) {
          acc[tableName] = new Set();
        }
      
        acc[tableName].add(category);
      
        return acc;
      }, {});
      
      const allTableNames = Object.values(categoriesByTable);
      const commonCategories = allTableNames.reduce((acc, categoriesSet) => {
        return new Set([...acc].filter(category => categoriesSet.has(category)));
      }, allTableNames[0]);
      
      const filteredObjects = categoriesObj.filter(obj => commonCategories.has(obj.category.value));


      const categories = filteredObjects.map((obj) => obj.category.value.split('/').pop() );
      const catNames = categories.filter(elem => elem in category_disctionary ).map(el => category_disctionary[el] );

      console.log(catNames);

      setCategoryNames(catNames);
      
      setLoading(false);

      const selectedCategorieIDs = Object.keys(category_disctionary).filter(k => category_disctionary[k] in selectedCategories);


    }).catch(error => {
        console.error('API Error:', error.message);
    }).finally(() => {
    });
  }

  const sendGetGasQuery = async () => {
    setLoading(true);
    //const data_tabels = [`"eu_leg_data_2023_eea"`, `"scenario_eu_leg_data_2021"`] ;
    const data_tabels = [ `"scenario_eu_leg_data_2021"`] ;

    selectedOutputDatasets.map(elem  => data_tabels.push('"' + elem.split(":")[1] + '"'));

    const get_gas_query = `PREFIX oeo: <http://openenergy-platform.org/ontology/oeo/>
    SELECT DISTINCT ?gas ?table_name WHERE {
      ?s oeo:OEO_00010121 ?gas .
      ?s oeo:OEO_00000504 ?table_name .
      FILTER(?table_name IN ( ${data_tabels} ) ).
    }`

    console.log(get_gas_query);

    const response = await axios.post(
      conf.obdi, 
      get_gas_query,
      {
        headers: {
          'X-CSRFToken': CSRFToken(),
          'Accept': 'application/sparql-results+json',
          'Content-Type': 'application/sparql-query',
        },
      }
    ).then(response => {

      const gasesObj = response.data.results.bindings;
      console.log(gasesObj);

      const gasesByTable = gasesObj.reduce((acc, obj) => {
        const gas = obj.gas.value;
        const tableName = obj.table_name.value;
      
        if (!acc[tableName]) {
          acc[tableName] = new Set();
        }
      
        acc[tableName].add(gas);
      
        return acc;
      }, {});
      
      const allTableNames = Object.values(gasesByTable);
      console.log(allTableNames);

      const commonGases = allTableNames.reduce((acc, gasesSet) => {
        return new Set([...acc].filter(gas => gasesSet.has(gas)));
      }, allTableNames[0]);
      
      console.log('commonGases', commonGases);

      const gases = Array.from(commonGases).map((obj) => obj.split('/').pop() );
      const gasNames = gases.filter(elem => elem in gas_dictionary ).map(el => gas_dictionary[el] );


      // const gases = filteredObjects.map((obj) => obj.gas.value.split('/').pop() );
      // console.log(gases);
      //const gasNames = gases.filter(elem => elem in category_disctionary ).map(el => category_disctionary[el] );


      //const gases = gasesObj.map((obj) => obj.gas.value );

      setGasesNames(gasNames);
      
      setLoading(false);

    }).catch(error => {
        console.error('API Error:', error.message);
    }).finally(() => {
    });
  }

  const handleInputDatasetsChange = (event: SelectChangeEvent<typeof selectedInputDatasets>) => {
    const {
      target: { value },
    } = event;
    setSelectedInputDatasets(
      typeof value === 'string' ? value.split(',') : value,
    );

    sendGetScenariosQuery();
    sendGetCategoriesQuery();
    sendGetGasQuery();


  };

  const handleOutputDatasetsChange = (event: SelectChangeEvent<typeof selectedOutputDatasets>) => {
    const {
      target: { value },
    } = event;
    setSelectedOutputDatasets(
      typeof value === 'string' ? value.split(',') : value,
    );

    sendGetScenariosQuery();
    sendGetCategoriesQuery();
    sendGetGasQuery();
  };
    
  const handleEmptyResultMessageClose = (event: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    setOpenEmptyResultDialog(false);
  };

  function divideByTableNameValue(items) {
    return items.reduce((acc, obj) => {
      const tableNameValue = obj.table_name.value;
      
      if (!acc[tableNameValue]) {
        acc[tableNameValue] = [];
      }
  
      acc[tableNameValue].push(obj);
      return acc;
    }, {});
  }

const sendQuery = async (index) => {
    setShowChart(false);
    setSparqlOutput([]);
    setLegendForGroupedStackedBarCharts([]);
    setLegendForStackedBarCharts([]);
    setScenarioYears([]);
    setChartData([]);
    console.log(chartData);
    setLoading(true);

    // const data_tabels = [`"eu_leg_data_2023_eea"`, `"scenario_eu_leg_data_2021"`] ;
    const data_tabels = [ `"scenario_eu_leg_data_2021"`] ;
    // const data_tabels = [];

    selectedInputDatasets.map(elem  => data_tabels.push('"' + elem.split(":")[1] + '"'));
    selectedOutputDatasets.map(elem  => data_tabels.push('"' + elem.split(":")[1] + '"'));
    
    const categories = [];
    for (let key in category_disctionary) {
        if (selectedCategories.includes(category_disctionary[key])) {
          categories.push('oeo:' + key);
        }
    }
  
    const gases = [];
    for (let key in gas_dictionary) {
        if (selectedGas.includes(gas_dictionary[key])) {
          gases.push('oeo:' + key);
        }
    }

    const scenariosFilter = [];
    for (let key in scenarios_disctionary) {
        if (selectedScenarios.includes(scenarios_disctionary[key])) {
          scenariosFilter.push('oeo:' + key);
        }
    }
  
    const main_query = `PREFIX obo: <http://purl.obolibrary.org/obo/>
    PREFIX ou: <http://opendata.unex.es/def/ontouniversidad#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX oeo: <http://openenergy-platform.org/ontology/oeo/>
    PREFIX llc:  <https://www.omg.org/spec/LCC/Countries/ISO3166-1-CountryCodes/>
  
    SELECT DISTINCT ?s ?value ?country_code ?year ?category ?gas ?table_name WHERE {
      ?s oeo:OEO_00020221 ?country_code .
      ?s oeo:OEO_00020224 ?year .
      ?s oeo:OEO_00140178 ?value .
      ?s oeo:OEO_00000504 ?table_name .
      ?s oeo:has_sector_division ?category .
      ?s oeo:OEO_00020226 ?scenario .
      ?s oeo:OEO_00010121 ?gas
      FILTER(?table_name IN (${data_tabels}) && ?scenario IN (${scenariosFilter}) && ?category IN (${categories})  && ?gas IN (${gases}) ) .
    }`;

    const response = await axios.post(
      conf.obdi, 
      main_query,
      {
        headers: {
          'X-CSRFToken': CSRFToken(),
          'Accept': 'application/sparql-results+json',
          'Content-Type': 'application/sparql-query',
        },
      }
    ).then(response => {

      const sparqOutput = response.data.results.bindings;
      setSparqlOutput(sparqOutput);

      if (sparqOutput.length !== 0) {

        const distinctTables = [];
        sparqOutput.map((obj) => {
          if (!distinctTables.includes(obj.table_name.value)) {
            distinctTables.push(obj.table_name.value)
          }
        } );

        const categorieIDs = [];
        for (let key in category_disctionary) {
            if (selectedCategories.includes(category_disctionary[key])) {
              categorieIDs.push('http://openenergy-platform.org/ontology/oeo/' + key);
            }
        }

        if (distinctTables.length === 1) {
            setChartType("SingleDataTable");
            const distinctYears = [];
            sparqOutput.map((obj) => {
              if (!distinctYears.includes(obj.year.value)) {
                distinctYears.push(obj.year.value)
              }
            } );
      
            const newScenarioYears = scenarioYears;
            newScenarioYears[index] = distinctYears.sort();
            setScenarioYears(newScenarioYears);
      
      
            const newScenarioYear = scenarioYear;
            newScenarioYear[index] = scenarioYears[index][0].toString();
            setScenarioYear(newScenarioYear);

            const filtered_output = sparqOutput.filter(item => item.year.value == scenarioYear[index]);

            const StackedBarChartsLegend = [];
            const country_labels = [];
            const chart_data_category = categorieIDs.map((cat, index) => {
              const categorized =  {}
              categorized['label'] = selectedCategories[index];
              categorized['data'] = filtered_output.filter((obj) => obj.category.value === cat ).map(el => el.value.value );
              categorized['backgroundColor'] = barColors[index];

              country_labels[index] = filtered_output.filter((obj) => obj.category.value === cat ).map(el =>  el.country_code.value.split('/').pop());

              StackedBarChartsLegend.push([selectedCategories[index], barColors[index]]);
              return categorized
            });

            const newChartData = [...chartData];
            newChartData[index] = chart_data_category ;
            setChartData(newChartData);

            const newChartLabels = [...chartLabels];
            newChartLabels[index] = country_labels[index];
            setChartLabels(newChartLabels);

            setLegendForStackedBarCharts(StackedBarChartsLegend);
        }
        else if (distinctTables.length > 1) {
          setChartType("MultipleDataTable");
          const distinctYears = [];
          sparqOutput.map((obj) => {
            if (!distinctYears.includes(obj.year.value)) {
              distinctYears.push(obj.year.value)
            }
          } );
      
          const newScenarioYears = scenarioYears;
          newScenarioYears[index] = distinctYears.sort();
          setScenarioYears(newScenarioYears);
    
          const newScenarioYear = scenarioYear;
          newScenarioYear[index] = scenarioYears[index][0].toString();
          setScenarioYear(newScenarioYear);

          const filtered_output = sparqOutput.filter(item => item.year.value == scenarioYear[index]);
          const groupedItems = divideByTableNameValue(filtered_output);

          console.log(groupedItems);

          const groupedStackedBarChartsLegend = [];

          const transformGroupedItems = (groupedItems) => {
            const total_num_of_colors =  Object.keys(groupedItems).length + categorieIDs.length
            const groupedRandomColors = Array.from({ length: total_num_of_colors }, generateRandomColor);
            setGroupedBarChartsRandomColors(groupedRandomColors);
            

            const result = {};
            let mainIndex = 0;
            let colorIndex = 0;
          
            for (let group in groupedItems) {
              const filtered_output = groupedItems[group].sort((a, b) => {
                const countryA = a.country_code.value.split('/').pop();
                const countryB = b.country_code.value.split('/').pop();
                return countryA.localeCompare(countryB);
              });

              const country_labels = [];
              
              const chart_data_category = categorieIDs.map((cat, idx) => {
                const categorized = {};
                categorized['label'] = selectedCategories[index];
                categorized['data'] = filtered_output
                  .filter((obj) => obj.category.value === cat)
                  .map(el => el.value.value);
                categorized['backgroundColor'] = groupedRandomColors[colorIndex];
                categorized['stack'] = mainIndex;
                
                country_labels[index] = filtered_output
                  .filter((obj) => obj.category.value === cat)
                  .map(el => el.country_code.value.split('/').pop());
                  
                groupedStackedBarChartsLegend.push([group, category_disctionary[cat.split("/").pop()], cat,  groupedRandomColors[colorIndex]]);
                colorIndex++;
                return categorized;
              });

              result[group] = {
                chart_data_category: chart_data_category,
                country_labels: country_labels,
              };

              mainIndex++;
            }
            return result;
          };

          setLegendForGroupedStackedBarCharts(groupedStackedBarChartsLegend);

          const transformedGroupedItems = transformGroupedItems(groupedItems);

          const datasets = [];
          const labels = [];

          for (let group in transformedGroupedItems) {
            
            const { chart_data_category, country_labels } = transformedGroupedItems[group];
    
            chart_data_category.forEach((categoryData, catIndex) => {
              const dataset = {};
              dataset['label'] = group ;
              dataset['data'] = categoryData.data;
              dataset['backgroundColor'] = categoryData.backgroundColor;
              dataset['stack'] = categoryData.stack;
              datasets.push(dataset);
              labels.push(country_labels[catIndex]);
            });
          }
          
          const newChartData = [...chartData];
          newChartData[index] = datasets ;
          setChartData(newChartData);
      
          const newChartLabels = [...chartLabels];
          newChartLabels[index] = labels[0];
          setChartLabels(newChartLabels);

        }
        
        setLoading(false);
        setShowChart(true);


      } else {
        setLoading(false);
        setShowChart(false);
        setOpenEmptyResultDialog(true);
      }

    }).catch(error => {
        console.error('API Error:', error.message);
    }).finally(() => {
      
    });
  }

  const addVisualization = (index) => {
    addVisualizationRows(visualizationRows + 1);
  };


  const dataBar1 = {
    labels: chartLabels,
    datasets: [
      {
        label: "eu_leg_data_2016_eea",
        backgroundColor: "lightblue",
        borderColor: "rgba(120,99,132,1)",
        borderWidth: 1,
        hoverBackgroundColor: "rgba(255,99,132,0.4)",
        hoverBorderColor: "rgba(255,99,132,1)",
        data: chartData
      }
    ]
  };

  /* const options = {
    plugins: {
      datalabels: {
        display: true,
        color: "black",
        formatter: Math.round,
        font: {
          weight: 'bold'
        },
        align: "top",
        anchor: "end"
      },
      legend: {
        display: false
      },
      tooltips: {
        callbacks: {
           label: function(tooltipItem) {
                  return tooltipItem.yLabel;
           }
        }
      }
    },
  }; */

  const options = {
    scales: {
      x: {
        stacked: true
      },
      y: {
        stacked: true
      }
    },
    plugins: {
      datalabels: {
        display: true,
        color: "black",
        formatter: Math.round,
        font: {
          weight: 'bold'
        },
        align: "top",
        anchor: "end"
      },
      legend: {
        display: false
      },
      tooltips: {
        callbacks: {
           label: function(tooltipItem) {
                  return tooltipItem.yLabel;
           }
        }
      }
    },
  };

  return (
    scenarios.length !== 0 &&
    <Grid container
      direction="row"
      justifyContent="space-between"
      alignItems="center"
    >
      <BreadcrumbsNavGrid subheaderContent="Comparison" />
      <Container maxWidth="lg2">
        <Toolbar sx={{ marginBottom: theme => theme.spacing(4) }}>
          <Grid container justifyContent="space-between"
            spacing={2}>
            <Grid item xs={12} md={4}>
              <Tooltip title="Back to main page">
                <Link to={`scenario-bundles/main`} onClick={() => this.forceUpdate}>
                  <Button variant="outlined" size="small" sx={{ mr: 1 }}>
                    <ArrowBackIcon />
                  </Button>
                </Link>
              </Tooltip>
            </Grid>
            <Grid item xs={6} md={4}>
            </Grid>
            <Grid item xs={6} md={4}>
              <Button color="primary"
                variant="text"
                size="small"
                startIcon={<ArrowRightIcon />}>
                How it works?
              </Button>
            </Grid>
            <Grid item xs={4}>
            </Grid>
            <Grid item xs={6}>
              <ToggleButtonGroup
                    color="primary"
                    value={alignment}
                    exclusive
                    onChange={handleChangeView}
                    aria-label="Platform"
                    size="large"
                  >
                    <ToggleButton style={{ width:'250px' }} value="Qualitative"><ManageSearchIcon />Qualitative</ToggleButton>
                    <ToggleButton style={{ width:'250px' }} value="Quantitative"><EqualizerIcon />Quantitative</ToggleButton>
              </ToggleButtonGroup>
            </Grid>
            <Grid item xs={2}>
            </Grid>
          </Grid>
        </Toolbar>
        {/* <ComparisonControl /> */}

        {alignment == "Qualitative" && 
        <Grid item xs={12}>
          <OptionBox>
            <h2>Criteria</h2>
            <FormGroup>
              <div >
                {
                  Criteria.map((item) => <FormControlLabel control={<Checkbox size="medium" color="primary" />} checked={selectedCriteria.includes(item)} onChange={handleCriteria} label={item} name={item} />)
                }
              </div>
            </FormGroup>
            {/* <MultipleSelectChip
              sx={{ mt: 2, width: "100%" }}
              options={['Scenario 1', 'Scenario 2', 'Scenario 3']}
              label="Scenarios to be compared"
              disabled={true}
            /> */}
          </OptionBox>
          <ComparisonBoardItems elements={scenarios} c_aspects={selectedCriteria} />
        </Grid>
        } 
        {alignment == "Quantitative" && 
        <Grid container spacing={2}>
          {Array.from({ length: visualizationRows }).map((_, index) => (
           <Grid item xs={12}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
               {/*  <Tooltip title={selectedOutputDatasets.length !== 0 ? "Comparison between input datasets and output datasets is not possible. Please make sure there is no selected output datasets" : ""}>
                  <FormControl sx={{ m: 1, width: '48%' }} size="small">
                    <InputLabel id="demo-simple-select-label">Input table(s)</InputLabel>
                    <Select
                      labelId="demo-simple-select-label"
                      id="demo-simple-select"
                      multiple
                      value={selectedInputDatasets}
                      label="Input table(s)"
                      onChange={handleInputDatasetsChange}
                      input={<OutlinedInput label="Input table(s)" />}
                      renderValue={(selected) => selected.join(', ')}
                      MenuProps={MenuProps}
                      disabled={selectedOutputDatasets.length !== 0}
                    >
                      {inputTableNames.map((name, index) => (
                        <MenuItem key={name+index} value={name}>
                          <Checkbox checked={selectedInputDatasets.indexOf(name) > -1} />
                          <ListItemText primary={name} />
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Tooltip> */}
                <Tooltip title={selectedInputDatasets.length !== 0 ? "Comparison between input datasets and output datasets is not possible. Please make sure there is no selected input datasets" : ""}>
                  <FormControl sx={{ m: 1, width: '48%' }} size="small">
                    <InputLabel id="demo-simple-select-label">Output table(s)</InputLabel>
                    <Select
                      labelId="demo-simple-select-label"
                      id="demo-simple-select"
                      multiple
                      value={selectedOutputDatasets}
                      label="Output table(s)"
                      onChange={handleOutputDatasetsChange}
                      input={<OutlinedInput label="Output table(s)" />}
                      renderValue={(selected) => selected.join(', ')}
                      MenuProps={MenuProps}
                      disabled={selectedInputDatasets.length !== 0}
                    >
                      {outputTableNames.map((name, index) => (
                        <MenuItem key={name+index} value={name}>
                          <Checkbox checked={selectedOutputDatasets.indexOf(name) > -1} />
                          <ListItemText primary={name} />
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Tooltip>
                <FormControl sx={{ m: 1, width: '48%' }} size="small">
                  <InputLabel id="demo-simple-select-label">Scenario</InputLabel>
                  <Select
                    labelId="demo-simple-select-label"
                    id="demo-simple-select"
                    value={''}
                    label="Scenario"
                    value={selectedScenarios}
                    onChange={handleScenariosChange}
                    input={<OutlinedInput label="Scenario" />}
                    renderValue={(selected) => selected.join(', ')}
                    MenuProps={MenuProps}
                  > 
                    {scenariosInTables.map((name) => (
                      <MenuItem key={name} value={name}>
                        <ListItemText primary={name} />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl sx={{ m: 1, width: '48%' }} size="small">
                  <InputLabel id="demo-multiple-checkbox-label">Sector(s)</InputLabel>
                  <Select
                    labelId="demo-select-small-label"
                    id="demo-select-small"
                    multiple
                    value={selectedCategories}
                    onChange={handleCategoriesChange}
                    input={<OutlinedInput label="Sector(s)" />}
                    renderValue={(selected) => selected.join(', ')}
                    MenuProps={MenuProps}
                  >
                    {categoryNames.map((name) => (
                      <MenuItem key={name} value={name}>
                        <Checkbox checked={selectedCategories.indexOf(name) > -1} />
                        <ListItemText primary={name} />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl sx={{ m: 1, width: '48%' }} size="small">
                  <InputLabel id="demo-multiple-checkbox-label">Gas(es)</InputLabel>
                  <Select
                    labelId="demo-select-small-label"
                    id="demo-select-small"
                    multiple
                    value={selectedGas}
                    onChange={handleGasChange}
                    input={<OutlinedInput label="Gas(es)" />}
                    renderValue={(selected) => selected.join(', ')}
                    MenuProps={MenuProps}
                  >
                    {gasesNames.map((name) => (
                      <MenuItem key={name} value={name}>
                        <Checkbox checked={selectedGas.indexOf(name) > -1} />
                        <ListItemText primary={name} />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <Button sx={{ m: 1, width: 70 }} size="medium" variant="outlined" endIcon={<SendIcon />} onClick={(event, value) => sendQuery(index)} >Submit</Button>
              </Grid>
              <Grid item xs={12}>
                {showChart == true && <Grid container>
                  <Grid item xs={12}>
                      <Box sx={{ bgcolor: 'background.paper' }}>
                        <Tabs
                          onChange={(e, number) => handleYearChange(e, number, index)}
                          value={scenarioYear[index]}
                          variant="scrollable"
                          scrollButtons
                          aria-label="Scenario years"
                          sx={{
                            [`& .${tabsClasses.scrollButtons}`]: {
                              '&.Mui-disabled': { opacity: 0.3 },
                            },
                          }}
                        >
                          {
                            scenarioYears[index].map((year, idx)  => (
                              <Tab label={year} key={year} value={scenarioYears[index][idx]}/>
                            ) )
                          }
    
                        </Tabs>
                      </Box>
                  </Grid>
                  <Grid item xs={12}>
                    <Bar data={{
                              labels: chartLabels[index],
                              datasets: chartData[index]
                            }} 
                        options={options} width={100} height={40} 
                        ref={chartRef}
                        />
                  </Grid>
                </Grid>}
                </Grid>
              </Grid>
             
              <Divider />
            </Grid>
            ))}
            <Grid item xs={12} >
              <div display="flex" justifyContent="space-between" flexWrap="wrap" alignItems="center">
                {chartType === "MultipleDataTable" && legendForGroupedStackedBarCharts.map((category, idx)  => (
                              <span style={{ marginRight:"20px" }}>
                                <span style={{ width:"20px", height:"20px", display: "inline-block",  borderRadius: "4px", backgroundColor: category[3], verticalAlign:'top' }}> </span>
                                <span style={{ paddingLeft:"10", display: "inline-block", fontSize: "12px", verticalAlign:'initial', marginLeft:'4px' }}> {category[0]}:<b>{category[1]}</b> </span>
                              </span>
                            ) )}
                {chartType === "SingleDataTable" && legendForStackedBarCharts.map((category, idx)  => (
                    <span style={{ marginRight:"20px" }}>
                      <span style={{ width:"20px", height:"20px", display: "inline-block",  borderRadius: "4px", backgroundColor: category[1], verticalAlign:'top' }}> </span>
                      <span style={{ paddingLeft:"10", display: "inline-block", fontSize: "12px", verticalAlign:'initial', marginLeft:'4px' }}> <b>{category[0]}</b> </span>
                    </span>
                  ) )}
              </div>
            </Grid>
            <Grid item xs={12} >
              {loading == true && <Box sx={{ paddingTop: "10px" }}>
                    <LinearProgress />
                  </Box>}
              <Box display="flex" justifyContent="flex-end">
                
                <IconButton
                    color="primary"
                    aria-label="add"
                    onClick={(index) => addVisualization(index)}
                  >
                  <AddIcon />
                </IconButton>
              </Box>
            </Grid>
            <Grid item xs={12} >
              <Snackbar
              open={openEmptyResultDialog}
              autoHideDuration={6000}
              onClose={handleEmptyResultMessageClose}
              >
              <Alert variant="filled" onClose={handleEmptyResultMessageClose} severity="success" sx={{ width: '100%' }}>
                <div>There is still <strong>no data</strong> for the selected filters. Please consider the following: </div>
                <div>(1) Changing the filters. </div>
                <div>(2) Checking the data tables. </div>
                <div>(3) Providing annotations for the selected tables.</div>
              </Alert>
              </Snackbar>
          </Grid>
          </Grid>
          } 
      </Container>
    </Grid>
  );
};

export default ComparisonBoardMain;
