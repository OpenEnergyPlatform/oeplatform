/* eslint-disable no-use-before-define */
import React from 'react';
import TextField from '@material-ui/core/TextField';
import Autocomplete, { createFilterOptions } from '@material-ui/lab/Autocomplete';
import GraphData from "../../../statics/oeo_info.json";

const filter = createFilterOptions();

export default function CustomSearchInput(props) {
  const [value, setValue] = React.useState(null);
  const searchHandler = props.searchHandler;

  return (
    <Autocomplete
      value={value}
      onChange={(event, newValue) => {
        searchHandler(newValue.id);
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

        // Suggest the creation of a new value
        // if (params.inputValue !== '') {
        //   filtered.push({
        //     inputValue: params.inputValue,
        //     title: `Add "${params.inputValue}"`,
        //   });
        // }

        return filtered;
      }}
      selectOnFocus
      clearOnBlur
      handleHomeEndKeys
      id="free-solo-with-text-demo"
      options={oeo_classes_info}
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
      style={{ width: "95%" }}
      freeSolo
      renderInput={(params) => (
        <TextField {...params} label="Search for OEO classes..." variant="outlined" size="small" />
      )}
    />
  );
}

const oeo_classes_info = GraphData.nodes;
