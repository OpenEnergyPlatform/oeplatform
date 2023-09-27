import palette from '../palette';

export const tableStyles = {
  styleOverrides: {
    root: {
      border: `1px solid ${palette.border}`
    }
  }
};

export const tableHeaderStyles = {
  styleOverrides: {
    root: {
      borderBottom: `1px solid ${palette.border}`
    }
  }
};

export const tableRowStyles = {
  styleOverrides: {
    root: {
      "&:not(:last-child)": {
        borderBottom: `1px solid ${palette.border}`
      }
    }
  }
};

export const tableCellStyles = {
  styleOverrides: {
    root: {
      backgroundColor: palette.background.white,
      border: 'none'
    },
    body: {
      paddingTop: 0,
      paddingBottom: 0
    }
  },
  variants: [
    {
      props: { 
        variant: 'light' 
      },
      style: {
        backgroundColor: palette.background.lighter
      }
    }
  ]
};