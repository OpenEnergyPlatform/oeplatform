export const buttonStyles = {
  defaultProps: {
    disableElevation : true
  },
  styleOverrides: {
    root: {
      textTransform: 'capitalize',
      minWidth: 'fit-content'
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