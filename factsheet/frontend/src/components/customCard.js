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
      <CardContent>
        <Typography gutterBottom variant="h5" component="div">
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {text}
        </Typography>
      </CardContent>
      <CardActions>
        <Button variant="outlined" size="small">View</Button>
        {create_new_button && <Button variant="contained" size="small" onClick={create_new}>Create new</Button>}
      </CardActions>
    </Card>
  );
}
