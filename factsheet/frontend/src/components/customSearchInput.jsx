// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/* eslint-disable no-use-before-define */
import React from 'react';
import TextField from '@mui/core/TextField';
import Autocomplete, { createFilterOptions } from '@mui/material/Autocomplete';
import SearchIcon from "@mui/icons/Search";
import InputAdornment from "@mui/core/InputAdornment";

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
        <TextField style={{ 'marginLeft' : '10px', 'margiBottom' : '10px', 'width': '100%' }}
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
