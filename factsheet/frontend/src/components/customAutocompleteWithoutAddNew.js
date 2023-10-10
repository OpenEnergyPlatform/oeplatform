import React, { useState } from 'react';
import Checkbox from '@mui/material/Checkbox';
import TextField from '@mui/material/TextField';
import Autocomplete, { createFilterOptions } from '@mui/material/Autocomplete';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import Typography from '@mui/material/Typography';
import Tooltip, { TooltipProps, tooltipClasses } from '@mui/material/Tooltip';
import { styled } from '@mui/material/styles';
import { makeStyles } from '@material-ui/core/styles';

const filter = createFilterOptions();
const icon = <CheckBoxOutlineBlankIcon fontSize="small" />;
const checkedIcon = <CheckBoxIcon fontSize="small" />;

const useStyles = makeStyles((theme) => ({
  inputRoot: {
    borderRadius: 0,  
  },
}));

export default function CustomAutocompleteWithoutAddNew(parameters) {
  const { manyItems, idx, name, type, showSelectedElements, handler, width, noTooltip=false } = parameters;
  const [value, setValue] = useState(parameters.selectedElements !== undefined ? parameters.selectedElements : []);
  const classes = useStyles();

  const handleChange = (e, newValue) => {
    setValue(newValue);
    handler(newValue);
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
    <Box style={{ width: width,  marginTop: '10px', }}>
      <Autocomplete
        size="small" 
        multiple
        id="checkboxes-tags-demo"
        options={parameters.optionsSet}
        disableCloseOnSelect
        getOptionLabel={(option) => option.name}
        renderOption={(props, option, { selected }) => (
          <li {...props}>
             {!option.inputValue &&<Checkbox
              icon={icon}
              checkedIcon={checkedIcon}
              style={{ marginRight: 8 }}
              checked={ selected }
            />}
            {!noTooltip && !option.inputValue && <HtmlTooltip
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
            </HtmlTooltip>}
            {option.name}
          </li>
        )}
        value={value}
        onChange={handleChange}
        renderTags={() => null}
        isOptionEqualToValue={(option, value) => option.name === value.name}
        renderInput={(params) => (
          <TextField {...params} label={parameters.kind} placeholder="" variant="outlined" InputProps={{
            ...params.InputProps,
            classes: {
              root: classes.inputRoot, // Apply the custom CSS class
            },
          }}/>
        )}
      />
      {showSelectedElements && <Box
        mt={3}
        sx={{
          'marginTop': '10px',
          'overflow': 'auto',
          'height': '100%',
          // 'border': '1px dashed #cecece',
          'overflow': 'scroll',
          'borderRadius': '5px',
          // 'backgroundColor':'#FCFCFC'
        }}
      >
        {value.map((v) => (
          <Chip size='small' key={v.id}  label={v.name} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px' }}/>
        ))}
      </Box>}
    </Box>
  );
  
}
