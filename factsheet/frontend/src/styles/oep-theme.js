import { createTheme } from '@mui/material/styles';
import palette from './oep-theme/palette';
import buttonStyles from './oep-theme/buttonStyles';
import tableStyles from './oep-theme/tableStyles';

const theme = createTheme({
  palette: palette,
  components: {
    MuiButton: buttonStyles,
    MuiTableCell: tableStyles,
    MuiToolbar: {
      styleOverrides: {
        root: {
          "&.MuiToolbar-root": {
            backgroundColor: palette.background.white
          }
        }
      }
    },
    MuiSvgIcon: {
      defaultProps: {
        fontSize: 'small'
      }
    }
  }
});

export default theme;
