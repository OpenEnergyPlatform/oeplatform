import palette from '../palette';
import variables from '../variables';

const toggleButtonGroupStyles = {
  styleOverrides: {
    grouped: {
      height: variables.buttonHeight.small,
      width: '6rem',
      '& svg': {
        marginRight: variables.spacing[1]
      }
    }
  }
};

export default toggleButtonGroupStyles;
