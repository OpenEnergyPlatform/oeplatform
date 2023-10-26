import { createTheme } from '@mui/material/styles';
import palette from './oep-theme/palette';
import buttonStyles from './oep-theme/components/buttonStyles';
import { tableContainerStyles, tableHeaderStyles, tableRowStyles, tableCellStyles } from './oep-theme/components/tableStyles';
import toolbarStyles from './oep-theme/components/toolbarStyles';
import variables from './oep-theme/variables';

const theme = createTheme({
  palette: palette,
  typography: {
    small: {
      fontSize: variables.fontSize.sm,
      color: palette.text.primary,
    },
  },
  components: {
    MuiTypography: {
      styleOverrides: {
        small: {
          '& .MuiFormControlLabel-label': {
            fontSize: variables.fontSize.sm,
            color: palette.text.primary,
          },
          '& label, & span': {
            fontSize: variables.fontSize.sm,
            color: palette.text.primary,
          },
        },
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: {
          fontSize: variables.fontSize.sm,
          color: palette.text.primary,
        },
      },
    },
    MuiInputBase: {
      styleOverrides: {
        input: {
          fontSize: variables.fontSize.sm,
          color: palette.text.primary
        },
      },
    },
    MuiTextareaAutosize: {
      styleOverrides: {
        root: {
          fontSize: variables.fontSize.sm,
          color: palette.text.primary,
        },
      },
    },
    MuiFormGroup: {
      styleOverrides: {
        '& label span': {
          fontSize: variables.fontSize.sm
        }
      } 
    },
    MuiButton: buttonStyles,
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
