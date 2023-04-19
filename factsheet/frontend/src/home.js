import React, { PureComponent, Fragment, useState, useEffect } from "react";
import Grid from '@mui/material/Grid';
import CardContent from "@mui/material/CardContent";
import Card from "@mui/material/Card";
import Factsheet from './components/factsheet.js'
import CustomCard from './components/customCard.js'
import Typography from "@mui/material/Typography";
import ApolloClient from 'apollo-boost';
import { ApolloProvider } from 'react-apollo';
import CardActions from "@mui/material/CardActions";
import Box from "@mui/material/Box";
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import AddBoxIcon from '@mui/icons-material/AddBox';
import LinearProgress from '@mui/material/LinearProgress';
import { Route, Routes, Link } from 'react-router-dom';
import axios from "axios"
import './styles/App.css';
import CustomSearchInput from "./components/customSearchInput";
import { useLocation } from 'react-router-dom';
import conf from "./conf.json";
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import './styles/hexagons.css';
import ArticleOutlinedIcon from '@mui/icons-material/ArticleOutlined';

const client = new ApolloClient({
  uri: 'http://localhost:8000/graphql/',
});

function Home(props) {

  const { state } = useLocation()
  const [factsheets, setFactsheets] = React.useState([]);
  const [loading, setLoading] = useState(true);

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

  useEffect(() => {
    setLoading(true);
    axios.get(conf.toep + `factsheet/all/`).then(response => {
      console.log(response.data);
      setFactsheets(response.data);
      setLoading(false);
    });
  }, [setFactsheets, setLoading]);

  const renderCards = (fs) => {
    if (Object.keys(fs).length !== 0) {
      return fs.map(item =>
          (
            <Link to={`factsheet/${item.uid}`} onClick={() => this.forceUpdate} style={{ textDecoration: 'none', color: 'blue' }}  >
              <div >
                <p style={{ textAlign: 'center' }} > <Typography variant="h6" gutterBottom style={{ marginTop: '100px' }}><b> {item.acronym.substring(0,30)} </b></Typography></p>
                <p style={{ textAlign: 'center' }} > <Typography variant="body1" gutterBottom style={{ marginTop: '0px' }}>  <span>{item.study_name != '' ? item.study_name.substring(0,30) : <p>&nbsp;</p>}</span> </Typography></p>
              </div>
              
            </Link>
          )
          )
      }
  }

  if (loading === false) {
    return (
      <ApolloProvider client={client}>
          <div key={props.id}>
            <Grid container spacing={2} direction="row" justifyContent="space-between">
                <Grid item xs={9}>
                  <CustomSearchInput searchHandler={searchHandler} data={[{ name: 'Factsheet A', label: 'Anguilla', phone: '1-264' },
                  { name: 'Factsheet B', label: 'Albania', phone: '355' },
                  { name: 'Factsheet C', label: 'Armenia', phone: '374' }]}
                 
                  />
                </Grid>
                <Grid item xs={3}>
                    <ThemeProvider theme={theme}>
                      <Link to={`factsheet/compare`} onClick={() => this.forceUpdate} style={{ textDecoration: 'none', color: 'white' }} >
                        <Button disabled disableElevation={true} startIcon={<CompareArrowsIcon />} style={{ 'textTransform': 'none', 'margin': '10px', 'marginRight' : '20px', 'zIndex': '1000', 'float': 'right',  }} size="large" variant="contained" color="neutral" >
                          Compare 
                        </Button>
                      </Link>
                      <Link to={`factsheet/new`} onClick={() => this.forceUpdate} style={{ textDecoration: 'none', color: 'white' }} >
                        <Button disableElevation={true} startIcon={<AddBoxIcon />} style={{ 'textTransform': 'none', 'marginTop': '10px', 'zIndex': '1000', 'float': 'right',  }} size="large" variant="contained" color="primary" >
                          Add a new 
                        </Button>
                      </Link>
                    </ThemeProvider>
                </Grid>
              </Grid>
              <Grid container spacing={2} direction="row" sx={{ 'marginTop': '20px', 'marginLeft': '1%', 'marginRight': '1%','padding': '20px', 'border': '1px solid #cecece', 'height':'80vh', 'width':'98%', 'overflow': 'auto' }}>
                <div class="main">
                  <div class="container">
                    {renderCards(eval(factsheets))}
                  </div>
                </div>
              </Grid>
          </div>
      </ApolloProvider>
    );
  }
  else {
    return <Box sx={{ width: '100%' }}>
            <LinearProgress />
           </Box>
  }
}

export default Home;
