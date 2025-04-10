// SPDX-FileCopyrightText: 2025 Adel Memariani <memarian@haskell2go.iks.cs.ovgu.de>
//
// SPDX-License-Identifier: MIT

import React from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter } from 'react-router-dom';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

ReactDOM.render(
  <React.StrictMode>
    <BrowserRouter >
      <App />
    </BrowserRouter >
  </React.StrictMode>,
  document.getElementById('root')
);

reportWebVitals();
