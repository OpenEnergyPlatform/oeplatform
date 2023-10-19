import { styled, TableCell } from '@mui/material';
import palette from '../palette';
import variables from '../variables';

export const tableContainerStyles = {
  styleOverrides: {
    root: {
      border: `1px solid ${palette.border}`,
      borderRadius: variables.borderRadius,
      marginBottom: variables.spacing[4]
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
    },
    {
      props: { 
        variant: 'border' 
      },
      style: {
        borderBottom: `1px solid ${palette.border}`
      }
    }
  ]
};

export const ContentTableCell = styled(TableCell)(({ theme }) => ({
  ...theme.components.MuiTableCell.variants.find(v => v.props.variant === 'border').style,
  padding: `${variables.spacing[3]} ${variables.spacing[4]}`
}));

export const FirstRowTableCell = styled(TableCell)(({ theme }) => ({
  ...theme.components.MuiTableCell.variants.find(v => v.props.variant === 'light').style,
  ...theme.components.MuiTableCell.variants.find(v => v.props.variant === 'border').style,
  padding: `${variables.spacing[3]} ${variables.spacing[4]}`,
  fontWeight: theme.typography.fontWeightBold,
  '& > div': {
    'display': 'flex',
    'flex-direction': 'row',
    'align-items': 'center'
  },
  '& > div > span': {
    'padding-right': variables.spacing[2],
    'white-space': 'nowrap'
  }
}));