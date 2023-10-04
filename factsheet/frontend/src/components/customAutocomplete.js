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
import EditIcon from '@mui/icons-material/Edit';
import uuid from "react-uuid";
import { makeStyles } from '@material-ui/core/styles';

const filter = createFilterOptions();
const icon = <CheckBoxOutlineBlankIcon fontSize="small" />;
const checkedIcon = <CheckBoxIcon fontSize="small" />;

const useStyles = makeStyles((theme) => ({
  inputRoot: {
    borderRadius: 0, // Set border radius to 0 for sharp edges
  },
}));

export default function CustomAutocomplete(parameters) {
  const { manyItems, idx, name, type, showSelectedElements, addNewHandler, editHandler, handler, width, bgColor } = parameters;
  const [value, setValue] = useState(parameters.selectedElements !== undefined ? parameters.selectedElements : []);
  const [open, toggleOpen] = React.useState(false);
  const [openEdit, toggleOpenEdit] = React.useState(false);
  const [editLabel, setEditLabel] = React.useState('');
  const [editIRI, setEditIRI] = React.useState('');
  const [updatedLabel, setUpdatedLabel] = React.useState('');

  const classes = useStyles();
  
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
    const updauedVlue = value.filter(item => item.name !== dialogValue.name);
    setValue(updauedVlue);
    toggleOpen(false);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
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
      handler(newValue);
    }
  }

  const handleDelete = (e, vc, vi) => {
    setUpdatedLabel(editLabel);
    setEditIRI(vi);
    setEditLabel(vc);
    toggleOpenEdit(true);
  };

  const handleCloseEdit = () => {
    toggleOpenEdit(false);
  };

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

  const handleUpdatedLabel = e => {
    setUpdatedLabel(e.target.value);
  };
  
  const handleAddNew = e => {
    const updauedValue = value.filter(item => (!item.hasOwnProperty('inputValue')) );
    const updatedDialogeValue = { "iri": uuid(), "id": dialogValue.id, "name": dialogValue.id };
    updauedValue.push(updatedDialogeValue);
    setValue(updauedValue);
    addNewHandler(updatedDialogeValue);
    toggleOpen(false);
    handler(updauedValue);
  };

  
  const handleEdit = e => {
    editHandler(editLabel, updatedLabel, editIRI);
    setUpdatedLabel('');
    toggleOpenEdit(false);
    const objIndex = value.findIndex((obj => obj.id == editLabel));
    value[objIndex].id = updatedLabel;
    value[objIndex].name = updatedLabel;
  }


  return (
    <Box style={{ width: width,  backgroundColor: bgColor !== undefined ? bgColor : '#FCFCFC', marginTop: '5px', }}>
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
          <TextField  {...params } label={parameters.kind} placeholder="" variant="outlined" InputProps={{
            ...params.InputProps,
            classes: {
              root: classes.inputRoot, // Apply the custom CSS class
            },
          }}/>
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
          <DialogContent>
            <DialogContentText sx={{
              'marginTop': '20px',
              'marginBottom': '20px',
              }}>
              You are about to add <b><i>{dialogValue.name}</i></b> as a new <b><i>{type}</i> </b> in Open Energy Knowledge Graph (OEKG)
            </DialogContentText>
            <TextField
              size="small"
              variant='standard'
              sx={{
                'marginTop': '20px',
                }}
                id="name"
                value={dialogValue.name}
                onChange={handleName}
                label="Label"
                fullWidth
            />
            <TextField
              size="small"
              variant='standard'
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
              size="small"
              variant='standard'
              multiline
              rows={1}
              maxRows={4}
              label={'Short description (Optional)'}
              fullWidth
            />
          </DialogContent>
          <DialogActions>
            <Button size="small" variant="contained" onClick={handleClose}>Cancel</Button>
            <Button size="small" variant="contained" onClick={handleAddNew}>Add</Button>
          </DialogActions>
        </form>
      </Dialog>
      <Dialog open={openEdit} onClose={handleCloseEdit}  >
        <DialogContent>
          <DialogContentText sx={{
            'marginTop': '20px',
            'marginBottom': '20px',
            }}>
            You are about to edit <b><i>{editLabel}</i></b> as a new <b><i>{type}</i></b>  in Open Energy Knowledge Graph (OEKG)
          </DialogContentText>
          <TextField
            sx={{
            'marginTop': '20px',
            }}
            size="small"
            variant='standard'
            id="name"
            value={updatedLabel}
            onChange={handleUpdatedLabel}
            label="New label"
            fullWidth
          />
          <TextField
            sx={{
            'marginTop': '20px',
            }}
            size="small"
            variant='standard'
            label={'URL (Optional)'}
            fullWidth
          />
          <TextField
            sx={{
              'marginTop': '20px',
            }}
            multiline
            size="small"
            variant='standard'
            rows={1}
            maxRows={4}
            label={'Short description (Optional)'}
            fullWidth
          />
        </DialogContent>
        <DialogActions>
          <Button size="small" variant="contained" onClick={handleCloseEdit}>Cancel</Button>
          <Button size="small" variant="contained" onClick={handleEdit}>Save</Button>
        </DialogActions>
      </Dialog>
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
          <Chip size='small' key={v.id}  label={v.name} deleteIcon={<EditIcon />}  onDelete={(e) => handleDelete(e, v.name, v.iri) } variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px' }}/>
        ))}
      </Box>}
    </Box>
  );
  
}
