import { grey } from "@mui/material/colors";

const primaryPalette = {
  50: '#F6FBFF',
  100: '#E5EFF6',
  200: '#C1D9EB',
  300: '#92BEDD',
  400: '#5295C6',
  500: '#2972A6',
  600: '#236695',
  700: '#1F567D',
  800: '#1E445F',
  900: '#122C3E'
}

const greyPalette = {
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
}

const palette = {
  primary: {
    lighter: primaryPalette[100],
    light: primaryPalette[300],
    main: primaryPalette[500],
    dark: primaryPalette[700],
    darker: primaryPalette[900],
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
  grey: greyPalette,
  text: {
    primary: greyPalette[700],
    secondary: '#5F7484'
  },
  divider: '#E3EAEF',
  background: {
    white: '#FFFFFF',
    lighter: greyPalette[100],
    light: greyPalette[200]
  }
}

export default palette;