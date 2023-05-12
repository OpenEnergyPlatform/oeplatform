import React, { useState } from 'react';
import ComparisonBoardItem from "./comparisonBoardItem";
import { Box } from "@mui/system";

const ComparisonBoardMain = (props) => {
  const { items } = props;

  return (
    <Box sx={{ 
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      width: '100%',
      overflow: 'auto',
      height: '75vh'
     }}>
       <ComparisonBoardItem factsheetName = {'A'} elements={
          [
            { id: '0', 
              content: 'KSz 2050 R2',
              'enrgy-transformation-processes': [],
              'descriptors':  ['sufficiency', 'Greenhouse gas emissions', 'CO2 emissions', 'total net electricity generation', 'degree of electrifiaction', 'peak electricity generation'],
              'sectors': [],
              'enrgy-carriers': [],
              'models': [{id: "PowerFlex", name: "PowerFlex"}, {id: "FORECAST", name: "FORECAST"}],
              'frameworks': [],
            }, 
           { id: '2', 
             content: 'DeV-KopSys',
             'enrgy-transformation-processes': [],
             'descriptors': ['Greenhouse gas emissions'],
             'sectors': [],
             'enrgy-carriers': [],
             'models': [],
             'frameworks': [],
          },
          { id: '1', 
              content: 'appBBB_gruene2030',
              'enrgy-transformation-processes': [
                {value: 'electricity generation process', label: 'electricity generation process', class: 'http://openenergy-platform.org/ontology/oeo/OEO_00240014'},
                {value: 'gas turbine process', label: 'gas turbine process', class: 'http://openenergy-platform.org/ontology/oeo/OEO_00310027'},
                {value: 'solar energy transformation', label: 'solar energy transformation', class: 'http://openenergy-platform.org/ontology/oeo/OEO_00020046'},
                {value: 'heat generation process', label: 'heat generation process', class: 'http://openenergy-platform.org/ontology/oeo/oeo-physical/OEO_00010248'},
                {value: 'energy transfer', label: 'energy transfer', class: 'http://openenergy-platform.org/ontology/oeo/OEO_00020103'},
              ],
              'descriptors': ["CO2 emissions", "(changes in) demand", "total gross electricity generation"],
              'sectors': [],
              'enrgy-carriers': [
                {value: 'coal', label: 'coal', class: 'http://openenergy-platform.org/ontology/oeo/OEO_00000088'},
                {value: 'natural gas', label: 'natural gas', class: 'http://openenergy-platform.org/ontology/oeo/OEO_00000292'},
                {value: 'renewable energy carrier', label: 'renewable energy carrier', class: 'http://openenergy-platform.org/ontology/oeo/OEO_00020050'},
                {value: 'biogas', label: 'biogas', class: 'http://openenergy-platform.org/ontology/oeo/OEO_00000074'},
                {value: 'photon', label: 'photon', class: 'http://openenergy-platform.org/ontology/oeo/OEO_00230021'},
              ],
              'frameworks': [{id: "Open Energy Modelling Framework (oemof-solph)", name: "Open Energy Modelling Framework (oemof-solph)"}],
              'models': [{id: "oemof Application Brandenburg Berlin", name: "oemof Application Brandenburg Berlin"}],
           },
          { id: '3', 
            content: 'FST76587',
            'enrgy-transformation-processes': [],
            'descriptors': [],
            'sectors': [],
            'enrgy-carriers': [],
            'models': [],
            'frameworks': [{name: 'YZ'}, {name: 'AB'}],
          }
          ]}/>
    </Box>
  );
};

export default ComparisonBoardMain;
