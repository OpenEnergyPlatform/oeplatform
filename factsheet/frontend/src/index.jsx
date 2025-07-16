// src/index.jsx
import 'vite/modulepreload-polyfill';
import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

import { CacheProvider } from '@emotion/react';
import createEmotionCache from './components/createEmotionCache';

import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider } from '@mui/material/styles';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

import theme from './styles/oep-theme';
import App from './App';
import './index.css';

const cache = createEmotionCache();
const container = document.getElementById('root');
const root = createRoot(container);

root.render(
  // StrictMode currently breaks DND in qualitative comparison
  // <React.StrictMode>
    <CacheProvider value={cache}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}>
            <App sx={{ '& :first-of-type': { marginTop: 0 } }} />
          </BrowserRouter>
        </LocalizationProvider>
      </ThemeProvider>
    </CacheProvider>
  // </React.StrictMode>
);
