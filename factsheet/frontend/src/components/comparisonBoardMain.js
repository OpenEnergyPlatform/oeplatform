import React, { useState, useEffect, } from 'react';
import ComparisonBoardItems from "./comparisonBoardItems";
import { Box } from "@mui/system";
import ComparisonControl from "./comparisonControl";

import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { Link } from 'react-router-dom';
import Button from '@mui/material/Button';
import axios from 'axios';
import conf from "../conf.json";


const ComparisonBoardMain = (props) => {
  const { params } = props;

  const [scenarios, setScenarios] = useState([]);
  
  const scenario_acronyms = params.split('CASPECTS')[0].split('-');
  const scenario_acronyms_json = JSON.stringify(scenario_acronyms);

  const scenario_aspects = params.split('CASPECTS')[1].split('-');

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

  return (
    scenarios.length !== 0 && <Box sx={{ 
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      alignItems: 'center',
      overflow: 'auto',
      height: '100%',
     }}>
       {/* <ComparisonControl /> */}
        <Box sx={{ 
            width: '100%',
            display: 'block',
          }}>
            <Link to={`sirop/`} onClick={() => this.forceUpdate}>
              <Button color="primary" variant="outlined" size="small" style={{ 'height': '43px', 'textTransform': 'none', 'marginLeft': '30px', 'marginTop': '20px', 'zIndex': '1000' }}>
                <ArrowBackIcon />
              </Button>
            </Link>  
          </Box>
      <ComparisonBoardItems elements={scenarios} c_aspects={scenario_aspects} />
    </Box>
  );
};

export default ComparisonBoardMain;
