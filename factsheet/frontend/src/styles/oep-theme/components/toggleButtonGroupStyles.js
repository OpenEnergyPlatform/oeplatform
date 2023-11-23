import palette from '../palette';
import variables from '../variables';

const toggleButtonGroupStyles = {
  styleOverrides: {
    grouped: {
      height: '32px',
      width: '6rem',
      '& svg': {
        marginRight: variables.spacing[1]
      }
    }
  }
};

export default toggleButtonGroupStyles;

