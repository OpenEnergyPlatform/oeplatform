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
import { Tooltip } from '@mui/material';
import ArrowRightIcon from '@mui/icons-material/ArrowRight';
import BreadcrumbsNavGrid from '../styles/oep-theme/components/breadcrumbsNavigation.js';
import OptionBox from '../styles/oep-theme/components/optionBox.js';
import MultipleSelectChip from '../styles/oep-theme/components/multiselect.js';

const ComparisonBoardMain = (props) => {
  const { params } = props;
  const [scenarios, setScenarios] = useState([]);
  const scenarios_uid = params.split('#');
  const scenarios_uid_json = JSON.stringify(scenarios_uid);
  const [selectedCriteria, setselectedCriteria] = useState(['Descriptors', 'Study name']);

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
    'Scenario abstract',
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
          </Grid>
        </Toolbar>
        {/* <ComparisonControl /> */}
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
      </Container>
    </Grid>
  );
};

export default ComparisonBoardMain;
