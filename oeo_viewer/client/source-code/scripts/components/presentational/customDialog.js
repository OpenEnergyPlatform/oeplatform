import React from "react";
import Button from "@material-ui/core/Button";
import Dialog from "@material-ui/core/Dialog";
import MuiDialogTitle from "@material-ui/core/DialogTitle";
import MuiDialogContent from "@material-ui/core/DialogContent";
import MuiDialogActions from "@material-ui/core/DialogActions";
import IconButton from "@material-ui/core/IconButton";
import CloseIcon from "@material-ui/icons/Close";
import Typography from "@material-ui/core/Typography";
import AddCircleIcon from '@material-ui/icons/AddCircle';

import {
  createTheme,
  withStyles,
  makeStyles,
  ThemeProvider
} from "@material-ui/core/styles";

import { green, purple } from "@material-ui/core/colors";

const BootstrapButton = withStyles({
  root: {
    boxShadow: "none",
    textTransform: "none",
    fontSize: 16,
    padding: "6px 12px",
    border: "1px solid",
    lineHeight: 1.5,
    backgroundColor: "#00688B",
    borderColor: "#0063cc",
    fontFamily: [
      "-apple-system",
      "BlinkMacSystemFont",
      '"Segoe UI"',
      "Roboto",
      '"Helvetica Neue"',
      "Arial",
      "sans-serif",
      '"Apple Color Emoji"',
      '"Segoe UI Emoji"',
      '"Segoe UI Symbol"'
    ].join(","),
    "&:hover": {
      backgroundColor: "#0069d9",
      borderColor: "#0062cc",
      boxShadow: "none"
    },
    "&:active": {
      boxShadow: "none",
      backgroundColor: "#0062cc",
      borderColor: "#005cbf"
    },
    "&:focus": {
      boxShadow: "0 0 0 0.2rem rgba(0,123,255,.5)"
    },
    color: "white"
  }
})(Button);

const ColorButton = withStyles(theme => ({
  root: {
    color: theme.palette.getContrastText(purple[500]),
    backgroundColor: purple[500],
    "&:hover": {
      backgroundColor: purple[700]
    }
  }
}))(Button);

const useStyles = makeStyles(theme => ({
  margin: {
    margin: theme.spacing(1)
  }
}));

const theme = createTheme({
  palette: {
    primary: green
  }
});

const styles = theme => ({
  root: {
    margin: 0,
    padding: theme.spacing(2)
  },
  closeButton: {
    position: "absolute",
    right: theme.spacing(1),
    top: theme.spacing(1),
    color: theme.palette.grey[500]
  }
});

const DialogTitle = withStyles(styles)(props => {
  const { children, classes, onClose, ...other } = props;
  return (
    <MuiDialogTitle disableTypography className={classes.root} {...other}>
      <Typography variant="h6">{children}</Typography>
      {onClose ? (
        <IconButton
          aria-label="close"
          className={classes.closeButton}
          onClick={onClose}
        >
          <CloseIcon />
        </IconButton>
      ) : null}
    </MuiDialogTitle>
  );
});

const DialogContent = withStyles(theme => ({
  root: {
    padding: theme.spacing(2)
  }
}))(MuiDialogContent);

const DialogActions = withStyles(theme => ({
  root: {
    margin: 0,
    padding: theme.spacing(1)
  }
}))(MuiDialogActions);

export default function CustomizedDialogs(props) {
  const { handleDialogOpen, handleDialogClose, open, content } = props;
  const classes = useStyles();
  return (
    <div>
      <Dialog
        onClose={handleDialogClose}
        aria-labelledby="customized-dialog-title"
        open={open}
      >
        <DialogTitle id="customized-dialog-title" onClose={handleDialogClose}>
          Annotate data
        </DialogTitle>
        <DialogContent dividers>
          <Typography gutterBottom>{content.id}</Typography>
        </DialogContent>
        <DialogContent dividers>
          <Typography gutterBottom>{content.description}</Typography>
        </DialogContent>
        <DialogContent dividers>
          <Typography gutterBottom>1- Choose a database schema</Typography>
        </DialogContent>
        <DialogContent dividers>
          <Typography gutterBottom>2- Choose a column</Typography>
        </DialogContent>
        <DialogActions>
          <BootstrapButton
            variant="contained"
            color="primary"
            disableRipple
            className={classes.margin}
            startIcon={<AddCircleIcon />}
          >
            Add
          </BootstrapButton>
        </DialogActions>
      </Dialog>
    </div>
  );
}
