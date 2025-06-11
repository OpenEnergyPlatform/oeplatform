// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: MIT

import React, { PureComponent, Fragment, useState, useEffect } from "react";
import LinearProgress from '@mui/material/LinearProgress';
import CircularProgress from '@mui/material/CircularProgress';
import axios from "axios";
import Home from './home.js';
import Factsheet from './components/scenarioBundle';
import './styles/App.css';
import conf from "./conf.json";
import { ThemeProvider } from '@mui/material/styles';
import theme from './styles/oep-theme.js';
import ComparisonBoardMain from "./components/comparisonBoardMain";
import HistoryTable from './components/historyTable.js';
import Diff from './components/oekg_modifications.js';

function App() {
  const [factsheet, setFactsheet] = useState({});
  const [loading, setLoading] = useState(true);

  const param_1 = String(window.location.href).split('/')[4];
  const param_2 = String(window.location.href).split('/')[5];
  const param_3 = String(window.location.href).split('/')[6];

  console.log(param_1, param_2, param_3)

  const getData = async () => {
    if (param_1 === 'id' && param_2 !== 'undefined') {
      const { data } = await axios.get(conf.toep + `scenario-bundles/get/`, { params: { id: param_2 } });
      return data;
    }
  };

  useEffect(() => {
    getData().then((data) => {
      setFactsheet(data);
      setLoading(false);
    });
  }, []);

  if (param_1 === 'main') {
    return (
      <ThemeProvider theme={theme}>
        <Home />
      </ThemeProvider>
    );
  }


  if (param_1 === 'oekg_history') {
    return <ThemeProvider theme={theme}><HistoryTable /></ThemeProvider>
  }

  if (param_1 === 'oekg_modifications') {
    return <ThemeProvider theme={theme}><Diff /></ThemeProvider>
  }

  if (loading === false) {

    if (param_1 === 'compare') {
      return <ThemeProvider theme={theme}><ComparisonBoardMain params={param_2} /></ThemeProvider>
    }
    if (param_1 === 'id') {
      return <ThemeProvider theme={theme}><Factsheet id={param_2} fsData={factsheet}/></ThemeProvider>
    }
  } else {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <CircularProgress />
    </div>
  }
}

export default App;
