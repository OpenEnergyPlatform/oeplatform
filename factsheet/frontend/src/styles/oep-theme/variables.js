// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: MIT

import palette from "./palette";

const variables = {
  borderRadius: '4px',
  border: {
    'light': `1px solid ${palette.border}`
  },
  buttonHeight: {
    'small': '32px'
  },
  fontSize: {
    'xs': '0.75rem',
    'sm': '0.875rem',
    'md': '1rem',
    'lg': '1.25rem',
    'xl': '1.5rem',
    'xl1': '2rem'
  },
  fontWeight: {
    'light': 300,
    'normal': 400,
    'bold': 700
  },
  lineHeight: {
    'sm': '1.25rem',
  },
  spacing: {
    0: '0',
    1: '0.25rem',
    2: '0.5rem',
    3: '0.75rem',
    4: '1rem',
    5: '1.5rem',
    6: '2rem',
    7: '2.5rem',
    8: '3rem',
    9: '4rem'
  }
}

export default variables;
