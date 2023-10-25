import React from 'react';
import { styled } from '@mui/system';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import palette from '../palette';

const BundleScenariosGrid = styled(Grid)({
  color: palette.text.primary
});

const LabelItem = styled('div')(({ theme }) => ({
  display: 'flex',
  flexDirection: 'row',
  alignItems: 'center',
  height: '100%',

  '& span:first-of-type': {
    paddingRight: theme.spacing(1),
    fontWeight: theme.typography.fontWeightBold
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
  renderField,
  showTooltip = true,
  linkText = "More info from Open Energy Ontology (OEO)..."
}) => {
  return (
    <BundleScenariosGrid item xs={12}>
      <Grid container>
        <Grid item xs={2}>
          <LabelItem>
            <span>{spanValue}</span>
            {showTooltip && TooltipComponent && (
            <span>
              <TooltipComponent
                title={
                  <React.Fragment>
                    <Typography color="inherit" variant="subtitle1">
                      {tooltipText}
                      <br />
                      <a href={hrefLink}>{linkText}</a>
                    </Typography>
                  </React.Fragment>
                }
              >
                <InfoOutlinedIcon sx={{ color: '#708696' }} />
              </TooltipComponent>
            </span>
            )}
          </LabelItem>
        </Grid>
        <Grid item xs={10}>
          {renderField()}
        </Grid>
      </Grid>
    </BundleScenariosGrid>
  );
};

export default BundleScenariosGridItem;
