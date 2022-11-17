import React, { PureComponent, Fragment, useState, useEffect } from "react";
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import CardMedia from '@mui/material/CardMedia';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { Route, Routes, Link } from 'react-router-dom';

import axios from "axios"

export default function CustomCard(props) {
  const { fs, id, title, study_name, acronym, abstract, institution, create_new, create_new_button  } = props;


  return (
    <Card sx={{ marginLeft: '10px', marginRight: '10px', height: '240px' }} variant="outlined">
      <CardContent>
        <Typography gutterBottom variant="h5" component="div">
          {title}
        </Typography>
        <Typography variant="h6" color="text.secondary">
          {study_name}
        </Typography>
        <Typography variant="h6" color="text.secondary">
          {acronym}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {abstract}
        </Typography>
      </CardContent>
      <CardActions class="actions">
        <Link to={`factsheet/fs/${id}`} onClick={() => this.forceUpdate} style={{ textDecoration: 'none', color: 'blue' }}  >
          <Button disableElevation={true} variant="text" color="primary" size="small" >
            More...
          </Button>
        </Link>
      </CardActions>
    </Card>
  );
}
