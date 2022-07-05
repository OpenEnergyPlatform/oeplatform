import React from "react";
import {
  fade,
  withStyles,
  makeStyles,
  createMuiTheme
} from "@material-ui/core/styles";
import { ThemeProvider } from "@material-ui/styles";
import InputLabel from "@material-ui/core/InputLabel";
import TextField from "@material-ui/core/TextField";

import { getColors } from "../../utils";

const CssTextField = withStyles({
  root: {
    "& label.Mui-focused": {
      color: getColors("borders")
    },
    "& .MuiOutlinedInput-root": {
      "& fieldset": {
        borderColor: getColors("borders")
      },
      "&:hover fieldset": {
        borderColor: "#26c6da"
      },
      "&.Mui-focused fieldset": {
        borderColor: getColors("borders")
      }
    }
  }
})(TextField);

const useStyles = makeStyles(theme => ({
  root: {
    padding: "5px"
  },
  input: {
    color: getColors("text")
  },
  floatingLabelFocusStyle: {
    color: getColors("text")
  }
}));

export default function CustomizedInputs(props) {
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <CssTextField
        variant="outlined"
        label={props.label}
        type={props.type}
        autoComplete="off"
        id={props.id}
        onChange={props.onChange}
        InputProps={{
          className: classes.input
        }}
        InputLabelProps={{
          className: classes.floatingLabelFocusStyle
        }}
      />
    </div>
  );
}
