import palette from './palette';

const toolbarStyles = {
  styleOverrides: {
    root: {
      "&.MuiToolbar-root": {
        backgroundColor: palette.background.white,
        borderBottom: `1px solid ${palette.divider}`
      }
    }
  }
}

export default toolbarStyles;