// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useState } from 'react';
import Button from '@mui/material/Button';
import ButtonGroup from '@mui/material/ButtonGroup';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import RemoveRedEyeOutlinedIcon from '@mui/icons-material/RemoveRedEyeOutlined';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import Tooltip from '@mui/material/Tooltip';
import { Link } from 'react-router-dom';


import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';


const ColorToggleButton = ({ handleSwap, canEdit, isOwnerLoading }) => {
  const [snackbarOpen, setNotTheOwner] = useState(false);

  const handleChange = (event, mode) => {
    if (mode === "edit" && (isOwnerLoading || !canEdit)) {
      setNotTheOwner(true);
      return;
    }
    handleSwap(mode);
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
          <span>
            <Button size="small" name="overview" disabled={String(window.location.href).split('/').pop() === "new"} onClick={(e) => handleChange(e, 'overview')}>
              <RemoveRedEyeOutlinedIcon sx={{ mr: 1 }} /> <span>View</span>
            </Button>
          </span>
        </Tooltip>
        <Tooltip title="Edit">
          <span>
            <Button
              size="small"
              value="edit"
              disabled={String(window.location.href).split('/').pop() === "new" || isOwnerLoading || !canEdit}
              onClick={(e) => handleChange(e, 'edit')}
            >
              <EditOutlinedIcon sx={{ mr: 1 }} /> <span>Edit</span>
            </Button>
          </span>
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
