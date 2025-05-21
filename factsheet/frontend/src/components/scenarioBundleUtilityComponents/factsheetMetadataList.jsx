import React from 'react';
import { Box, Typography, List, ListItem, ListItemText } from '@mui/material';

const FactsheetMetadataList = ({ data }) => {
  if (!data || typeof data !== 'object') {
    return null; // or return a fallback <Typography>Unknown factsheet</Typography>
  }

  const name = data.name ?? 'Unnamed factsheet';
  const acronym = data.acronym ?? 'N/A';
  const license = data.license ?? 'unspecified';
  const institutions = Array.isArray(data.institutions) ? data.institutions : [];

  return (
    <Box>
      <Typography variant="h6">
        The factsheet {name} with the acronym <b>{acronym}</b> is licensed as <b>{license}</b> and maintained by the following institution(s):
      </Typography>
      <List>
        {institutions.length > 0 ? (
          institutions.map((institution, index) => (
            <ListItem key={index}>
              <ListItemText primary={institution} />
            </ListItem>
          ))
        ) : (
          <ListItem>
            <ListItemText primary="No institutions available." />
          </ListItem>
        )}
      </List>
    </Box>
  );
};

export default FactsheetMetadataList;
