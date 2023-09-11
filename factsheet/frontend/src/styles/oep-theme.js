import { createTheme } from '@mui/material/styles';

const oepTheme = createTheme({
  status: {
    danger: '#e53e3e',
  },
  palette: {
    primary: {
      lighter: '#E5EFF6',
      light: '#92BEDD',
      main: '#2972A6',
      dark: '#1F567D',
      darker: '#122C3E',
      contrastText: '#fff',
    },
    neutral: {
      main: '#198BB9',
      darker: '#053e85',
      contrastText: '#fff',
    },
  },
});

export default oepTheme;
