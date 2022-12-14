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
  const { manyItems, idx } = parameters;
  console.log(parameters.selectedElements);
  console.log(parameters.selectedElements);
  const [value, setValue] = useState(parameters.selectedElements !== undefined ? parameters.selectedElements : []);
  const params = parameters.optionsSet;
  const handler = parameters.handler;
  const onDelete = (id) => () => {
    setValue((value) => value.filter((v) => v.id !== id));
  };

  useEffect(()=>{
    handler(value, idx);
  })

  return (
    <Box style={{ width: '90%', marginTop: manyItems ? '20px' :'10px', }}>
      <Autocomplete
        multiple
        id="checkboxes-tags-demo"
        options={params}
        disableCloseOnSelect
        getOptionLabel={(option) => option.id}
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
        onChange={(e, newValue) => (setValue(newValue))}
        renderTags={() => null}
        isOptionEqualToValue={(option, value) => option.id === value.id}
        renderInput={(params) => (
          <TextField {...params} label={parameters.kind} placeholder="Sectors" />
        )}
      />
      <Box
        mt={3}
        sx={{
          'marginTop': '10px',
          'overflow': 'auto',
          'height': manyItems ? '80px' :'40px',
          'marginBottom': '20px',
          '& > :not(:last-child)': { marginRight: 1 },
          '& > *': { marginBottom: 1 },
          border: '1px solid #cecece',
          padding: '20px',
          overflow: 'scroll',
        }}
      >
        {value.map((v) => (
          <Chip key={v.id} label={v.id} onDelete={onDelete(v.id)} variant="outlined" sx={{ 'marginBottom': '2px' }}/>
        ))}
      </Box>
    </Box>
  );
}
