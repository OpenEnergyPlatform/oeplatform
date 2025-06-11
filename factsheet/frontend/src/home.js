// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: MIT

import React, { PureComponent, Fragment, useState, useEffect } from "react";
import Typography from "@mui/material/Typography";
import LinearProgress from '@mui/material/LinearProgress';
import { Route, Routes, Link } from 'react-router-dom';
import axios from "axios"
import CustomTable from "./components/customTable.js";
import conf from "./conf.json";
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import { createTheme, ThemeProvider } from '@mui/material/styles';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';

import  { makeStyles } from '@material-ui/core/styles';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import ButtonGroup from '@mui/material/ButtonGroup';


//import BootstrapButton from './styles/style.js';

import './styles/App.css';


import { StyledEngineProvider } from '@mui/material/styles';

function Home(props) {

  const [factsheets, setFactsheets] = React.useState([]);
  const [loading, setLoading] = useState(true);

  const useStyles = makeStyles({
    drawerPaper: {
      marginTop: "72px",
    }
  });

  useEffect(() => {
    setLoading(true);
    axios.get(conf.toep + `scenario-bundles/all/`).then(response => {
      const token = response.data.token;
      setFactsheets(response.data);
      setLoading(false);
    });
  }, [setFactsheets, setLoading]);

  if (loading === false) {
    return (
      <Box>
        <CustomTable factsheets={eval(factsheets)} />
      </Box>
    );
  }
  else {
    return <Box sx={{ paddingTop: theme => theme.spacing(2) }}>
              <LinearProgress />
           </Box>
  }
}

export default Home;
