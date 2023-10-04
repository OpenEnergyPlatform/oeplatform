import React from "react";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import CardContent from "@material-ui/core/CardContent";
import Typography from "@material-ui/core/Typography";
import Button from '@material-ui/core/Button';
import Grid from "@material-ui/core/Grid";


import { createTheme, withStyles, makeStyles, ThemeProvider } from '@material-ui/core/styles';
import { green, purple, blue, red, orange } from '@material-ui/core/colors';

const useStyles = makeStyles({
  root: {
    borderStyle: "solid",
    borderWidth: "1px",
    backgroundColor: "#f7f7f7",
    borderColor: "#00688B",
    overflow: "auto",
    height: "250px",

  },
  bullet: {
    display: "inline-block",
    margin: "0 2px",
    transform: "scale(0.8)"
  },
  title: {
    fontSize: 14
  },
  pos: {
    marginBottom: 12
  },
});

export default function SimpleCard(props) {
  const {nodeInfo} = props;
  const classes = useStyles();
  return (
      <Card className={classes.root} variant="outlined">
        <CardContent>
            <Typography variant="body1" >
              <p style={{ display: 'inline', color: 'DarkGray' }}>Name:</p> {nodeInfo.name} &nbsp;&nbsp;
              <p style={{ display: 'inline', color: 'DarkGray' }}>ID:</p> {nodeInfo.id}
            </Typography>
            {
              nodeInfo.description != undefined && nodeInfo.description.length != 0 ?
                  <div>
                    <Typography variant="body1" component="p">
                        <p style={{ display: 'inline', color: 'DarkGray' }}>Definition:</p> {nodeInfo.description}
                    </Typography>
                  </div>
                  :null
            }
            {
              nodeInfo.editor_note != undefined && nodeInfo.editor_note.length != 0 ?
                  <div>
                    <Typography variant="body1" component="p">
                      <p style={{ display: 'inline', color: 'DarkGray' }}>Editor's note:</p>  {nodeInfo.editor_note}
                    </Typography>
                  </div>
                  :null
            }
        </CardContent>
      </Card>
  );
}
