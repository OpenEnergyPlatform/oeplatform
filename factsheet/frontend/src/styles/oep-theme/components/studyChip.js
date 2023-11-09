import React from 'react';
import Chip from '@mui/material/Chip';

const StudyChip = ({ index, label, included, color }) => {
  const chipColor = included ? 'success' : 'error';
  const backgroundColor = index === 0 ? 'white' : 'white'; // You can adjust the logic here based on your requirements

  return (
    <Chip
      color={index === 0 ? 'default' : chipColor}
      size='small'
      label={label}
      variant="outlined"
      sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor }}
    />
  );
};

export default StudyChip;