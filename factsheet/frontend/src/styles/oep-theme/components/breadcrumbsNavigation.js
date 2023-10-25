import { Grid } from '@mui/material';
import { styled } from '@mui/material/styles';
import Container from '@mui/material/Container';
import ListAltOutlinedIcon from '@mui/icons-material/ListAltOutlined';
import palette from '../palette';
import variables from '../variables';

const BreadcrumbsNav = styled(Grid)(({ theme }) => ({
  backgroundColor: theme.palette.grey[100],
  color: palette.text.primary,
  paddingBottom: variables.spacing[5],
  marginBottom: variables.spacing[4],

  '& .header-style': {
    paddingTop: variables.spacing[4],
    display: 'flex',
    alignItems: 'center',
    fontWeight: theme.typography.fontWeightLight,
    fontSize: variables.fontSize.lg
  },

  '& .header-style span': {
    marginTop: variables.spacing[1],
    color: palette.text.primary
  },

  '& .header-style p': {
    paddingLeft: variables.spacing[2],
    color: palette.text.primary,
    fontSize: variables.fontSize.lg
  },

  '& .header-substyle': {
    display: 'flex',
    alignItems: 'center',
    fontSize: variables.fontSize.md
  },

  '& .header-substyle span': {
    paddingRight: variables.spacing[2],
    textTransform: 'uppercase',
    fontWeight: theme.typography.fontWeightBold
  },
}));

export default function BreadcrumbsNavGrid({ acronym, id, mode }) {
  return (
    <BreadcrumbsNav container>
      <Container maxWidth="lg">
        <Grid item xs={12} className='header-style'>
          <span>
            <ListAltOutlinedIcon />
          </span>
          <p>Scenario Bundle</p>
        </Grid>
        <Grid item xs={12} className='header-substyle'>
          <span> 
            {id === "new" ? "new/" : mode + " /"} 
          </span> 
          {acronym}
        </Grid>
      </Container>
    </BreadcrumbsNav>
  );
}
