import palette from '../palette';

const toolbarStyles = {
  styleOverrides: {
    root: {
      "&.MuiToolbar-root": {
        backgroundColor: palette.background.white,
        borderBottom: `1px solid ${palette.divider}`,
        padding: 0,

        "& > .MuiGrid-container": {
          padding: '0 0 1rem',

          "& > .MuiGrid-item:nth-of-type(1)": {
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'flex-start'
          },

          "& > .MuiGrid-item:nth-of-type(2)": {
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'center'
          },

          "& > .MuiGrid-item:nth-of-type(3)": {
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'flex-end'
          }
        }
      }
    }
  }
}

export default toolbarStyles;
