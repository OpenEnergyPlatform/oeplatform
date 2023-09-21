import { createTheme } from '@mui/material/styles';
import palette from './oep-theme/palette';
import buttonStyles from './oep-theme/components/buttonStyles';
import tableStyles from './oep-theme/components/tableStyles';
import toolbarStyles from './oep-theme/components/toolbarStyles';

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
