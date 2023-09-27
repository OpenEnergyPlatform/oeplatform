import { createTheme } from '@mui/material/styles';
import palette from './oep-theme/palette';
import buttonStyles from './oep-theme/components/buttonStyles';
import { tableStyles, tableHeaderStyles, tableRowStyles, tableCellStyles } from './oep-theme/components/tableStyles';
import toolbarStyles from './oep-theme/components/toolbarStyles';
import shape from '@material-ui/core/styles/shape';

const theme = createTheme({
  palette: palette,
  components: {
    MuiButton: buttonStyles,
    MuiTable: tableStyles,
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
