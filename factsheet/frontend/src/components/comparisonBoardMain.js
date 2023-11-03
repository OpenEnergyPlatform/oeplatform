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
  const scenarios_uid = params.split('#');
  const scenarios_uid_json = JSON.stringify(scenarios_uid);
  const [selectedCriteria, setselectedCriteria] = useState(['Descriptors']);

  const getScenarios = async () => {
    const { data } = await axios.get(conf.toep + `scenario-bundles/get_scenarios/`, { params: { scenarios_uid: scenarios_uid_json } });
    return data;
  };

  useEffect(() => {
    getScenarios().then((data) => {
      setScenarios(data);
      });
  }, []);


  const Criteria = [
    'Study name',
    'Study abstract',
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
          <div style={{ backgroundColor: '#e3eaef', height: '100px', marginBottom: '10px' }}>
            <div id='headerStyle'>
            <span>
              <ListAltOutlinedIcon />
            </span>
            <span>Scenario Bundle</span>
            </div>
          <div id='headerSubStyle'> <span> Comparison </span> </div>
          </div>
        </Grid>
        <Container maxWidth="false">
            <Box sx={{ 
              padding: '5px',
              margin: '5px',
              display: 'block'}}
            >
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Link to={`scenario-bundles/main`} onClick={() => this.forceUpdate}>
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
              padding: '5px',
              paddingLeft: '15px',
              margin: '5px',
              backgroundColor: '#F6F9FB',
              overflow: 'auto',
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
