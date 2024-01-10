import palette from '../palette';
import variables from '../variables';

const toolbarStyles = {
  styleOverrides: {
    root: {
      "&.MuiToolbar-root": {
        backgroundColor: palette.background.white,
        borderBottom: `1px solid ${palette.divider}`,
        padding: `${variables.spacing[4]} ${variables.spacing[0]} ${variables.spacing[0]}`,

        "& > .MuiGrid-container": {
          "& > .MuiGrid-item:nth-of-type(1)": {
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'flex-start',
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
        },
        "& .MuiButton-root": {
          height: variables.buttonHeight.small
        }
      }
    }
  }
}

export default toolbarStyles;

