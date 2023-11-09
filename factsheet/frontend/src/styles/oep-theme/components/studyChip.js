import React from 'react';
import Chip from '@mui/material/Chip';
import palette from '../palette';
import variables from '../variables';

const StudyChip = ({ index, label, included }) => {
  const chipColor = included ? 'success' : 'error';
  const backgroundColor = index === 0 ? palette.background.white : palette.background.white;

  return (
    <Chip
      color={index === 0 ? 'default' : chipColor}
      size='small'
      label={label}
      variant="outlined"
      sx={{ 'marginBottom': variables.spacing[2], 'marginTop': variables.spacing[2], 'marginLeft': variables.spacing[2], backgroundColor, fontSize: variables.fontSize.sm }}
    />
  );
};

export default StudyChip;