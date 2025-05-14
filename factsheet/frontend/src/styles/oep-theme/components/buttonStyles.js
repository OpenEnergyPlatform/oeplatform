// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien>
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
//
// SPDX-License-Identifier: MIT

import variables from '../variables';

export const buttonStyles = {
  defaultProps: {
    disableElevation : true
  },
  styleOverrides: {
    root: {
      textTransform: 'capitalize',
      minWidth: 'fit-content',
      fontSize: variables.fontSize.sm
    }
  }
}

export const buttonGroupStyles = {
  styleOverrides: {
    root: {
      "&.MuiButtonGroup-root": {
        boxShadow: 'none'
      }
    }
  }
}
