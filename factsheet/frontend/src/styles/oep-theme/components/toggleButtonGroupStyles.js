// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien>
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
//
// SPDX-License-Identifier: MIT

import palette from '../palette';
import variables from '../variables';

const toggleButtonGroupStyles = {
  styleOverrides: {
    grouped: {
      height: variables.buttonHeight.small,
      width: '6rem',
      '& svg': {
        marginRight: variables.spacing[1]
      }
    }
  }
};

export default toggleButtonGroupStyles;
