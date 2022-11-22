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
import CustomSearchInput from "./components/customSearchInput"


const client = new ApolloClient({
  uri: 'http://localhost:8000/graphql/',
});

function Home() {

  const [factsheets, setFactsheets] = React.useState([]);
  const [loading, setLoading] = useState(true);

  const searchHandler = (v) => {
    console.log(v);
  };
  const getData = async () => {
    const { data } = await axios.get(`http://localhost:8000/factsheet/all/`);
    let factsheets = data.replaceAll('\\', '').replaceAll('"[', '[').replaceAll(']"', ']');
    setFactsheets(JSON.parse(JSON.stringify(factsheets)));
    setLoading(false)
  };
  useEffect(() => {
    getData();
  }, []);

  const renderCards = (fs) => {
    if (Object.keys(fs).length !== 0) {
      console.log('f');
      return fs.map(item =>
          (<Grid item xs={3}>
            <CustomCard
              id={item.pk}
              title={item.fields.factsheetData.name}
              study_name={item.fields.factsheetData.study_name}
              acronym={item.fields.factsheetData.acronym}
              abstract={item.fields.factsheetData.abstract}
              fs={item}
            />
          </Grid>)
          )
      }
  }

  if (loading === false) {
    return (
      <ApolloProvider client={client}>
          <div >
            <Grid container spacing={2} direction="row" justifyContent="space-between">
                <Grid item xs={10}>
                  <CustomSearchInput searchHandler={searchHandler} data={[{ name: 'Factsheet A', label: 'Anguilla', phone: '1-264' },
                  { name: 'Factsheet B', label: 'Albania', phone: '355' },
                  { name: 'Factsheet C', label: 'Armenia', phone: '374' }]}/>
                </Grid>
                <Grid item xs={2}>
                      <Link to={`factsheet/fs/new`} onClick={() => this.forceUpdate} style={{ textDecoration: 'none', color: 'white' }} >
                        <Button disableElevation={true} startIcon={<AddBoxIcon />} style={{ 'textTransform': 'none', 'margin': '10px', 'marginBottom' : '10px', 'marginRight' : '20px','height': '55px', 'zIndex': '1000', 'float': 'right' }} variant="contained" color="primary" >
                          Add a new Factsheet
                        </Button>
                      </Link>
                </Grid>
              </Grid>
              <Grid container spacing={2} direction="row" sx={{ 'marginTop': '20px', 'marginLeft': '1%', 'marginRight': '1%','padding': '20px', 'border': '1px solid #cecece', 'height':'75vh', 'width':'98%', 'overflow': 'auto'  }}>
                {renderCards(eval(factsheets))}
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
