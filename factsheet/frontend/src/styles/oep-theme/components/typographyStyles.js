import palette from '../palette';
import variables from '../variables';

const fontSizeSmallStyles = {
  fontSize: variables.fontSize.sm,
  color: palette.text.primary
}

export const typographyVariants = {
  body2: {
    fontSize: variables.fontSize.sm,
    color: palette.text.primary,
  },
  link: {
    fontWeight: variables.fontWeight.bold,
    cursor: 'pointer',
    color: palette.link
  }
};

export const typographyStyles = {
  styleOverrides: {
    small: {
      '& .MuiFormControlLabel-label': fontSizeSmallStyles,
      '& label, & span': fontSizeSmallStyles
    },
  },
};

export const inputLabelStyles = {
  styleOverrides: {
    root: fontSizeSmallStyles
  },
};

export const inputBaseStyles = {
  styleOverrides: {
    root: fontSizeSmallStyles
  },
};

export const textareaAutosizeStyles = {
  styleOverrides: {
    root: fontSizeSmallStyles
  },
};

export const formGroupStyles = {
  styleOverrides: {
    root: fontSizeSmallStyles
  },
};