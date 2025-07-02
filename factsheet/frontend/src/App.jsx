// src/App.jsx
import React, { useState, useEffect } from 'react'
import CircularProgress from '@mui/material/CircularProgress'
import axios from 'axios'

import Home from './home'
import Factsheet from './components/scenarioBundle'
import ComparisonBoardMain from './components/comparisonBoardMain'
import HistoryTable from './components/historyTable'
import Diff from './components/oekg_modifications'

import './styles/App.css'
import conf from './conf.json'

function App() {
  console.log('🏠 App rendered');
  const [factsheet, setFactsheet] = useState(null)
  const [loading, setLoading] = useState(true)

  // split all path segments, e.g. '/scenario-bundles/id/NEW' → ['scenario-bundles','id','NEW']
  const [resource, route, idOrNew] =
    window.location.pathname.split('/').slice(1)

  useEffect(() => {
    async function fetchData() {
      // only fetch when route==='id' and we have an id/new
      if (resource === 'scenario-bundles' && route === 'id' && idOrNew) {
        try {
          const { data } = await axios.get(
            `${conf.toep}scenario-bundles/get/`,
            { params: { id: idOrNew } }
          )
          setFactsheet(data)
        } catch (err) {
          console.error('Fetch error:', err)
        }
      }
      setLoading(false)
    }
    fetchData()
  }, [resource, route, idOrNew])

  // top-level routes that don’t need data
  if (resource === 'scenario-bundles' && route === 'main') {
    return <Home />
  }
  if (resource === 'scenario-bundles' && route === 'oekg_history') {
    return <HistoryTable />
  }
  if (resource === 'scenario-bundles' && route === 'oekg_modifications') {
    return <Diff />
  }
  if (!loading) {
    if (resource === 'scenario-bundles' && route === 'compare') {
      const uidString = window.location.pathname.split('/')[3] || '';
      const uids = uidString.split('&'); // ✅ split into array
      return <ComparisonBoardMain params={uids} />
    }
    // now matches both '/scenario-bundles/id/new' and '/scenario-bundles/id/<uuid>'
    if (resource === 'scenario-bundles' && route === 'id' && idOrNew) {
      return <Factsheet id={idOrNew} fsData={factsheet || {}} />
    }
    return null
  }

  // still loading
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh'
    }}>
      <CircularProgress />
    </div>
  )
}

export default App
