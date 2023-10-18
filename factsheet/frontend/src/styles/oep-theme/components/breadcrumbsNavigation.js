import { Grid } from '@mui/material';
import { styled } from '@mui/material/styles';
import ListAltOutlinedIcon from '@mui/icons-material/ListAltOutlined';

const BreadcrumbsNav = styled(Grid)(({ theme }) => ({
  backgroundColor: theme.palette.grey[300], 
  height: '150px',
  marginBottom: '10px',
  
  '& .header-style': {
    'padding-top': '20px',
    'padding-left': '60px',
    'display': 'flex',
    'align-items': 'center',
    'font-size': '20px'
  },

  '& .header-style p': {
    'color': 'rgb(72, 72, 72)',
    'margin-left': '10px',
    'font-size': '20px'
  },

  '& .header-style span': {
    'margin-top': '4px',
    'color': 'rgb(72, 72, 72)'
  },

  '& .header-substyle': {
    'padding-left': '60px',
    'display': 'flex',
    'align-items': 'center',
    'font-size': '20px'
  },

  '& .header-substyle span': {
    'text-transform': 'uppercase',
    'font-weight': 'bold'
  },
}));

export default function BreadcrumbsNavGrid({ acronym, id, mode }) {
  return (
    <BreadcrumbsNav container>
      <Grid item xs={12} className='header-style'>
        <span>
          <ListAltOutlinedIcon />
        </span>
        <p>Scenario Bundle</p>
      </Grid>
      <Grid item xs={12} className='header-substyle'>
        <span> 
          {id === "new" ? "new/" : mode + "/"} 
        </span> 
        {acronym}
      </Grid>
    </BreadcrumbsNav>
  );
}
