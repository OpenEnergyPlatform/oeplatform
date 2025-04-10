// SPDX-FileCopyrightText: 2025 Bryan Lancien <bryanlancien.ui@gmail.com>
// SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
//
// SPDX-License-Identifier: MIT

import palette from '../palette';
import variables from '../variables';
import Grid from '@mui/material/Grid';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

export const CardItem = ({ children }) => {
  return (
    <Grid
      item xs={12}
      sx={{
        border: variables.border.light,
        borderRadius: variables.borderRadius,
        mb: variables.spacing[4]
      }}
    >
      {children}
    </Grid>
  )
}

export const CardHeader = ({ children }) => {
  return (
    <div style={{
      backgroundColor: palette.background.lighter,
      borderTopLeftRadius: variables.borderRadius,
      borderTopRightRadius: variables.borderRadius,
      padding: `${variables.spacing[4]} ${variables.spacing[5]}`
    }}>
      <Stack
        direction="row"
        justifyContent="flex-start"
        alignItems="center"
        spacing={2}
        sx={{ minHeight: variables.spacing[4] }}
      >
        {children}
      </Stack>
    </div>
  )
}

export const CardBody = ({ children }) => {
  return (
    <div style={{ padding: `${variables.spacing[3]} ${variables.spacing[5]}` }}>
      {children}
    </div>
  )
}

export const CardRow = ({ rowKey, rowValue }) => {
  return (
    <Stack
      direction="row"
      justifyContent="flex-start"
      alignItems="flex-start"
      sx={{ paddingBottom: variables.spacing[2] }}
    >
      <Typography
        variant="body2"
        sx={{
          fontWeight: variables.fontWeight.bold,
          minWidth: '12rem'
        }}
      >
        {rowKey}
      </Typography>
      <Typography variant="body2">
        {rowValue}
      </Typography>
    </Stack>
  )
}
