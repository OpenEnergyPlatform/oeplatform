import React, { useState } from 'react';
import ComparisonBoardItems from "./comparisonBoardItems";
import { Box } from "@mui/system";
import ComparisonControl from "./comparisonControl";

const ComparisonBoardMain = (props) => {
  const { items } = props;

  return (
    <Box sx={{ 
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      alignItems: 'center',
      width: '100%',
      overflow: 'auto',
      height: '100%',
      padding: '20px'
     }}>
       <ComparisonControl />
       <ComparisonBoardItems factsheetName = {'A'} elements={
          [
            { id: '2', 
              content: 'DEV06439',
              'institutions': ['IKL', 'OTF'],
              'scenario-descriptors': ['100% renewables', 'negative emission'],
              'scenarios': ['Klimaschutzszenario-7480',' Mit-Erweiterten-Maßnahmen-Szenario'],
              'region': ['Germany'],
              'scenario_years': ['2020', '2025', '2030', '2035', '2040', '2045', '2050', '2055', '2060'],
              'enrgy-transformation-processes': ['heat transfer', "chemical energy transfer", ],
              'descriptors':  ['sufficiency', 'Greenhouse gas emissions', 'CO2 emissions', 'total net electricity generation', 'degree of electrifiaction', 'peak electricity generation'],
              'sectors': ['CRF sectors (IPCC 2006)'],
              'enrgy-carriers': ["compressed air", "natural gas", 'water'],
              'models': ["PowerG", "FOREC"],
              'frameworks': ["Open Energy Modelling KL"],
            }, 
            { id: '1', 
              content: 'DJHG9087',
              'institutions': ['IKL', 'RLS'],
              'scenario-descriptors': ['100% renewables', 'grid / infrastructure extension'],
              'scenarios': ['Klimaschutzszenario-7480', 'Mit-Erweiterten-Maßnahmen-Szenario'],
              'region': ['Germany'],
              'scenario_years': ['2020', '2025', '2030', '2035', '2040', '2045', '2050', '2055', '2060'],
              'enrgy-transformation-processes': ['heat transfer', 'electrical energy transfer'],
              'descriptors': ['total gross electricity generation',
                'total net electricity generation',
                'peak electricity generation'],
              'sectors': ['CRF sectors (IPCC 2006)'],
              'enrgy-carriers': ['liquid air', 'renewable fuel', 'water'],
              'models': ["PowerG"],
              'frameworks': ["Open Energy Modelling KL"],
            },
            { id: '0', 
                content: 'PIO876',
                'institutions': ['FH'],
                'scenario-descriptors': ['acceptance', 'sufficiency', 'grid restrictions' ],
                'scenarios': ['Klimaschutzszenario-4575', 'Mit-Erweiterten-Maßnahmen-Szenario'],
                'region': ['Germany'],
                'scenario_years': ['2020', '2025', '2030', '2035', '2040', '2045', '2050', '2055', '2060'],
                'enrgy-transformation-processes': [
                  'heat transfer', 'solar-steam-electric process', 'photovoltaic energy transformation'
                ],
                'descriptors': ["(changes in) demand", "total gross electricity generation"],
                'sectors': ['CRF sectors (IPCC 1996)'],
                'enrgy-carriers': [
                  'coal', 
                 'natural gas'
                ],
                'frameworks': ["Open Energy Modelling KL"],
                'models': ["FOREC"],
            },
            { id: '3', 
              content: 'HFG987',
              'institutions': [],
              'scenario-descriptors': [],
              'scenarios': [],
              'region': [],
              'scenario_years': [],
              'enrgy-transformation-processes': [],
              'descriptors': [],
              'sectors': [],
              'enrgy-carriers': [],
              'models': [],
              'frameworks': [],
            }
          ]}/>
    </Box>
  );
};

export default ComparisonBoardMain;
