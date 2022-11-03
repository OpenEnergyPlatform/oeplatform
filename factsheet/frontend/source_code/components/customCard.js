import * as React from 'react';
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import CardMedia from '@mui/material/CardMedia';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';

export default function CustomCard(props) {

  const { top_img, title, text, create_new, create_new_button  } = props;
  return (
    <Card sx={{ maxWidth: 345 }}>
      <CardMedia
        component="img"
        height="140"
        alt="green iguana"
      />
      <CardContent>
        <Typography gutterBottom variant="h5" component="div">
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Do you want to learn more about scenarios and models related to the data? Then, this is the right place to look. Also if you contributed data and want to provide more context, Create your own factsheet here.
        </Typography>
      </CardContent>
      <CardActions>
        <Button variant="outlined" size="small">View</Button>
        {create_new_button && <Button variant="contained" size="small" onClick={create_new}>Create new</Button>}
      </CardActions>
    </Card>
  );
}
