import React, { PureComponent, Fragment, useState, useEffect } from "react";
import Grid from '@mui/material/Grid';
import Typography from "@mui/material/Typography";
import ApolloClient from 'apollo-boost';
import Button from '@mui/material/Button';
import AddBoxIcon from '@mui/icons-material/AddBox';
import LinearProgress from '@mui/material/LinearProgress';
import { Route, Routes, Link } from 'react-router-dom';
import axios from "axios"

import CustomTable from "./components/customTable.js";
import { useLocation } from 'react-router-dom';
import conf from "./conf.json";
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import { createTheme, ThemeProvider } from '@mui/material/styles';

import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import Divider from '@mui/material/Divider';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import SearchIcon from "@material-ui/icons/Search";
import HelpIcon from '@mui/icons-material/Help';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import Info from "@mui/icons-material/Info";
import ShareIcon from '@mui/icons-material/Share';
import SettingsIcon from '@mui/icons-material/Settings';
import InsightsIcon from '@mui/icons-material/Insights';
import MenuIcon from '@mui/icons-material/Menu';
import  { makeStyles } from '@material-ui/core/styles';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import ButtonGroup from '@mui/material/ButtonGroup';


import './styles/App.css';

function Home(props) {

  const [factsheets, setFactsheets] = React.useState([]);
  const [loading, setLoading] = useState(true);

  const [state, setState] = React.useState({
    top: false,
    left: false,
    bottom: false,
    right: false,
  });

  const searchHandler = (v) => {
    console.log(v);
  };

  const theme = createTheme({
    status: {
      danger: '#e53e3e',
    },
    palette: {
      primary: {
        main: '#04678F',
        darker: '#053e85',
        contrastText: '#fff',
      },
      neutral: {
        main: '#198BB9',
        darker: '#053e85',
        contrastText: '#fff',
      },
    },
  });

  const useStyles = makeStyles({
    drawerPaper: {
      marginTop: "72px",
    }
  });

  const classes = useStyles();

  useEffect(() => {
    setLoading(true);
    axios.get(conf.toep + `factsheet/all/`).then(response => {
      setFactsheets(response.data);
      setLoading(false);
    });
  }, [setFactsheets, setLoading]);

  const renderCards = (fs) => {
    if (Object.keys(fs).length !== 0) {
      return fs.map(item =>
          (
            <Link to={`factsheet/fs/${item.uid}`} onClick={() => this.forceUpdate} style={{ textDecoration: 'none', color: 'blue' }}  >
              <div >
                <p style={{ width: '200px', height: '50px' }}> 
                </p>
                <p style={{ textAlign: 'center',  width: '200px', height: '100px', marginLeft: '50px' }}> 
                <Typography variant="body1" gutterBottom >
                  <b> {item.study_name} </b>  
                </Typography>
                </p>
                <p style={{ textAlign: 'center' }} > <Typography variant="body1" gutterBottom>  <span>{item.acronym}</span> </Typography></p>
                {/* <p style={{ textAlign: 'center' }} > <Typography variant="caption" gutterBottom style={{ color: '#9b9b9b' }}>  <span> 2023.04.01</span> </Typography></p> */}
                <p style={{ textAlign: 'center' }} > 
                  <Checkbox  color="default" />
                </p>
              </div>
              
            </Link>
          )
          )
      }
  }

  const toggleDrawer = (anchor, open) => (event) => {
    if (event.type === 'keydown' && (event.key === 'Tab' || event.key === 'Shift')) {
      return;
    }
    setState({ ...state, [anchor]: open });
  };

  const handleConditionChange = (consdition) => {
    console.log(consdition);
  }

  const list = (anchor) => (
    <Box
      sx={{ width: anchor === 'top' || anchor === 'bottom' ? 'auto' : 250 }}
      role="presentation"
      onClick={toggleDrawer(anchor, false)}
      onKeyDown={toggleDrawer(anchor, false)}
    >
      <List>
        {['Add a new factsheet', 'Compare selected', 'Free text search', 'Visualizations'].map((text, index) => (
          <ListItem key={text} disablePadding>
            <ListItemButton>
              <ListItemIcon>
                {index === 0 && <AddCircleIcon style={{ color: '#005374' }}/>}
                {index === 1 && <CompareArrowsIcon style={{ color: '#005374' }}/>}
                {index === 2 && <SearchIcon style={{ color: '#005374' }}/>}
                {index === 3 && <InsightsIcon style={{ color: '#005374' }}/>}
              </ListItemIcon>
              {index === 0 && <ListItemText 
                primary={
                  <Link to={`factsheet/fs/new`} onClick={() => this.forceUpdate} style={{ textDecoration: 'none', color: '#005374' }} >
                    <Typography variant="body1" style={{ color: '#005374' }}>
                      {text} 
                    </Typography>
                  </Link>}
              />}
              {index === 1 && <ListItemText primary={
                <Link to={`factsheet/fs/compare/`} onClick={() => this.forceUpdate} style={{ textDecoration: 'none', color: 'white' }} >
                  <Typography variant="body1" style={{ color: '#005374' }}>{text} </Typography>
                </Link>}
              />}
              {index === 2 && <ListItemText primary={<Typography variant="body1" style={{ color: '#005374' }}>{text} </Typography>} />}
              {index === 3 && <ListItemText primary={<Typography variant="body1" style={{ color: '#005374' }}>{text} </Typography>} />}
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Divider />
      <List>
        {['Settings', 'Share', 'FAQ', 'Help'].map((text, index) => (
          <ListItem key={text} disablePadding>
            <ListItemButton>
              <ListItemIcon>
                {index === 3 && <HelpIcon style={{ color: '#005374' }}/>}
                {index === 2 && <Info style={{ color: '#005374' }}/>}
                {index === 1 && <ShareIcon style={{ color: '#005374' }}/>}
                {index === 0 && <SettingsIcon style={{ color: '#005374' }}/>}
              </ListItemIcon>
              {index === 0 && <ListItemText primary={<Typography variant="body1" style={{ color: '#005374' }}>{text} </Typography>} />}
              {index === 1 && <ListItemText primary={<Typography variant="body1" style={{ color: '#005374' }}>{text} </Typography>} />}
              {index === 2 && <ListItemText primary={<Typography variant="body1" style={{ color: '#005374' }}>{text} </Typography>} />}
              {index === 3 && <ListItemText primary={<Typography variant="body1" style={{ color: '#005374' }}>{text} </Typography>} />}
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  if (loading === false) {
    return (
            <ThemeProvider theme={theme}>
              {/* <Grid container spacing={2} direction="row" sx={{ 'marginTop': '10px', 'marginLeft': '1%', 'marginRight': '1%','padding': '10px', 'border': '1px solid #cecece', 'height':'410px', 'width':'98%', 'overflow': 'auto', 'backgroundColor':' #0c455cfa', 'borderRadius': '5px' }}>
                <Grid item xs={5}>
                  <div>
                    <ThemeProvider theme={theme}>
                        <Button 
                          style={{ 'textTransform': 'none', 'marginLeft': '0px', 'zIndex': '1000'  }} size="large" variant="contained" color="neutral"
                          onClick={toggleDrawer('Main Menu', true)}>
                          <MenuIcon />
                        </Button>
                        <Drawer
                        anchor={'left'}
                        open={state['Main Menu']}
                        onClose={toggleDrawer('Main Menu', false)}
                        classes={{
                          paper: classes.drawerPaper
                        }}
                      >
                        {list('anchor')}
                      </Drawer>
                    </ThemeProvider>
                  </div>
                  <div class="main-main">
                    <div class="container2">
                      <div>
                        <p style={{ textAlign: 'center' }} > <Typography variant="h6" gutterBottom style={{ marginTop: '70px' }}>Studies</Typography></p>
                        <p style={{ textAlign: 'center', marginTop: '-20px' }} > <Typography variant="caption" gutterBottom >More info </Typography></p>

                      </div>
                      <div>
                        <p style={{ textAlign: 'center' }} > <Typography variant="h6" gutterBottom style={{ marginTop: '70px' }}>Scenarios</Typography></p>
                        <p style={{ textAlign: 'center', marginTop: '-20px' }} > <Typography variant="caption" gutterBottom >More info </Typography></p>

                      </div>
                      <div>
                        <p style={{ textAlign: 'center' }} > <Typography variant="h6" gutterBottom style={{ marginTop: '70px' }}>Models</Typography></p>
                        <p style={{ textAlign: 'center', marginTop: '-20px' }} > <Typography variant="caption" gutterBottom >More info </Typography></p>

                      </div>
                      <div>
                        <p style={{ textAlign: 'center' }} > <Typography variant="h6" gutterBottom style={{ marginTop: '70px' }}>Frameworks</Typography></p>
                        <p style={{ textAlign: 'center', marginTop: '-20px' }} > <Typography variant="caption" gutterBottom >More info </Typography></p>

                      </div>
                      <div>
                        <p style={{ textAlign: 'center' }} > <Typography variant="h6" gutterBottom style={{ marginTop: '70px' }}>Datasets</Typography></p>
                        <p style={{ textAlign: 'center', marginTop: '-20px' }} > <Typography variant="caption" gutterBottom >More info </Typography></p>
                      </div>
                     
                    </div>
                  </div>
                </Grid>
                <Grid item xs={7}>
                  <div style={{ 'height':'360px', 'border': '1px solid #cecece82', 'marginRight': '50px', 'marginTop': '-5px', 'marginBottom': '30px', 'backgroundColor':' #ffffff', 'borderRadius': '5px' }} >
                    <p style={{ textAlign: 'center', 'width':'100%', color: '#04678F' }} >
                      <Typography variant="6" gutterBottom style={{ marginTop: '30px' }}> <b> BUILD YOUR QUERY </b> </Typography>
                    </p>
                    <ThemeProvider theme={theme}>
                    <div>
                        <Select
                          label=""
                          value={"Choose a condition"}
                          onChange={handleConditionChange}
                          variant="outlined" 
                          style={{ width: '50%', 'height': '35px', marginTop:'10px', marginBottom:'20px', marginLeft: '170px' }}
                        >
                          <MenuItem value={10}>Region</MenuItem>
                          <MenuItem value={20}>Scenario year</MenuItem>
                          <MenuItem value={30}>Energy carrier</MenuItem>
                        </Select>
                        <Button disableElevation={true} style={{ 'height': '35px', 'marginLeft': '10px' }} size="large" variant="contained" color="primary"> <AddBoxIcon /> </Button>
                        <Button disableElevation={true} style={{ 'height': '35px', 'marginLeft': '10px' }} variant="contained" color="error"> <DeleteOutlineIcon /> </Button>
                      </div>
                      <div>
                        <Button disableElevation={true} startIcon={<PlayArrowIcon />} style={{ 'height': '35px', 'marginLeft': '170px', 'marginTop': '10px' }} size="large" variant="contained" color="primary" >
                            Run
                        </Button>
                      </div>
                    </ThemeProvider>
                  </div>
                </Grid>
              </Grid> */}
              {/* <Grid container spacing={2} direction="column" sx={{ 'marginTop': '20px', 'marginLeft': '1%', 'marginRight': '1%','padding': '20px', 'height':'80vh', 'width':'98%', 'overflow': 'auto' }}>
                    {renderCards(eval(factsheets))}
                      <div>
                      <Box
                        sx={{
                          display: 'flex',
                          flexDirection: 'row',
                          alignItems: 'left',
                          '& > *': {
                            m: 0.3,
                          },
                        }}
                      >
                        <Link to={`factsheet/fs/new`} onClick={() => this.forceUpdate} style={{ textDecoration: 'none', color: '#005374' }} >
                            <Button variant="contained" key="Add">Add a new</Button>
                        </Link>
                        <Link to={`factsheet/fs/compare`} onClick={() => this.forceUpdate} style={{ textDecoration: 'none', color: 'white' }} >
                            <Button variant="outlined" key="Compare">Compare</Button>
                        </Link>
                        <Button variant="outlined" key="Search">Search</Button>
                      </Box>
                      </div>
                      <div>
                      <CustomTable />
                     </div>
              </Grid> */}
              <CustomTable factsheets={eval(factsheets)} />
            </ThemeProvider>
    );
  }
  else {
    return <Box sx={{ width: '100%' }}>
            <LinearProgress />
           </Box>
  }
}

export default Home;
