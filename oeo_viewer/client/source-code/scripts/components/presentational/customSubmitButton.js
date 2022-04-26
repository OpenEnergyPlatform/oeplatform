import React, { Component } from "react";
import "babel-polyfill";
import { styled } from "@material-ui/styles";
import Button from "@material-ui/core/Button";
import {
  fade,
  withStyles,
  makeStyles,
  createMuiTheme
} from "@material-ui/core/styles";



export default function CustomButton(props) {
  const classes = useStyles();
  const { caption, type } = props;
  return (
    <div className={classes.root}>
      <Button className={classes.button} type={type}>
        {caption}
      </Button>
    </div>
  );
}
