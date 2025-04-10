// SPDX-FileCopyrightText: 2025 Bryan Lancien <bryanlancien.ui@gmail.com>
// SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
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
