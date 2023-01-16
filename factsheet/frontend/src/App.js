import React, { PureComponent, Fragment, useState, useEffect } from "react";
import Grid from '@mui/material/Grid';
import CardContent from "@mui/material/CardContent";
import Card from "@mui/material/Card";
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
import Backdrop from '@mui/material/Backdrop';
import CircularProgress from '@mui/material/CircularProgress';
import axios from "axios"

import CustomCard from './components/customCard.js'
import Home from './home.js'
import Factsheet from './components/factsheet.js'

import './styles/App.css';
import CustomSearchInput from "./components/customSearchInput"

import conf from "./conf.json";

const url_id = String(window.location.href).split('/').pop()

const client = new ApolloClient({
  uri: 'http://localhost:8000/graphql/',
});

function App() {
  const [factsheet, setFactsheet] = useState({});
  const [loading, setLoading] = useState(true);

  const url_id = String(window.location.href).split('/').pop();
  const getData = async () => {
    if (url_id !== '' && url_id !== 'new') {
        const { data } = await axios.get(conf.toep + `factsheet/get/`, { params: { id: url_id } });
        const fsd = data.replaceAll('\\', '').replaceAll('"[', '[').replaceAll(']"', ']');
        const result = eval(fsd)[0].fields.factsheetData;
        return result;
    }
  };
  useEffect(() => {
    getData().then((data) => {
      setFactsheet(data);
      setLoading(false);
  });;
  }, []);

  if (url_id === '') {
    return < Home id={url_id}/>
  } else {
    if (loading === false) {
      return <Factsheet id={url_id} fsData={factsheet}/>
    } else {
      return <Box sx={{ width: '100%' }}>
              <Backdrop open={loading} sx={{ backgroundColor:'white' }} >
                <CircularProgress sx={{ margin: '5px' }} />
                <div>
                  Please wait ...
                </div>

              </Backdrop>
             </Box>
    }
  }
}

export default App;
