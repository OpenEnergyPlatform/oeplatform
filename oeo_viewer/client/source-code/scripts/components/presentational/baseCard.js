import React from "react";
import { makeStyles } from "@material-ui/core/styles";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import CardContent from "@material-ui/core/CardContent";
import Typography from "@material-ui/core/Typography";

const useStyles = makeStyles({
  root: {
    borderStyle: "solid",
    borderWidth: "1px",
    backgroundColor: "#f7f7f7",
    borderColor: "#00688B",
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
