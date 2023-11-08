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
import Toolbar from '@mui/material/Toolbar';
import ArrowRightIcon from '@mui/icons-material/ArrowRight';
import BreadcrumbsNavGrid from '../styles/oep-theme/components/breadcrumbsNavigation.js';

const ComparisonBoardMain = (props) => {
  const { params } = props;
  const [scenarios, setScenarios] = useState([]);
  const scenarios_uid = params.split('#');
  const scenarios_uid_json = JSON.stringify(scenarios_uid);
  const [selectedCriteria, setselectedCriteria] = useState(['Descriptors']);

  const getScenarios = async () => {
    const { data } = await axios.get(conf.toep + `sirop/get_scenarios/`, { params: { scenarios_uid: scenarios_uid_json } });
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
      <BreadcrumbsNavGrid subheaderContent="Comparison" />
      <Container maxWidth="false">
        <Toolbar sx={{ marginBottom: theme => theme.spacing(4) }}>
          <Grid container justifyContent="space-between"
            spacing={2}>
            <Grid item xs={12} md={4}>
              <Link to={`sirop/`} onClick={() => this.forceUpdate}>
                <Button color="primary" 
                  variant="text" 
                  size="small" 
                  startIcon={<ArrowBackIcon />}>
                  Back
                </Button>
              </Link> 
            </Grid>
            <Grid item xs={6} md={4}>
            </Grid>
            <Grid item xs={6} md={4}>
              <Button color="primary" 
                variant="outlined" 
                size="small" 
                startIcon={<ArrowRightIcon />}>
                How it works? 
              </Button>
            </Grid>
          </Grid>   
        </Toolbar>
        {/* <ComparisonControl /> */}
        <Box sx={{ 
          padding: '5px',
          paddingLeft: '15px',
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
