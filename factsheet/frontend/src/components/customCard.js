import React, { PureComponent, Fragment, useState, useEffect } from "react";
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import CardMedia from '@mui/material/CardMedia';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { Route, Routes, Link } from 'react-router-dom';
import Checkbox from '@mui/material/Checkbox';

import axios from "axios"

export default function CustomCard(props) {
  const { fs, id, study_name, acronym, abstract, institution, create_new, create_new_button  } = props;

  return (
    <Card sx={{ marginLeft: '10px', marginRight: '10px', minHeight: 200,  display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }} variant="outlined">
      <CardContent>
        <Typography gutterBottom variant="subtitle1" component="div">
          <b>{acronym.substring(0,50)}</b>
        </Typography>
        <Typography variant="subtitle2" color="text.secondary">
          <b> Study name: </b> {study_name.substring(0,50)}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          <b> Abstract: </b> {abstract.substring(0,180) + '...'}
        </Typography>
      </CardContent>
      <CardActions class="actions">
        <Link to={`factsheet/fs/${id}`} onClick={() => this.forceUpdate} style={{ textDecoration: 'none', color: 'blue' }}  >
          <Button disableElevation={true} variant="text" color="primary" size="small" >
            More...
          </Button>
        </Link>
        <Checkbox  />
      </CardActions>
    </Card>
  );
}
