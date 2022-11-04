import * as React from 'react';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import SchemaIcon from '@mui/icons-material/Schema';
import ListAltIcon from '@mui/icons-material/ListAlt';
import FactCheckOutlinedIcon from '@mui/icons-material/FactCheckOutlined';
import Tooltip from '@mui/material/Tooltip';

export default function ColorToggleButton(props) {
  const [alignment, setAlignment] = React.useState('web');

  const handleChange = (event, newAlignment) => {
    setAlignment(newAlignment);
    props.handleSwap(newAlignment);
  };

  return (
    <ToggleButtonGroup
      color="primary"
      value={alignment}
      exclusive
      onChange={handleChange}
      size="large"
      style={{ 'marginTop': '10px', 'marginLeft': '10px'}}>
    >
      <Tooltip title="Factsheet">
        <ToggleButton size="small" value="wizard" style={{ 'textTransform': 'none' }}> <ListAltIcon /> </ToggleButton>
      </Tooltip>
      <Tooltip title="Overview">
        <ToggleButton size="small" value="overview" style={{ 'textTransform': 'none' }}> <FactCheckOutlinedIcon /> </ToggleButton>
      </Tooltip>
      {/* <ToggleButton size="small" value="playground" style={{ 'textTransform': 'none' }}> <SchemaIcon /> </ToggleButton> */}
    </ToggleButtonGroup>
  );
}
