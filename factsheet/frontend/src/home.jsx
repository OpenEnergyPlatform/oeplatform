import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';
import axios from 'axios';

import CustomTable from './components/customTable';
import conf from './conf.json';

export default function Home() {
  console.log('🏠 Home rendered');
  const [factsheets, setFactsheets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const response = await axios.get(`${conf.toep}scenario-bundles/all/`);
        if (mounted) setFactsheets(response.data);
      } catch (err) {
        console.error('Failed to fetch factsheets', err);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
  }, []);

  if (loading) {
    return (
      <Box sx={{ pt: 2 }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ mt: '72px' }}>
      <CustomTable factsheets={factsheets} />
    </Box>
  );
}
