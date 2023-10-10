import React, { useState, useEffect, } from 'react';
import ComparisonBoardItems from "./comparisonBoardItems";
import { Box } from "@mui/system";
import ComparisonControl from "./comparisonControl";
import Grid from '@mui/material/Grid';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { Link } from 'react-router-dom';
import Button from '@mui/material/Button';
import axios from 'axios';
import conf from "../conf.json";
import ListAltOutlinedIcon from '@mui/icons-material/ListAltOutlined';
import Container from '@mui/material/Container';
import Checkbox from '@mui/material/Checkbox';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Stack from '@mui/material/Stack';
import ArrowRightIcon from '@mui/icons-material/ArrowRight';

const ComparisonBoardMain = (props) => {
  const { params } = props;
  const [scenarios, setScenarios] = useState([]);
  console.log(params);
  const scenario_acronyms = params.split('-');
  const scenario_acronyms_json = JSON.stringify(scenario_acronyms);
  const [selectedCriteria, setselectedCriteria] = useState(['Descriptors']);

  const getScenarios = async () => {
    const { data } = await axios.get(conf.toep + `sirop/get_scenarios/`, { params: { scenarios_acronym: scenario_acronyms_json } });
    return data;
  };

  useEffect(() => {
    getScenarios().then((data) => {
      setScenarios(data);
      });
  }, []);

  console.log(scenarios);

  const Criteria = [
    'Descriptors',
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

  return (
    scenarios.length !== 0 && 
    <Grid container
      direction="row"
      justifyContent="space-between"
      alignItems="center"
    >
        <Grid item xs={12} >
          <div style={{ backgroundColor: '#e3eaef', height: '150px', marginBottom: '10px' }}>
            <div id='headerStyle'>
            <span>
              <ListAltOutlinedIcon />
            </span>
            <p>Scenario Bundle</p>
            </div>
          <div id='headerSubStyle'> <span> Comparison </span> </div>
          </div>
        </Grid>
        <Container maxWidth="xl">
            <Box sx={{ 
              padding: '10px',
              margin: '10px',
              display: 'block'}}
            >
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Link to={`sirop/`} onClick={() => this.forceUpdate}>
                <Button color="primary" 
                        variant="outlined" 
                        size="small" 
                        startIcon={<ArrowBackIcon />}>
                  Back
                </Button>
              </Link> 
              <Button color="primary" 
                      variant="outlined" 
                      size="small" 
                      startIcon={<ArrowRightIcon />}>
                How it works? 
              </Button>
            </Stack>
            </Box>
            {/* <ComparisonControl /> */}
            <Box sx={{ 
              padding: '20px',
              margin: '20px',
              backgroundColor: '#F6F9FB',
              display: 'block'}}
              >
              <b>Criteria</b>
              <FormGroup>
                <div >
                  {
                    Criteria.map((item) => <FormControlLabel control={<Checkbox size="medium" color="primary" />} checked={selectedCriteria.includes(item)} onChange={handleCriteria} label={item} name={item} />)
                  }
                </div>
              </FormGroup>
            </Box>
            <ComparisonBoardItems elements={scenarios} c_aspects={selectedCriteria} />
        </Container>
      </Grid>
    );
};

export default ComparisonBoardMain;
