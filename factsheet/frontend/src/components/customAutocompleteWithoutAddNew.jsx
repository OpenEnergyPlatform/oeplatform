// CustomAutocompleteWithoutAddNew.jsx
import React, { useState } from 'react';
import {
  Checkbox,
  TextField,
  Autocomplete,
  Box,
  Chip,
  Typography
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { createFilterOptions } from '@mui/material/Autocomplete';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CheckBoxIcon           from '@mui/icons-material/CheckBox';
import HelpOutlineIcon        from '@mui/icons-material/HelpOutline';
import HtmlTooltip            from '../styles/oep-theme/components/tooltipStyles.jsx';

const filter      = createFilterOptions();
const icon        = <CheckBoxOutlineBlankIcon fontSize="small" />;
const checkedIcon = <CheckBoxIcon fontSize="small" />;

// If you had any custom classes on the TextField input, port them here
const StyledTextField = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    // e.g. padding: theme.spacing(1),
    // backgroundColor: theme.palette.background.paper,
  }
}));

export default function CustomAutocompleteWithoutAddNew({
  optionsSet,
  selectedElements = [],
  kind,
  handler,
  showSelectedElements,
  width = '100%',
  noTooltip = false,
}) {
  const [value, setValue] = useState(selectedElements);

  const handleChange = (_, newValue) => {
    setValue(newValue);
    handler(newValue);
  };

  return (
    <Box sx={{ width }}>
      <Autocomplete
        multiple
        size="small"
        disableCloseOnSelect
        options={optionsSet}
        getOptionLabel={(o) => o.name}
        isOptionEqualToValue={(o, v) => o.name === v.name}
        value={value}
        onChange={handleChange}
        renderTags={() => null}
        filterOptions={(opts, params) => filter(opts, params)}
        renderOption={(props, option, { selected }) => (
          <li {...props}>
            {!option.inputValue && (
              <Checkbox
                icon={icon}
                checkedIcon={checkedIcon}
                sx={{ mr: 1 }}
                checked={selected}
              />
            )}
            {!noTooltip && !option.inputValue && (
              <HtmlTooltip
                placement="top"
                title={
                  <Typography variant="caption" color="inherit">
                    Description of <b>{option.name}</b>: TDB…
                    <br />
                    <a href="#">More info from OEKG…</a>
                  </Typography>
                }
              >
                <HelpOutlineIcon sx={{ color: 'text.secondary', mr: 1 }} />
              </HtmlTooltip>
            )}
            {option.name}
          </li>
        )}
        renderInput={(params) => (
          <StyledTextField
            {...params}
            label={kind}
            variant="outlined"
            placeholder=""
          />
        )}
      />

      {showSelectedElements && (
        <Box
          sx={{
            mt: 1,
            overflow: 'auto',
            borderRadius: 1,
          }}
        >
          {value
            .slice() // copy before sort
            .sort((a, b) => a.name.localeCompare(b.name))
            .map((v) => (
              <Chip
                key={v.id}
                size="small"
                label={v.name}
                variant="outlined"
                sx={{ m: 0.5 }}
              />
            ))}
        </Box>
      )}
    </Box>
  );
}
