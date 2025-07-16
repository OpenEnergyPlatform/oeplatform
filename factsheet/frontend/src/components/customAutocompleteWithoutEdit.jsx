import React, { useState } from 'react';
import {
  Box,
  Chip,
  Typography,
  TextField,
  Checkbox,
  Autocomplete,
  Dialog,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button
} from '@mui/material';
import { styled, useTheme } from '@mui/material/styles';
import {
  createFilterOptions
} from '@mui/material/Autocomplete';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CheckBoxIcon           from '@mui/icons-material/CheckBox';
import HelpOutlineIcon        from '@mui/icons-material/HelpOutline';
import HtmlTooltip            from '../styles/oep-theme/components/tooltipStyles';
import uuid                   from 'react-uuid';

import FactsheetMetadataList  from './scenarioBundleUtilityComponents/factsheetMetadataList.jsx';
import handleOpenURL          from './scenarioBundleUtilityComponents/handleOnClickTableIRI.jsx';

const filter      = createFilterOptions();
const icon        = <CheckBoxOutlineBlankIcon fontSize="small" />;
const checkedIcon = <CheckBoxIcon fontSize="small" />;

// Optional: if you had a lot of Input styles, you can extract them here.
// Otherwise you can inline everything via the `sx` prop below.
const StyledTextField = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    // for example, if your old `inputRoot` was:
    // padding: theme.spacing(1),
    // backgroundColor: theme.palette.background.paper,
    // you’d place it here.
  }
}));

function stripInvalidProps(props) {
  const {
    fullwidth,
    textColor,
    indicator,
    selectionFollowsFocus,
    ...safeProps
  } = props;
  return safeProps;
}

export default function CustomAutocompleteWithoutEdit(props) {
  const {
    manyItems,
    type,
    showSelectedElements,
    addNewHandler,
    editHandler,
    handler,
    width,
    bgColor,
    optionsSet,
    selectedElements,
    kind
  } = props;

  const [value, setValue]     = useState(selectedElements ?? []);
  const [open, toggleOpen]    = useState(false);
  const [openEdit, toggleOpenEdit] = useState(false);
  const [dialogValue, setDialogValue] = useState({ id: '', name: '' });
  const [editLabel, setEditLabel]     = useState('');
  const [editIRI, setEditIRI]         = useState('');
  const [updatedLabel, setUpdatedLabel] = useState('');

  const theme = useTheme();

  const handleChange = (e, newValue) => {
    if (newValue.length && newValue[newValue.length - 1].inputValue) {
      const iv = newValue[newValue.length - 1].inputValue;
      setDialogValue({ id: iv, name: iv });
      toggleOpen(true);
    } else {
      setValue(newValue);
      handler(newValue);
    }
  };

  const onDelete = (name) => () => {
    const filtered = value.filter((v) => v.name !== name);
    setValue(filtered);
  };

  const handleAddNew = () => {
    const base = value.filter((i) => !i.inputValue);
    const newItem = { iri: uuid(), id: dialogValue.id, name: dialogValue.name };
    const updated = [...base, newItem];
    setValue(updated);
    addNewHandler(newItem);
    handler(updated);
    toggleOpen(false);
  };

  const handleEdit = () => {
    editHandler(editLabel, updatedLabel, editIRI);
    const updated = value.map((v) =>
      v.id === editLabel ? { ...v, id: updatedLabel, name: updatedLabel } : v
    );
    setValue(updated);
    toggleOpenEdit(false);
    setUpdatedLabel('');
  };

  return (
    <Box
      sx={{
        width: width,
        backgroundColor: bgColor ?? '#FCFCFC',
        mt: 0,
        mb: 2,
      }}
    >
      <Autocomplete
        multiple
        size="small"
        disableCloseOnSelect
        options={optionsSet}
        getOptionLabel={(o) =>
          typeof o === 'string' ? o : o?.name || o?.acronym || o?.id || ''
        }
        isOptionEqualToValue={(o, v) => o.name === v.name}
        value={value}
        onChange={handleChange}
        renderTags={() => null}
        filterOptions={(opts, params) => filter(opts, params)}
        renderOption={(props, option, { selected }) => {
          const { key, ...safeProps } = stripInvalidProps(props);
          return (
            <li key={key} {...safeProps}>
              {!option.inputValue && (
                <Checkbox
                  icon={icon}
                  checkedIcon={checkedIcon}
                  sx={{ mr: 1 }}
                  checked={selected}
                />
              )}
              {!option.inputValue && (
                <HtmlTooltip
                  placement="top"
                  title={
                    <Typography variant="caption" color="inherit">
                      <FactsheetMetadataList data={option} />
                      <br />
                      <a href={option.url}>More info …</a>
                    </Typography>
                  }
                >
                  <HelpOutlineIcon sx={{ color: 'text.secondary', mr: 1 }} />
                </HtmlTooltip>
              )}
              {option.name}
            </li>
          );
        }}

        renderInput={(params) => (
          <StyledTextField
            {...params}
            label={kind}
            variant="outlined"
            placeholder=""
          />
        )}
      />

      {/* “Add new” dialog */}
      <Dialog open={open} onClose={() => toggleOpen(false)}>
        <DialogContent>
          <DialogContentText sx={{ my: 2 }}>
            You are about to add <b><i>{dialogValue.name}</i></b> as a new <b><i>{type}</i></b> in OEKG
          </DialogContentText>
          <TextField
            fullwidth
            size="small"
            variant="standard"
            label="Label"
            value={dialogValue.name}
            onChange={(e) =>
              setDialogValue({ id: e.target.value, name: e.target.value })
            }
            sx={{ mt: 2 }}
          />
          {/* …other optional fields… */}
        </DialogContent>
        <DialogActions>
          <Button size="small" onClick={() => toggleOpen(false)}>
            Cancel
          </Button>
          <Button size="small" variant="contained" onClick={handleAddNew}>
            Add
          </Button>
        </DialogActions>
      </Dialog>

      {/* “Edit” dialog */}
      <Dialog open={openEdit} onClose={() => toggleOpenEdit(false)}>
        <DialogContent>
          <DialogContentText sx={{ my: 2 }}>
            You are about to edit <b><i>{editLabel}</i></b> as a new <b><i>{type}</i></b> in OEKG
          </DialogContentText>
          <TextField
            fullwidth
            size="small"
            variant="standard"
            label="New label"
            value={updatedLabel}
            onChange={(e) => setUpdatedLabel(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button size="small" onClick={() => toggleOpenEdit(false)}>
            Cancel
          </Button>
          <Button size="small" variant="contained" onClick={handleEdit}>
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {showSelectedElements && (
        <Box
          sx={{
            mt: 1,
            overflow: 'auto',
            borderRadius: 1,
          }}
        >
          {value.map((v) => (
            <Chip
              key={v.id}
              size="small"
              label={v.acronym ?? v.name}
              variant="outlined"
              sx={{ m: 0.5 }}
              onClick={() => handleOpenURL(v.url)}
            />
          ))}
        </Box>
      )}
    </Box>
  );
}
