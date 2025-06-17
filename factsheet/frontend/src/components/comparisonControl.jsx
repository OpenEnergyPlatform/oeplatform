// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: MIT

import React, { useState } from 'react';
// import ComparisonBoardItem from "./comparisonBoardItems";
import Box from '@mui/material/Box';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControl from '@mui/material/FormControl';
import FormLabel from '@mui/material/FormLabel';

const ComparisonControl = (props) => {
  const { items } = props;

  return (
    <Box sx={{
      width: '97%',
      height: '10%',
      padding: '20px',
      marginLeft: '40px',
      marginRight: '40px',
      backgroundColor: '#4372a41a',
      border: '1px solid',
      borderRadius: '4px',
      display: 'block',

     }}>
        <FormControl>
            <FormLabel id="demo-row-radio-buttons-group-label">Please select the aspect for the comaprison</FormLabel>
            <RadioGroup
                row
                aria-labelledby="demo-row-radio-buttons-group-label"
                name="row-radio-buttons-group"
            >
                <FormControlLabel value="2" control={<Radio />} label="Cost-effectiveness" />
                <FormControlLabel value="3" control={<Radio />} label="Environmental friendiness" />
                <FormControlLabel value="1" control={<Radio />} label="Renewability" />
                <FormControlLabel value="4" control={<Radio />} label="Storage efficiency" />
                <FormControlLabel value="5" control={<Radio />} label="Intensivity of emission" />
                <FormControlLabel value="6" control={<Radio />} label="Conversion Efficiency" />
            </RadioGroup>
        </FormControl>
    </Box>
  );
};

export default ComparisonControl;
