// CustomAutocomplete.jsx
import React, { useState } from 'react';
import {
  Checkbox,
  TextField,
  Autocomplete,
  Box,
  Chip,
  Dialog,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { createFilterOptions } from '@mui/material/Autocomplete';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CheckBoxIcon           from '@mui/icons-material/CheckBox';
import uuid                   from 'react-uuid';

const filter      = createFilterOptions();
const icon        = <CheckBoxOutlineBlankIcon fontSize="small" />;
const checkedIcon = <CheckBoxIcon fontSize="small" />;

// If you had custom Input styles via `classes.inputRoot`, port them in here:
const StyledTextField = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    // e.g. padding: theme.spacing(1),
    // backgroundColor: theme.palette.background.paper,
  }
}));

export default function CustomAutocomplete({
  optionsSet,
  selectedElements = [],
  kind,
  type,
  addNewHandler,
  editHandler,
  handler,
  showSelectedElements,
  width = '100%',
  bgColor = '#FCFCFC',
}) {
  const [value, setValue]         = useState(selectedElements);
  const [open, toggleOpen]        = useState(false);
  const [openEdit, toggleOpenEdit]= useState(false);
  const [dialogValue, setDialogValue] = useState({ id: '', name: '' });
  const [editLabel, setEditLabel]     = useState('');
  const [editIRI, setEditIRI]         = useState('');
  const [updatedLabel, setUpdatedLabel] = useState('');

  const handleChange = (_, newVal) => {
    if (newVal.length && newVal[newVal.length - 1].inputValue) {
      const iv = newVal[newVal.length - 1].inputValue;
      setDialogValue({ id: iv, name: iv });
      toggleOpen(true);
    } else {
      setValue(newVal);
      handler(newVal);
    }
  };

  const handleAddNew = () => {
    const base = value.filter(i => !i.inputValue);
    const newItem = { iri: uuid(), id: dialogValue.id, name: dialogValue.name };
    const updated = [...base, newItem];
    setValue(updated);
    addNewHandler(newItem);
    handler(updated);
    toggleOpen(false);
  };

  const handleEdit = () => {
    editHandler(editLabel, updatedLabel, editIRI);
    const updated = value.map(v =>
      v.id === editLabel ? { ...v, id: updatedLabel, name: updatedLabel } : v
    );
    setValue(updated);
    toggleOpenEdit(false);
    setUpdatedLabel('');
  };

  return (
    <Box
      sx={{
        width,
        backgroundColor: bgColor,
        mb: 2,
      }}
    >
      <Autocomplete
        multiple
        size="small"
        disableCloseOnSelect
        options={optionsSet}
        getOptionLabel={o => o.name}
        isOptionEqualToValue={(o, v) => o.name === v.name}
        value={value}
        onChange={handleChange}
        renderTags={() => null}
        filterOptions={(opts, params) => {
          const filtered = filter(opts, params);
          if (params.inputValue) {
            filtered.push({
              inputValue: params.inputValue,
              name: `Add "${params.inputValue}"`,
            });
          }
          return filtered;
        }}
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
            {option.name}
          </li>
        )}
        renderInput={params => (
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
            You’re about to add <b><i>{dialogValue.name}</i></b> as a new <b><i>{type}</i></b>.
          </DialogContentText>
          <TextField
            fullWidth
            size="small"
            variant="standard"
            label="Label"
            value={dialogValue.name}
            onChange={e =>
              setDialogValue({ id: e.target.value, name: e.target.value })
            }
            sx={{ mt: 2 }}
          />
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
            You’re about to edit <b><i>{editLabel}</i></b> as a new <b><i>{type}</i></b>.
          </DialogContentText>
          <TextField
            fullWidth
            size="small"
            variant="standard"
            label="New label"
            value={updatedLabel}
            onChange={e => setUpdatedLabel(e.target.value)}
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
          {value.map(v => (
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
