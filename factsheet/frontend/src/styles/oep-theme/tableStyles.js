import palette from './palette';

const tableStyles = {
  styleOverrides: {
    root: {
      backgroundColor: palette.background.white
    }
  },
  variants: [
    {
      props: { 
        variant: 'light' 
      },
      style: {
        backgroundColor: palette.background.light
      }
    }
  ]
};

export default tableStyles;
