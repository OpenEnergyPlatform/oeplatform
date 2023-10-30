import React, { PureComponent, Fragment, useState, useEffect } from "react";
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import CardMedia from '@mui/material/CardMedia';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { Route, Routes, Link } from 'react-router-dom';
import Checkbox from '@mui/material/Checkbox';
import TextField from '@mui/material/TextField';
import axios from "axios"
import Chip from '@mui/material/Chip';
import '../styles/hexagons.css';
import { Box } from "@mui/system";

export default function CustomCard(props) {
  const { fs, id, study_name, acronym, abstract, institution, create_new, create_new_button  } = props;

  return (
    <Box>
            <b>{acronym.substring(0,50)}</b>
         
    </Box>
  );
}
