import palette from '../palette';

export const tableStyles = {
  styleOverrides: {
    root: {
      borderWidth: '1px',
      borderStyle: 'solid',
      borderColor: palette.border,
      borderRadius: '4px'
    }
  }
};

export const tableHeaderStyles = {
  styleOverrides: {
    root: {
      borderTopLeftRadius: '4px',
      borderTopRightRadius: '4px'
    }
  }
};

export const tableRowStyles = {
  styleOverrides: {
    root: {
      borderBottomWidth: '1px',
      borderBottomStyle: 'solid',
      borderBottomColor: palette.border
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