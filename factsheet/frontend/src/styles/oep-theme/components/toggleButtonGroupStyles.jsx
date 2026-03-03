// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

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
