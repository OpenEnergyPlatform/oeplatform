import { grey } from "@mui/material/colors";

const palette = {
  primary: {
    lighter: '#E5EFF6',
    light: '#92BEDD',
    main: '#2972A6',
    dark: '#1F567D',
    darker: '#122C3E',
    contrastText: '#FFFFFF',
  },
  error: {
    main: '#e53e3e',
  },
  neutral: {
    main: '#198BB9',
    darker: '#053e85',
    contrastText: '#FFFFFF',
  },
  grey: {
    50: '#FAFDFF',
    100: '#F6F9FB',
    200: '#E3EAEF',
    300: '#C3D1DB',
    400: '#A2B3BE',
    500: '#708696',
    600: '#4B6678',
    700: '#294456',
    800: '#112F44',
    900: '#001C30'
  },
  text: {
    primary: '#294456',
    secondary: '#5F7484'
  },
  divider: '#E3EAEF',
  background: {
    white: '#FFFFFF',
    lighter: grey[100],
    light: grey[200]
  }
}

export default palette;