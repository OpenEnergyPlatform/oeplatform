import { createTheme } from '@mui/material/styles'
import palette from './oep-theme/palette';

// component style fragments you already wrote:
// each one should export an object with `styleOverrides`, `defaultProps` or `variants`
import {
  buttonStyles,
  buttonGroupStyles,
} from './oep-theme/components/buttonStyles';

import toggleButtonGroupStyles from './oep-theme/components/toggleButtonGroupStyles'
import toolbarStyles from './oep-theme/components/toolbarStyles'

import {
  tableContainerStyles,
  tableHeaderStyles,
  tableRowStyles,
  tableCellStyles,
} from './oep-theme/components/tableStyles'

import {
  typographyVariants,
  typographyStyles,
  inputLabelStyles,
  inputBaseStyles,
  textareaAutosizeStyles,
  formGroupStyles,
} from './oep-theme/components/typographyStyles'

const theme = createTheme({
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1200,
      lg2: 1360,
      xl: 1536,
    },
  },

  palette,

  // this is exactly like your old `typography: typographyVariants`
  typography: typographyVariants,

  components: {
    // If you need to add global Box defaults
    MuiBox: {
      styleOverrides: {
        root: {
          // e.g. clean reset, custom display, etc.
        },
      },
    },

    // typography + form elements
    MuiTypography: typographyStyles,
    MuiInputLabel: inputLabelStyles,
    MuiInputBase: inputBaseStyles,
    MuiTextareaAutosize: textareaAutosizeStyles,
    MuiFormGroup: formGroupStyles,

    // buttons
    MuiButton: buttonStyles,
    MuiButtonGroup: buttonGroupStyles,
    MuiToggleButtonGroup: toggleButtonGroupStyles,

    // tables
    MuiTableContainer: tableContainerStyles,
    MuiTableHead:      tableHeaderStyles,
    MuiTableRow:       tableRowStyles,
    MuiTableCell:      tableCellStyles,

    // toolbar, icons, etc.
    MuiToolbar: toolbarStyles,

    // set small icon by default
    MuiSvgIcon: {
      defaultProps: { fontSize: 'small' },
    },
  },
})

export default theme
