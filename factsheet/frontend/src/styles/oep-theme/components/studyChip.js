import React from 'react';
import Chip from '@mui/material/Chip';
import palette from '../palette';
import variables from '../variables';

const StudyChip = ({ index, label, included, onClick }) => {
  const chipColor = included ? 'success' : 'error';
  const backgroundColor = index === 0 ? palette.background.white : chipColor === 'success' ? palette.success.lighter : palette.error.lighter;

  return (
    <Chip
      color={index === 0 ? 'default' : chipColor}
      size='small'
      label={label}
      variant="outlined"
      sx={{
        marginBottom: variables.spacing[1],
        marginTop: variables.spacing[1],
        marginRight: variables.spacing[1],
        backgroundColor,
        fontSize: variables.fontSize.sm
      }}
      onClick={onClick}
    />
  );
};

export default StudyChip;
