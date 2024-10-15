import React from 'react';
import { Box, Typography, List, ListItem, ListItemText } from '@mui/material';

const FactsheetMetadataList = ({ data }) => {
  return (
    <Box>
      <Typography variant="h6">The factsheet {data.name} with the acronym <b>{data.acronym}</b> is licensed as <b>{data.license}</b> and maintained by the following institution(s):</Typography>
      <List>
        {data.institutions.length > 0 ? (
          data.institutions.map((institution, index) => (
            <ListItem key={index}>
              <ListItemText
                primary={institution}
              />
            </ListItem>
          ))
        ) : (
          <ListItem>
            <ListItemText
              primary="No institutions available."
            />
          </ListItem>
        )}
      </List>
    </Box>
  );
};

export default FactsheetMetadataList;
