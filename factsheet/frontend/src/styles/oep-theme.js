import { createTheme } from '@mui/material/styles';
import palette from './oep-theme/palette';
import buttonStyles from './oep-theme/buttonStyles';
import tableStyles from './oep-theme/tableStyles';
import toolbarStyles from './oep-theme/toolbarStyles';

const theme = createTheme({
  palette: palette,
  components: {
    MuiButton: buttonStyles,
    MuiTableCell: tableStyles,
    MuiToolbar: toolbarStyles,
    MuiSvgIcon: {
      defaultProps: {
        fontSize: 'small'
      }
    }
  }
});

export default theme;
