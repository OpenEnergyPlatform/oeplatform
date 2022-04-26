import React from "react";
import { makeStyles } from "@material-ui/core/styles";
import Grid from "@material-ui/core/Grid";

const useStyles = makeStyles(theme => ({
  root: {
    flexGrow: 1,
    backgroundColor: "ffffff"
  }
}));

export default function AutoGrid(props) {
  const classes = useStyles();
  const { topContent, centerContent, buttomContent } = props;
  return (
      <Grid className={classes.root}>
      {centerContent}
      </Grid>
  );
}
