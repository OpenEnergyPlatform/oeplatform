import variables from '../variables';

export const buttonStyles = {
  defaultProps: {
    disableElevation : true
  },
  styleOverrides: {
    root: {
      textTransform: 'capitalize',
      minWidth: 'fit-content',
      fontSize: variables.fontSize.sm
    }
  }
}

export const buttonGroupStyles = {
  styleOverrides: {
    root: {
      "&.MuiButtonGroup-root": {
        boxShadow: 'none'
      }
    }
  }
}
