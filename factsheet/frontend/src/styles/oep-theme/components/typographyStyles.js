// SPDX-FileCopyrightText: 2025 Bryan Lancien <bryanlancien.ui@gmail.com>
// SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
//
// SPDX-License-Identifier: MIT

import palette from '../palette';
import variables from '../variables';

const fontSizeSmallStyles = {
  fontSize: variables.fontSize.sm,
  color: palette.text.primary
}

const linkStyles = {
  fontWeight: variables.fontWeight.bold,
  cursor: 'pointer',
  color: palette.link
}

export const typographyVariants = {
  body1: {
    fontSize: variables.fontSize.md,
    color: palette.text.primary,
    "& a": linkStyles
  },
  body2: {
    fontSize: variables.fontSize.sm,
    color: palette.text.primary,
    "& a": linkStyles
  },
  link: linkStyles
};

export const typographyStyles = {
  styleOverrides: {
    small: {
      '& .MuiFormControlLabel-label': fontSizeSmallStyles,
      '& label, & span': fontSizeSmallStyles
    },
  },
};

export const inputLabelStyles = {
  styleOverrides: {
    root: fontSizeSmallStyles
  },
};

export const inputBaseStyles = {
  styleOverrides: {
    root: fontSizeSmallStyles
  },
};

export const textareaAutosizeStyles = {
  styleOverrides: {
    root: fontSizeSmallStyles
  },
};

export const formGroupStyles = {
  styleOverrides: {
    root: fontSizeSmallStyles
  },
};
