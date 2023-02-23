import React, { useState, useEffect } from 'react';
import Checkbox from '@mui/material/Checkbox';
import TextField from '@mui/material/TextField';
import Autocomplete, { createFilterOptions } from '@mui/material/Autocomplete';
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
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Snackbar, { SnackbarOrigin } from '@mui/material/Snackbar';

const filter = createFilterOptions();
const icon = <CheckBoxOutlineBlankIcon fontSize="small" />;
const checkedIcon = <CheckBoxIcon fontSize="small" />;

export default function CustomAutocomplete(parameters) {
  const { manyItems, idx, name, type, showSelectedElements, addNewHandler } = parameters;
  const [value, setValue] = useState(parameters.selectedElements !== undefined ? parameters.selectedElements : []);
  const params = parameters.optionsSet;
  const handler = parameters.handler;
  const [open, toggleOpen] = React.useState(false);

  const [dialogValue, setDialogValue] = React.useState({
    id: '',
    name: '',
  });
  const theme = useTheme();

 
  const onDelete = (name) => () => {
    const newValue = value.filter((v) => v.name !== name);
    setValue(newValue);
  };

  const handleClose = () => {
    setDialogValue({
      id: '',
      name: '',
    });
    toggleOpen(false);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    setValue({
      id: dialogValue.id,
      name: parseInt(dialogValue.name, 10),
    });
    handleClose();
  };

  const handleChange = (e, newValue) => {
    if (newValue.length !== 0 && newValue[newValue.length - 1].inputValue) {
      toggleOpen(true);
      setDialogValue({
        id: newValue[newValue.length - 1].inputValue,
        name: newValue[newValue.length - 1].inputValue,
      });
    } else {
      setValue(newValue);
    }
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

  const handleName = e => {
    setDialogValue({
      id: e.target.value,
      name: e.target.value,
    });
  };

  const handleAddNew = e => {
    addNewHandler(dialogValue);
    toggleOpen(false);
  };
  
  return (
    <Box style={{ width: '90%', marginTop: manyItems ? '20px' :'10px', }}>
      <Autocomplete
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
            {!option.inputValue && <HtmlTooltip
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
          <TextField {...params} label={parameters.kind} placeholder="" />
        )}
        filterOptions={(options, params) => {
          const filtered = filter(options, params);

          if (params.inputValue !== '') {
            filtered.push({
              inputValue: params.inputValue,
              name: `Add "${params.inputValue}"`,
            });
          }
          return filtered;
        }}
      />
      <Dialog open={open} onClose={handleClose}  >
        <form onSubmit={handleSubmit}>
          <DialogTitle>Add a new entity to Open Energy Knowledge Graph (OEKG)</DialogTitle>
          <DialogContent>
            <DialogContentText sx={{
              'marginTop': '20px',
              'marginBottom': '20px',
              }}>
              You are about to add <b><i>{dialogValue.name}</i></b> as a new <b><i>{type}</i></b> 
            </DialogContentText>
            <TextField
             sx={{
              'marginTop': '20px',
              }}
              id="name"
              value={dialogValue.name}
              onChange={handleName}
              label="Name"
              fullWidth
            />
            <TextField
             sx={{
              'marginTop': '20px',
              }}
              label={'URL (Optional)'}
              fullWidth
            />
            <TextField
              sx={{
                'marginTop': '20px',
              }}
              multiline
              rows={4}
              maxRows={8}
              label={'Short description (Optional)'}
              fullWidth
            />
          </DialogContent>
          <DialogActions>
            <Button variant="contained" onClick={handleClose}>Cancel</Button>
            <Button variant="contained" onClick={handleAddNew}>Add</Button>
          </DialogActions>
        </form>
      </Dialog>
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
