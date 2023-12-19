import React from "react";
import { makeStyles } from "@material-ui/core/styles";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";

const useStyles = makeStyles({
  root: {
    borderStyle: "solid",
    borderWidth: "1px",
    backgroundColor: "#f7f7f7",
    borderColor: "#00688B",
    overflow: "auto",
    height:'84vh',
    maxHeight: '82vh',
  }
});

export default function SimpleCard(props) {
  const { content } = props;
  const classes = useStyles();

  return (
      <Card className={classes.root}>
        <CardContent>
          {content}
        </CardContent>
      </Card>
  );
}
