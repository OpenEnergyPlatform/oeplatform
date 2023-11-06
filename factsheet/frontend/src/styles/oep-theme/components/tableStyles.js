import palette from '../palette';
import variables from '../variables';

export const tableContainerStyles = {
  styleOverrides: {
    root: {
      border: `1px solid ${palette.border}`,
      borderRadius: variables.borderRadius
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