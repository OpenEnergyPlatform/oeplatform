import * as React from 'react';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import SchemaIcon from '@mui/icons-material/Schema';
import ListAltIcon from '@mui/icons-material/ListAlt';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import FactCheckOutlinedIcon from '@mui/icons-material/FactCheckOutlined';
import Tooltip from '@mui/material/Tooltip';
import { Route, Routes, Link } from 'react-router-dom';
import DiamondIcon from '@mui/icons-material/Diamond';

import Button from '@mui/material/Button';
import ButtonGroup from '@mui/material/ButtonGroup';

export default function ColorToggleButton(props) {

  const handleChange = (event, mode) => {
    props.handleSwap(mode);
  };

  return (
    <div style={{ 'marginLeft': '10px', 'display':'flex' }}>
      <Tooltip title="Back to main page!">
        <Link to={`sirop/`} onClick={() => this.forceUpdate}>
          <Button variant="outlined" size="small" style={{ 'height': '43px', 'textTransform': 'none', 'marginTop': '10px', 'marginRight': '5px', 'zIndex': '1000' }}>
            <ArrowBackIcon />
          </Button>
        </Link>  
      </Tooltip>
      <ButtonGroup variant="contained" aria-label="outlined primary button group" style={{ 'height': '43px', 'textTransform': 'none', 'marginTop': '10px', 'marginRight': '5px', 'zIndex': '1000' }}>
        <Tooltip title="Overview!">
          <Button size="small" name="overview"  onClick={(e) => handleChange(e, 'overview')} > <FactCheckOutlinedIcon /> </Button>
        </Tooltip>
        <Tooltip title="Edit!">
          <Button size="small" value="wizard"  onClick={(e) => handleChange(e, 'edit')} > <ListAltIcon /> </Button>
        </Tooltip>
        {/* <Tooltip title="Similar factsheets!">
          <Button size="small" value="playground" > <DiamondIcon /> </Button>
        </Tooltip> */}
      </ButtonGroup>
    </div>
  );
}
