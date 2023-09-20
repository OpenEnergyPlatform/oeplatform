import { createTheme } from '@mui/material/styles';
import palette from './oep-theme/palette';
import buttonStyles from './oep-theme/buttonStyles';

const theme = createTheme({
  palette: palette,
  components: {
    MuiButton: buttonStyles,
    MuiToolbar: {
      styleOverrides: {
        root: {
          "&.MuiToolbar-root": {
            backgroundColor: '#FFF'
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
