/* eslint-disable no-use-before-define */
import React from 'react';
import TextField from '@material-ui/core/TextField';
import Autocomplete, { createFilterOptions } from '@material-ui/lab/Autocomplete';
import SearchIcon from "@material-ui/icons/Search";
import InputAdornment from "@material-ui/core/InputAdornment";

const filter = createFilterOptions();

export default function CustomSearchInput(props) {
  const [value, setValue] = React.useState(null);
  const {searchHandler, data} = props;
  return (
    <Autocomplete
      style={{ 'margin': '10px' }}
      value={value}
      onChange={(event, newValue) => {
        searchHandler(newValue.name);
        if (typeof newValue === 'string') {
          setValue({
            name: newValue,
          });
        } else if (newValue && newValue.inputValue) {
          // Create a new value from the user input
          setValue({
            name: newValue.inputValue,
          });
        } else {
          setValue(newValue);
        }
      }}
      filterOptions={(options, params) => {
        const filtered = filter(options, params);
        return filtered;
      }}
      selectOnFocus
      clearOnBlur
      handleHomeEndKeys
      id="free-solo-with-text-demo"
      options={data}
      getOptionLabel={(option) => {
        // Value selected with enter, right from the input
        if (typeof option === 'string') {
          return option;
        }
        // Add "xxx" option created dynamically
        if (option.inputValue) {
          return option.inputValue;
        }
        // Regular option
        return option.name;
      }}
      renderOption={(option) => option.name}
      freeSolo
      renderInput={(params) => (
        <TextField style={{ 'marginLeft' : '10px', 'margiBottom' : '10px', 'width': '100%', 'zIndex': '1000', 
                           }}
                   color="primary"
                   {...params}
                   label="Search..."
                   variant="outlined"
                   size="small"
        InputProps={{
            ...params.InputProps,
            style: {
                      fontWeight: 600,
                    },
            endAdornment: (
              <InputAdornment position="end">
                <SearchIcon />
              </InputAdornment>
            )
          }}

        />
      )}

    />
  );
}
