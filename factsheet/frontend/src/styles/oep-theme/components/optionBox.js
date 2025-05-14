// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien>
//
// SPDX-License-Identifier: MIT

import { styled } from '@mui/material';
import Box from '@mui/material/Box';
import palette from '../palette';
import variables from '../variables';

const OptionBox = styled(Box)(({ theme }) => ({
  backgroundColor: palette.background.lighter,
  color: palette.text.primary,
  padding: variables.spacing[5],
  marginBottom: variables.spacing[5],
  fontSize: variables.fontSize.sm,
  lineHeight: theme.typography.body1.lineHeight,

  '& h2': {
    marginTop: variables.spacing[0],
    fontSize: variables.fontSize.sm,
    fontWeight: theme.typography.fontWeightBold
  },

  '& label': {
    paddingLeft: variables.spacing[2],
  },

  '& label span': {
    padding: variables.spacing[0],
    paddingRight: variables.spacing[1],
    fontSize: variables.fontSize.sm,
    lineHeight: theme.typography.body1.lineHeight,
  }
}));

export default OptionBox;
