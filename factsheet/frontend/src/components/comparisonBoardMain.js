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

const ComparisonBoardMain = (props) => {

  const { params } = props;
  const [scenarios, setScenarios] = useState([]);
  const scenarios_uid = params.split('#');
  const scenarios_uid_json = JSON.stringify(scenarios_uid);
  const [selectedCriteria, setselectedCriteria] = useState(['Study descriptors', 'Scenario types', 'Study name']);
  const [alignment, setAlignment] = React.useState('Qualitative');
  const [sparqOutput, setSparqlOutput] = useState('');
  const [scenarioYear, setScenarioYear] = React.useState('2020');
  const [chartData, setChartData] = React.useState([]);
  const [chartLabels, setChartLabels] = React.useState([]);
  const [loading, setLoading] = useState(false);
  const [showChart, setShowChart] = useState(false);

  

  const getScenarios = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_scenarios/`, { params: { scenarios_uid: scenarios_uid_json } });
    return data;
  };

  useEffect(() => {
    getScenarios().then((data) => {
      setScenarios(data);
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

  const handleYearChange = (event) => {
    setScenarioYear(event.target.value);
    const filtered_output = sparqOutput.filter(item => item.year.value == event.target.value)
    const country = filtered_output.map((obj) => obj.country_code.value.split('/').pop() );
    const value = filtered_output.map((obj) => obj.value.value );
    setChartData(value);
    setChartLabels(country);
    
  };

  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const data_tabels = `"scenario_eu_leg_data_2021"`;
  const scenario_years =  `"2020", "2025", "2030", "2035", "2040"`;
  const categories =  `"1.A.3 Transport"`;

  const query = `PREFIX obo: <http://purl.obolibrary.org/obo/>
  PREFIX ou: <http://opendata.unex.es/def/ontouniversidad#>
  PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
  PREFIX oeo: <http://openenergy-platform.org/ontology/oeo/>
  PREFIX llc:  <https://www.omg.org/spec/LCC/Countries/ISO3166-1-CountryCodes/>
  
  SELECT DISTINCT ?table_name ?value ?unit ?country_code ?year ?category WHERE {
    ?s oeo:OEO_00000504 ?table_name .
    ?s oeo:OEO_00040010 ?unit .
    ?s oeo:IAO_0000136 oeo:OEO_00000025.
    ?s oeo:OEO_00020226 oeo:OEO_00020310 .
    ?s oeo:has_sector_division ?category .
    ?s oeo:OEO_00140178 ?value .
    ?s oeo:OEO_00010378 ?country_code .
    ?s oeo:OEO_00020224 ?year .
    FILTER(?year IN (${scenario_years}) && ?table_name IN (${data_tabels}) && ?category IN (${categories})) .
  } ORDER BY Asc(?year)`;

  const sendQuery = async () => {
    setLoading(true);
    const response = await axios.post(
      'http://localhost:8080/sparql',  
      query,
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
      const filtered_output = sparqOutput.filter(item => item.year.value == scenarioYear)
      const country = filtered_output.map((obj) => obj.country_code.value.split('/').pop() );
      const value = filtered_output.map((obj) => obj.value.value );
      setChartData(value);
      setChartLabels(country);
      setLoading(false);
      setShowChart(true);
    }).catch(error => {
        console.error('API Error:', error.message);
    }).finally(() => {
    });
  }

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

  const options = {
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
        <Grid container >
          <Grid item xs={11}>
            
          </Grid>
          <Grid item xs={1}>
            <Button variant="outlined" endIcon={<SendIcon />} onClick={sendQuery} >Go</Button>
          </Grid>
          <Grid item xs={12}>
            {loading == true && <Box sx={{ paddingTop: "10px" }}>
              <LinearProgress />
            </Box>}
            {showChart == true && <Grid container>
              <Grid item xs={12}>
                <FormControl fullWidth margin="dense">
                  <FormLabel ></FormLabel>
                  <RadioGroup
                    row
                    name="row-radio-buttons-group"
                    onChange={handleYearChange}
                    defaultValue="2020"
                  >
                    <Box sx={{ 
                      display: 'flex', 
                      paddingLeft: '20px',
                      paddingRight: '20px',
                      justifyContent: 'space-between',
                      width: '100%'
                    }}>
                      <FormControlLabel value="2020" control={<Radio />} label="2020" />
                      <FormControlLabel value="2025" control={<Radio />} label="2025" />
                      <FormControlLabel value="2030" control={<Radio />} label="2030" />
                      <FormControlLabel value="2035" control={<Radio />} label="2035" />
                      <FormControlLabel value="2040" control={<Radio />} label="2040" />
                    </Box>
                    </RadioGroup>
                  </FormControl>
              </Grid>
              <Grid item xs={12}>
                <Bar data={dataBar1} options={options} width={100} height={40} />
              </Grid>
            </Grid>}
          </Grid>
        </Grid>
        } 
      </Container>
    </Grid>
  );
};

export default ComparisonBoardMain;
