import 'vite/modulepreload-polyfill';
import React from "react";
import { createRoot } from 'react-dom/client';
import App from "./App";
import { ScenarioProvider } from "./context/ScenarioContext";
import "./styles/index.css";

const root = createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ScenarioProvider>
      <App />
    </ScenarioProvider>
  </React.StrictMode>
);
