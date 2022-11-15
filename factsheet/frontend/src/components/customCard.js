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

  const { top_img, id, title, study_name, acronym, abstract, institution, create_new, create_new_button  } = props;

  const [factsheet, setFactsheet] = React.useState([]);
  const [loading, setLoading] = useState(true);

  const getData = async () => {
    const { data } = await axios.get(`http://localhost:8000/factsheet/get/`, { params: { id: id } });
    let factsheet = data.replaceAll('\\', '').replaceAll('"[', '[').replaceAll(']"', ']');
    setFactsheet(JSON.parse(JSON.stringify(factsheet)));
    setLoading(false)
  };
  useEffect(() => {
    getData();
    console.log(factsheet);
  }, []);


  return (
    <Card sx={{ marginLeft: '10px', marginRight: '10px', height: '300px' }} variant="outlined">
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
      <CardActions >
        <Link to="/factsheet" style={{ textDecoration: 'none' }} state={{ fsData: factsheet }}>More</Link>
      </CardActions>
    </Card>
  );
}
