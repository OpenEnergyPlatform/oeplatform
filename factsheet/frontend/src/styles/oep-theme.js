import { createTheme } from '@mui/material/styles';
import palette from './oep-theme/palette';
import { buttonStyles, buttonGroupStyles } from './oep-theme/components/buttonStyles';
import { tableContainerStyles, tableHeaderStyles, tableRowStyles, tableCellStyles } from './oep-theme/components/tableStyles';
import toolbarStyles from './oep-theme/components/toolbarStyles';
import { typographyStyles, inputLabelStyles, inputBaseStyles, textareaAutosizeStyles, formGroupStyles } from './oep-theme/components/typographyStyles';
import variables from './oep-theme/variables';

const theme = createTheme({
  breakpoints: {
    values: {
      xl: 1360,
      xxl: 1536
    }
  },
  palette: palette,
  typography: {
    small: {
      fontSize: variables.fontSize.sm,
      color: palette.text.primary,
    },
  },
  components: {
    MuiTypography: typographyStyles,
    MuiInputLabel: inputLabelStyles,
    MuiInputBase: inputBaseStyles,
    MuiTextareaAutosize: textareaAutosizeStyles,
    MuiFormGroup: formGroupStyles,
    MuiButton: buttonStyles,
    MuiButtonGroup: buttonGroupStyles,
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
