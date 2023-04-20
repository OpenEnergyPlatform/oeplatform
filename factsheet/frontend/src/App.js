import React, { PureComponent, Fragment, useState, useEffect } from "react";
import Grid from '@mui/material/Grid';
import CardContent from "@mui/material/CardContent";
import Card from "@mui/material/Card";
import Typography from "@mui/material/Typography";
import ApolloClient from 'apollo-boost';
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
import CircularProgress from '@mui/material/CircularProgress';
import LinearProgress from '@mui/material/LinearProgress';
import axios from "axios"
import CustomCard from './components/customCard.js'
import Home from './home.js'
import Factsheet from './components/factsheet.js'
import './styles/App.css';
import CustomSearchInput from "./components/customSearchInput"
import conf from "./conf.json";
import { createTheme, ThemeProvider } from '@mui/material/styles';

const url_id = String(window.location.href).split('/').pop()

function App() {
  const [factsheet, setFactsheet] = useState({});
  const [loading, setLoading] = useState(true);

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

  const url_id = String(window.location.href).split('/').pop();
  const getData = async () => {
    if (url_id !== '' && url_id !== 'new') {
        const { data } = await axios.get(conf.toep + `factsheet/get/`, { params: { id: url_id } });
        return data;
    }
  };
  useEffect(() => {
    getData().then((data) => {
      setFactsheet(data);
      setLoading(false);
  });
  }, []);


  
  if (url_id === '') {
    return < Home id={url_id}/>
  } else {
    if (loading === false) {
      return <ThemeProvider theme={theme}><Factsheet id={url_id} fsData={factsheet}/></ThemeProvider>
    } else {
      return <LinearProgress />
    }
  }
}

export default App;
