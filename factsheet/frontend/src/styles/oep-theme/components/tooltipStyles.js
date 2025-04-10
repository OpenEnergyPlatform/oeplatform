// SPDX-FileCopyrightText: 2025 Bryan Lancien <bryanlancien.ui@gmail.com>
// SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
//
// SPDX-License-Identifier: MIT

import React from 'react';
import { styled, Tooltip, tooltipClasses } from '@mui/material';
import { TooltipProps } from '@mui/material/Tooltip';
import palette from '../palette';
import variables from '../variables';

const HtmlTooltip = styled(({ className, ...props }: TooltipProps) => (
  <Tooltip {...props} classes={{ popper: className }} />
))(({ theme }) => ({
  [`& .${tooltipClasses.tooltip}`]: {
      backgroundColor: palette.background.lighter,
      color: palette.text.primary,
      maxWidth: 520,
      border: `1px solid ${palette.border}`,
      padding: variables.spacing[3]
    },
    [`& .${tooltipClasses.tooltip}, & .${tooltipClasses.tooltip} *`]: {
      fontSize: variables.fontSize.sm,
      lineHeight: theme.typography.body1.lineHeight
    }
}));

export default HtmlTooltip;
