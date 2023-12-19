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

const successPalette = {
  50: '#F6FFFC',
  100: '#EBFFF9',
  200: '#BDF8E5',
  300: '#73DDBC',
  400: '#4AC29D',
  500: '#21A179',
  600: '#13825F',
  700: '#09684A',
  800: '#06543B',
  900: '#013D2A'
}

const errorPalette = {
  50: '#FFF6F8',
  100: '#FFEBED',
  200: '#FAC7CD',
  300: '#F09EA9',
  400: '#E5707F',
  500: '#CD4759',
  600: '#AB2134',
  700: '#860E1E',
  800: '#640B17',
  900: '#3E0109'
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
  success: {
    lighter: successPalette[100],
    light: successPalette[300],
    main: successPalette[600],
    dark: successPalette[700],
    darker: successPalette[900],
  },
  error: {
    lighter: errorPalette[100],
    light: errorPalette[300],
    main: errorPalette[600],
    dark: errorPalette[700],
    darker: errorPalette[900],
  },
  neutral: {
    main: '#198BB9',
    darker: '#053e85',
    contrastText: '#FFFFFF',
  },
  grey: greyPalette,
  text: {
    primary: greyPalette[700],
    secondary: '#5F7484',
    link: primaryPalette[700]
  },
  link: primaryPalette[500],
  divider: '#E3EAEF',
  border: greyPalette[300],
  background: {
    white: '#FFFFFF',
    lighter: greyPalette[100],
    light: greyPalette[200],
    highlight: primaryPalette[500]
  }
}

export default palette;