import React from 'react';
import { styled } from '@mui/system';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

const LabelItem = styled('div')(({ theme }) => ({
  display: 'flex',
  flexDirection: 'row',
  alignItems: 'center',
  height: '100%',

  '& span:first-of-type': {
    paddingRight: theme.spacing(1)
  },
  '& svg': {
    transform: 'translateY(3px)'
  }
}));

const BundleScenariosGridItem = ({
  spanValue,
  tooltipText,
  hrefLink,
  TooltipComponent,
  renderField
}) => {
  return (
    <Grid item xs={12}>
      <Grid container>
        <Grid item xs={2}>
          <LabelItem>
            <span>{spanValue}</span>
            <span>
              <TooltipComponent
                title={
                  <React.Fragment>
                    <Typography color="inherit" variant="subtitle1">
                      {tooltipText}
                      <br />
                      <a href={hrefLink}>More info...</a>
                    </Typography>
                  </React.Fragment>
                }
              >
                <InfoOutlinedIcon sx={{ color: '#708696' }}/>
              </TooltipComponent>
            </span>
          </LabelItem>
        </Grid>
        <Grid item xs={10}>
          {renderField()}
        </Grid>
      </Grid>
    </Grid>
  );
};

export default BundleScenariosGridItem;
