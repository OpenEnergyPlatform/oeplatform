// src/App.jsx
import React, { useState, useEffect } from 'react';
import CircularProgress from '@mui/material/CircularProgress';
import axios from 'axios';

import Home from './home';
import Factsheet from './components/scenarioBundle';
import ComparisonBoardMain from './components/comparisonBoardMain';
import HistoryTable from './components/historyTable';
import Diff from './components/oekg_modifications';

import './styles/App.css';
import conf from './conf.json';

function App() {
  console.log('🏠 App rendered');
  const [factsheet, setFactsheet] = useState({});
  const [loading, setLoading] = useState(true);

  // parse the first three path segments: /{param1}/{param2}/{param3}
  const [param1, param2] = window.location.pathname.split('/').slice(1, 3);

  useEffect(() => {
    async function fetchData() {
      if (param1 === 'id' && param2) {
        try {
          const { data } = await axios.get(
            `${conf.toep}scenario-bundles/get/`,
            { params: { id: param2 } }
          );
          setFactsheet(data);
        } catch (err) {
          console.error('Fetch error:', err);
        }
      }
      setLoading(false);
    }
    fetchData();
  }, [param1, param2]);

  // top‐level routes
  if (param2 === 'main') return <Home />;
  if (param2 === 'oekg_history') return <HistoryTable />;
  if (param2 === 'oekg_modifications') return <Diff />;

  // once data is loaded
  if (!loading) {
    if (param2 === 'compare') {
      return <ComparisonBoardMain params={param2} />;
    }
    if (param2 === 'id') {
      return <Factsheet id={param2} fsData={factsheet} />;
    }
    return null;
  }

  // loading spinner
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh'
    }}>
      <CircularProgress />
    </div>
  );
}

export default App;
