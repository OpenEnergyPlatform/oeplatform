import { createTheme } from '@mui/material/styles';
import palette from './oep-theme/palette';
import buttonStyles from './oep-theme/buttonStyles';

const theme = createTheme({
  components: {
    MuiButton: buttonStyles,
    MuiSvgIcon: {
      defaultProps: {
        fontSize: 'small'
      }
    }
  },
  palette: palette
});

export default theme;
