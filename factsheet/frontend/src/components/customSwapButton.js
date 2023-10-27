import * as React from 'react';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import SchemaIcon from '@mui/icons-material/Schema';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import RemoveRedEyeOutlinedIcon from '@mui/icons-material/RemoveRedEyeOutlined';
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
    <div style={{ 'display':'flex' }}>
      <Tooltip title="Back to main page">
        <Link to={`sirop/`} onClick={() => this.forceUpdate}>
          <Button variant="outlined" size="small" sx={{ mr: 1 }}>
            <ArrowBackIcon />
          </Button>
        </Link>  
      </Tooltip>
      <ButtonGroup variant="contained" aria-label="outlined primary button group" sx={{ mr: 1 }}>
        <Tooltip title="Overview">
          <Button size="small" name="overview"  onClick={(e) => handleChange(e, 'overview')} > <RemoveRedEyeOutlinedIcon sx={{ mr: 1 }} /> <span>View</span></Button>
        </Tooltip>
        <Tooltip title="Edit">
          <Button size="small" value="wizard"  onClick={(e) => handleChange(e, 'edit')} > <EditOutlinedIcon sx={{ mr: 1 }} /> <span>Edit</span> </Button>
        </Tooltip>
        {/* <Tooltip title="Similar factsheets!">
          <Button size="small" value="playground" > <DiamondIcon /> </Button>
        </Tooltip> */}
      </ButtonGroup>
    </div>
  );
}
