import React, { PureComponent, Fragment, useState, useEffect } from "react";
import LinearProgress from '@mui/material/LinearProgress';
import axios from "axios";
import Home from './home.js';
import Factsheet from './components/factsheet.js';
import './styles/App.css';
import conf from "./conf.json";
import { ThemeProvider } from '@mui/material/styles';
import theme from './styles/oep-theme.js';
import ComparisonBoardMain from "./components/comparisonBoardMain";
import HistoryTable from './components/historyTable.js';

function App() {
  const [factsheet, setFactsheet] = useState({});
  const [loading, setLoading] = useState(true);

  const url_params = String(window.location.href).split('/').pop();
  const url_page = String(window.location.href).split('/').at(-2);

  const getData = async () => {
    if (url_page === 'factsheet') {
      const { data } = await axios.get(conf.toep + `sirop/get/`, { params: { id: url_params } });
      return data;
    }
  };
  
  useEffect(() => {
    getData().then((data) => {
      setFactsheet(data);
      setLoading(false);
  });
  }, []);

  if (url_page === 'sirop' && url_params === '') {
    return (
      <ThemeProvider theme={theme}>
        <Home />
      </ThemeProvider>
    );
  } 


  if (url_params === 'oekg_history') {
    return <ThemeProvider theme={theme}><HistoryTable/></ThemeProvider>
  }

  if (loading === false) {
   
    if (url_page === 'compare') {
      return <ThemeProvider theme={theme}><ComparisonBoardMain params={url_params} /></ThemeProvider>
    }
    if (url_page === 'factsheet') {
      return <ThemeProvider theme={theme}><Factsheet id={url_params} fsData={factsheet}/></ThemeProvider>
    } 
  } else {
    return <LinearProgress />
  }
}

export default App;
