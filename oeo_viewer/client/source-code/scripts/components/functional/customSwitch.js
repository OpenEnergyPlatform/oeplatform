import React from 'react';
import { withStyles } from '@material-ui/core/styles';
import { purple } from '@material-ui/core/colors';
import FormGroup from '@material-ui/core/FormGroup';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import Switch from '@material-ui/core/Switch';
import Grid from '@material-ui/core/Grid';
import Typography from '@material-ui/core/Typography';

const IOSSwitch = withStyles((theme) => ({
  root: {
    width: 42,
    height: 28,
    padding: 0,
    marginTop: 12,
    marginLeft: 20,
  },
  switchBase: {
    padding: 1,
    '&$checked': {
      transform: 'translateX(15px)',
      color: theme.palette.common.white,
      '& + $track': {
        backgroundColor: '#1f567d',
        opacity: 1,
        border: 'none',
      },
    },
    '&$focusVisible $thumb': {
      color: '#1f567d',
      border: '8px solid #fff',
    },
  },
  thumb: {
    width: 24,
    height: 24,
  },
  track: {
    borderRadius: 26 / 2,
    border: `1px solid ${theme.palette.grey[400]}`,
    backgroundColor: theme.palette.grey[50],
    opacity: 1,
    transition: theme.transitions.create(['background-color', 'border']),
  },
  checked: {},
  focusVisible: {},
}))(({ classes, ...props }) => {
  return (
    <Switch
      focusVisibleClassName={classes.focusVisible}
      disableRipple
      classes={{
        root: classes.root,
        switchBase: classes.switchBase,
        thumb: classes.thumb,
        track: classes.track,
        checked: classes.checked,
      }}
      {...props}
    />
  );
});

export default function CustomSwitch(props) {

  const { toggleRenderMode } = props;

  const [state, setState] = React.useState({
    checkedA: true,
    checkedB: true,
    checkedC: true,
  });

  const handleChange = (event) => {
    setState({ ...state, [event.target.name]: event.target.checked });
    toggleRenderMode();
  };

  return (
    <FormGroup style={{ alignItems: "end" }}>
      <FormControlLabel
        control={
          <IOSSwitch
          checked={state.checkedB}
          onChange={handleChange}
          name="checkedB"
          />}
        label=""
      />
    </FormGroup>
  );
}
