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
    <ButtonGroup variant="contained" aria-label="outlined primary button group" style={{ 'marginLeft': '10px', 'marginTop': '10px' }}>
        <Tooltip title="Factsheet's edit mode!">
          <Button size="small" value="wizard" style={{ 'textTransform': 'none' }} >
            <Link to={`factsheet/`} onClick={() => this.forceUpdate} >
              <ArrowBackIcon  style={{ 'marginTop': '7px' }} > </ArrowBackIcon>
            </Link>  
          </Button>
        </Tooltip>
        <Tooltip title="Overview!">
          <Button size="small" name="overview" style={{ 'textTransform': 'none' }} onClick={(e) => handleChange(e, 'overview')} > <FactCheckOutlinedIcon /> </Button>
        </Tooltip>
        <Tooltip title="Factsheet's edit mode!">
          <Button size="small" value="wizard" style={{ 'textTransform': 'none' }} onClick={(e) => handleChange(e, 'edit')} > <ListAltIcon /> </Button>
        </Tooltip>
        <Tooltip title="Analysis">
          <Button size="small" value="playground" style={{ 'textTransform': 'none' }} > <DiamondIcon /> </Button>
        </Tooltip>
    </ButtonGroup>
  );
}
