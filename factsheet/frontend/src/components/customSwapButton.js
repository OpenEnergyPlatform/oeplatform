import * as React from 'react';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import SchemaIcon from '@mui/icons-material/Schema';
import ListAltIcon from '@mui/icons-material/ListAlt';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import FactCheckOutlinedIcon from '@mui/icons-material/FactCheckOutlined';
import Tooltip from '@mui/material/Tooltip';
import { Route, Routes, Link } from 'react-router-dom';

export default function ColorToggleButton(props) {
  const [alignment, setAlignment] = React.useState('web');

  const handleChange = (event, newAlignment) => {
    setAlignment(newAlignment);
    props.handleSwap(newAlignment);
  };

  return (
    <ToggleButtonGroup
      value={alignment}
      onChange={handleChange}
      exclusive
      style={{ 'marginTop': '10px', 'marginLeft': '10px'}}>
    >
      <Tooltip title="Back to main factsheet page!">
        <Link to={`factsheet/`} onClick={() => this.forceUpdate} style={{ textDecoration: 'none', marginRight:'5px' }}  >
          <ToggleButton color="primary" variant="contained" size="small" value="wizard" style={{ 'textTransform': 'none' }}> <ArrowBackIcon /> </ToggleButton>
        </Link>
      </Tooltip>
      <Tooltip title="Factsheet's edit mode!">
        <ToggleButton size="small" value="wizard" style={{ 'textTransform': 'none' }}> <ListAltIcon /> </ToggleButton>
      </Tooltip>
      <Tooltip title="Overview!">
        <ToggleButton size="small" value="overview" style={{ 'textTransform': 'none' }}> <FactCheckOutlinedIcon /> </ToggleButton>
      </Tooltip>
      {/* <ToggleButton size="small" value="playground" style={{ 'textTransform': 'none' }}> <SchemaIcon /> </ToggleButton> */}
    </ToggleButtonGroup>
  );
}
