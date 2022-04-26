import React from "react";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import CardContent from "@material-ui/core/CardContent";
import Typography from "@material-ui/core/Typography";
import Button from '@material-ui/core/Button';
import ButtonGroup from '@material-ui/core/ButtonGroup';
import { createTheme, withStyles, makeStyles, ThemeProvider } from '@material-ui/core/styles';
import { green, purple, blue, red, orange } from '@material-ui/core/colors';
import Divider from '@material-ui/core/Divider';
import Grid from "@material-ui/core/Grid";
import StorageIcon from '@material-ui/icons/Storage';
import UnfoldLessIcon from '@material-ui/icons/UnfoldLess';
import UnfoldMoreIcon from '@material-ui/icons/UnfoldMore';
import CenterFocusWeakIcon from '@material-ui/icons/CenterFocusWeak';
import FullscreenIcon from '@material-ui/icons/Fullscreen';
import SelectAllIcon from '@material-ui/icons/SelectAll';
import ExpandLessIcon from '@material-ui/icons/ExpandLess';
import ExpandMoreIcon from '@material-ui/icons/ExpandMore';
import ArrowDropUpIcon from '@material-ui/icons/ArrowDropUp';

import CustomSearchInput from "../presentational/customSearchInput.js";
import CustomSwitch from "./customSwitch.js";

const PurpleButton = withStyles((theme) => ({
  root: {
    color: 'white',
    backgroundColor: '#50394c',
    '&:hover': {
      backgroundColor: 'black',
    },
  },
}))(Button);

const GreenButton = withStyles((theme) => ({
  root: {
    color: 'white',
    backgroundColor: '#82b74b',
    '&:hover': {
      backgroundColor: 'black',
    },
  },
}))(Button);

const BlueButton = withStyles((theme) => ({
  root: {
    color: 'white',
    backgroundColor: '#667292',
    '&:hover': {
      backgroundColor: 'black',
    },
  },
}))(Button);

const RedButton = withStyles((theme) => ({
  root: {
    color: 'white',
    backgroundColor: '#c94c4c',
    '&:hover': {
      backgroundColor: 'black',
    },
  },
}))(Button);

const DarkGreenButton = withStyles((theme) => ({
  root: {
    color: 'white',
    backgroundColor: '#5b9aa0',
    '&:hover': {
      backgroundColor: 'silver',
    },
  },
}))(Button);

const OrangeButton = withStyles((theme) => ({
  root: {
    color: 'white',
    backgroundColor: '#034f84',
    '&:hover': {
      backgroundColor: 'black',
    },
  },
}))(Button);

const theme = createTheme({
  palette: {
    primary: green,
  },
});

export default function LayoutActions(props) {
  const {
    focusHandler,
    annotate,
    search,
    viewAll,
    hierarchicalView,
    fitAllHandler,
    annotateDatabaseHandler,
    expandHandler,
    showParentHandler,
    shrinkHandler,
    viewAllHandler,
    toggleRenderMode,
    HierarchicalViewHandler,
    searchHandler
  } = props;

  return (
      <div>
        <Grid container
              direction="row"
              >
              <Grid item xs={6}>
                  <ButtonGroup color="primary" aria-label="outlined primary button group">
                      {annotate &&
                        <GreenButton
                          variant="contained"
                          component="span"
                          onClick={annotateDatabaseHandler}
                          startIcon={<StorageIcon />}>
                        Annotate My Data
                        </GreenButton>
                      }
                      <RedButton
                        variant="contained"
                        component="span"
                        startIcon={<ExpandLessIcon />}
                        onClick={shrinkHandler}>
                          Shrink
                      </RedButton>
                      <OrangeButton
                        variant="contained"
                        component="span"
                        startIcon={<ExpandMoreIcon />}
                        onClick={expandHandler}>
                          Expand
                      </OrangeButton>
                      <GreenButton
                        variant="contained"
                        component="span"
                        onClick={showParentHandler}
                        startIcon={<ArrowDropUpIcon />}>
                          Parent
                      </GreenButton>
                      <PurpleButton
                        variant="contained"
                        component="span"
                        startIcon={<CenterFocusWeakIcon />}
                        onClick={focusHandler}>
                          Focus
                      </PurpleButton>
                      <BlueButton
                        variant="contained"
                        component="span"
                        startIcon={<FullscreenIcon />}
                        onClick={fitAllHandler}>
                          Fit
                      </BlueButton>
                      {viewAll && <DarkGreenButton
                        variant="contained"
                        component="span"
                        startIcon={<SelectAllIcon />}
                        onClick={viewAllHandler}>
                          View All
                      </DarkGreenButton>}
                    </ButtonGroup>
                </Grid>
                <Grid item xs={1}>
                  {hierarchicalView && <CustomSwitch toggleRenderMode={HierarchicalViewHandler}/>}
                </Grid>
                <Grid item xs={5}>
                  {search && <CustomSearchInput searchHandler={searchHandler} />}
                </Grid>
        </Grid>
      </div>
  );
}
