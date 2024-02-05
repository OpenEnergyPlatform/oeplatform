import { createTheme } from '@mui/material/styles';
import palette from './oep-theme/palette';
import { buttonStyles, buttonGroupStyles } from './oep-theme/components/buttonStyles';
import { tableContainerStyles, tableHeaderStyles, tableRowStyles, tableCellStyles } from './oep-theme/components/tableStyles';
import toggleButtonGroupStyles from './oep-theme/components/toggleButtonGroupStyles';
import toolbarStyles from './oep-theme/components/toolbarStyles';
import { typographyVariants, typographyStyles, inputLabelStyles, inputBaseStyles, textareaAutosizeStyles, formGroupStyles } from './oep-theme/components/typographyStyles';

const theme = createTheme({
  breakpoints: {
    values: {
      xs: 0,
      sm: 600,
      md: 900,
      lg: 1200,
      lg2: 1360,
      xl: 1536
    }
  },
  palette: palette,
  typography: typographyVariants,
  components: {
    MuiTypography: typographyStyles,
    MuiInputLabel: inputLabelStyles,
    MuiInputBase: inputBaseStyles,
    MuiTextareaAutosize: textareaAutosizeStyles,
    MuiFormGroup: formGroupStyles,
    MuiButton: buttonStyles,
    MuiButtonGroup: buttonGroupStyles,
    MuiToggleButtonGroup: toggleButtonGroupStyles,
    MuiTableContainer: tableContainerStyles,
    MuiTableHead: tableHeaderStyles,
    MuiTableRow: tableRowStyles,
    MuiTableCell: tableCellStyles,
    MuiToolbar: toolbarStyles,
    MuiSvgIcon: {
      defaultProps: {
        fontSize: 'small'
      }
    }
  }
});

export default theme;
