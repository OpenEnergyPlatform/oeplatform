import React, { useState, useEffect } from 'react';
import Checkbox from '@mui/material/Checkbox';
import TextField from '@mui/material/TextField';
import Autocomplete from '@mui/material/Autocomplete';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import { withStyles } from "@material-ui/core/styles";
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import Tooltip, { TooltipProps, tooltipClasses } from '@mui/material/Tooltip';
import { styled } from '@mui/material/styles';
const icon = <CheckBoxOutlineBlankIcon fontSize="small" />;
const checkedIcon = <CheckBoxIcon fontSize="small" />;

export default function CustomAutocomplete(parameters) {
  const { manyItems, idx, name, showSelectedElements } = parameters;
  const [value, setValue] = useState(parameters.selectedElements !== undefined ? parameters.selectedElements : []);
  const params = parameters.optionsSet;
  const handler = parameters.handler;

  const onDelete = (name) => () => {
    const newValue = value.filter((v) => v.name !== name);
    setValue(newValue);
  };

  const handleChange = (e, newValue) => {
    setValue(newValue);
    handler(newValue, name, idx);
  }

  const HtmlTooltip = styled(({ className, ...props }: TooltipProps) => (
    <Tooltip {...props} classes={{ popper: className }} />
  ))(({ theme }) => ({
    [`& .${tooltipClasses.tooltip}`]: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      color: 'white',
      maxWidth: 520,
      fontSize: theme.typography.pxToRem(20),
      border: '1px solid black',
      padding: '20px'
    },
  }));

  return (
    <Box style={{ width: '90%', marginTop: manyItems ? '20px' :'10px', }}>
      <Autocomplete
        multiple
        id="checkboxes-tags-demo"
        options={params}
        disableCloseOnSelect
        getOptionLabel={(option) => option.name}
        renderOption={(props, option, { selected }) => (
          <li {...props}>
            <Checkbox
              icon={icon}
              checkedIcon={checkedIcon}
              style={{ marginRight: 8 }}
              checked={ selected }
            />
            <HtmlTooltip
            style={{ marginRight: '5px' }}
            placement="top"
            title={
              <React.Fragment>
              <Typography color="inherit" variant="caption">
                Description of <b>{option.name}</b> : TDB ...
              <br />
              <a href={2}>More info from Open Enrgy Knowledge Graph (OEKG)...</a>
              </Typography>
              </React.Fragment>
            }
            >
            <HelpOutlineIcon sx={{ color: '#bdbdbd' }}/>
            </HtmlTooltip>
            {option.name}
          </li>
        )}
        value={value}
        onChange={handleChange}
        renderTags={() => null}
        isOptionEqualToValue={(option, value) => option.name === value.name}
        renderInput={(params) => (
          <TextField {...params} label={parameters.kind} placeholder="" />
        )}
      />
      {showSelectedElements && <Box
        mt={3}
        sx={{
          'marginTop': '10px',
          'overflow': 'auto',
          'height': manyItems ? '100px' :'40px',
          'marginBottom': '20px',
          border: '1px dashed #cecece',
          padding: '20px',
          overflow: 'scroll',
          borderRadius: '5px',
           backgroundColor:'#FCFCFC'
        }}
      >
        {value.map((v) => (
          <Chip key={v.id} label={v.name}  variant="outlined" sx={{ 'marginBottom': '2px', 'marginTop': '10px', 'marginLeft': '5px' }}/>
        ))}
      </Box>}
    </Box>
  );
}
