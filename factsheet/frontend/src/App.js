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
import { Route, Routes, Link } from 'react-router-dom';
import axios from "axios"

import CustomCard from './components/customCard.js'
import Home from './home.js'
import Factsheet from './components/factsheet.js'

import './styles/App.css';
import CustomSearchInput from "./components/customSearchInput"


const client = new ApolloClient({
  uri: 'http://localhost:8000/graphql/',
});

function App() {
  return (
    < Home />
  );
}

export default App;
