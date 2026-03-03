import React from 'react';
import { Alert, AlertTitle, Collapse, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

export default function FilterFeedbackBanner({ open, onClose, type }) {
  let title = '';
  let message = '';

  if (type === 'noFilters') {
    title = 'No filters selected';
    message = 'Showing all available factsheets.';
  } else if (type === 'noResults') {
    title = 'No matches found';
    message = 'No factsheets matched the selected filters.';
  }

  return (
    <Collapse in={open}>
      <Alert
        severity={type === 'noFilters' ? 'info' : 'warning'}
        action={
          <IconButton
            aria-label="close"
            color="inherit"
            size="small"
            onClick={onClose}
          >
            <CloseIcon fontSize="inherit" />
          </IconButton>
        }
        sx={{ mb: 2 }}
      >
        <AlertTitle>{title}</AlertTitle>
        {message}
      </Alert>
    </Collapse>
  );
}
