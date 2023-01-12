import React, { useState, useEffect } from 'react';
import Checkbox from '@mui/material/Checkbox';
import TextField from '@mui/material/TextField';
import Autocomplete from '@mui/material/Autocomplete';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import { withStyles } from "@material-ui/core/styles";
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';

const icon = <CheckBoxOutlineBlankIcon fontSize="small" />;
const checkedIcon = <CheckBoxIcon fontSize="small" />;

export default function CustomAutocomplete(parameters) {
  const { manyItems, idx, name } = parameters;
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
      <Box
        mt={3}
        sx={{
          'marginTop': '10px',
          'overflow': 'auto',
          'height': manyItems ? '80px' :'40px',
          'marginBottom': '20px',
          border: '1px dashed #cecece',
          padding: '20px',
          overflow: 'scroll',
          borderRadius: '5px'
        }}
      >
        {value.map((v) => (
          <Chip key={v.id} label={v.name}  variant="outlined" sx={{ 'marginBottom': '2px', 'marginTop': '10px', 'marginLeft': '5px' }}/>
        ))}
      </Box>
    </Box>
  );
}
