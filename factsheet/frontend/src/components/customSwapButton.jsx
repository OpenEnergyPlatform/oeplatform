import React, { useState, useEffect } from 'react';
import Button from '@mui/material/Button';
import ButtonGroup from '@mui/material/ButtonGroup';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import RemoveRedEyeOutlinedIcon from '@mui/icons-material/RemoveRedEyeOutlined';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import Tooltip from '@mui/material/Tooltip';
import { Link } from 'react-router-dom';
import axios from 'axios';

import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import CSRFToken from './csrfToken';

import conf from "../conf.json";

const ColorToggleButton = (props) => {
  const [isOwner, setIsOwner] = useState(false);
  const [snackbarOpen, setNotTheOwner] = useState(false);

  const param_2 = String(window.location.href).split('/')[5];

  useEffect(() => {
    // Replace 'bundle_id' with the actual ID of the ScenarioBundle you want to check
    const bundleId = param_2; // Assuming you pass the uid as a prop
    // Make the API call to check if the user is the owner
    axios.post(conf.toep + `scenario-bundles/check-owner/${bundleId}/`,
      {
        uid: bundleId
      },
      {
        headers: { 'X-CSRFToken': CSRFToken() }
      })
      .then(response => {
        // Assuming the response.data contains the ownership information
        setIsOwner(response.data.isOwner);
      })
      .catch(error => {
        console.error('Error checking ownership:', error);
        // Handle errors if needed
      });
  }, [param_2]); // Dependency array includes props.uid to re-run the effect when it changes

  const handleChange = (event, mode) => {
    // Only allow the 'edit' action if the user is the owner
    if (mode === 'edit' && !isOwner) {
      setNotTheOwner(true);
      return;
    }

    props.handleSwap(mode);
  };


  const handleNotTheOwnerClose = (event, reason) => {
    if (reason === 'clickaway') {
      return;
    }
    setNotTheOwner(false);
  };

  return (
    <div style={{ 'display': 'flex' }}>
      <Tooltip title="Back to main page">
        <Link to={`scenario-bundles/main`} onClick={() => this.forceUpdate}>
          <Button variant="outlined" size="small" sx={{ mr: 1 }}>
            <ArrowBackIcon />
          </Button>
        </Link>
      </Tooltip>
      <ButtonGroup variant="contained" aria-label="outlined primary button group" sx={{ mr: 1 }}>
        <Tooltip title="Overview">
          <Button size="small" name="overview" disabled={String(window.location.href).split('/').pop() === "new"} onClick={(e) => handleChange(e, 'overview')}>
            <RemoveRedEyeOutlinedIcon sx={{ mr: 1 }} /> <span>View</span>
          </Button>
        </Tooltip>
        <Tooltip title="Edit">
          <Button
            size="small"
            value="edit"
            disabled={String(window.location.href).split('/').pop() === "new" | !isOwner}
            onClick={(e) => handleChange(e, 'edit')}
          >
            <EditOutlinedIcon sx={{ mr: 1 }} /> <span>Edit</span>
          </Button>
        </Tooltip>
        {/* <Tooltip title="Similar factsheets!">
          <Button size="small" value="playground" > <DiamondIcon /> </Button>
        </Tooltip> */}
      </ButtonGroup>

      {/* Snackbar component */}
      <Snackbar open={snackbarOpen} autoHideDuration={10000} onClose={handleNotTheOwnerClose}>
        <Alert variant="filled" severity="error" sx={{ width: '100%' }}>
          <AlertTitle>Access denied!</AlertTitle>
          You cannot edit scenario bundles that you do not own!
        </Alert>
      </Snackbar>
    </div>
  );
};

export default ColorToggleButton;
