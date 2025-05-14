// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien>
//
// SPDX-License-Identifier: MIT

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
  alignItems: 'baseline',
  transform: 'translateY(0.5rem)',
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
  labelGridSize = 2,
  fieldGridSize = 10,
  spanValue,
  tooltipText,
  hrefLink,
  TooltipComponent,
  customSpan = null,
  renderField,
  showTooltip = true,
  linkText = "More info from Open Energy Ontology (OEO)..."
}) => {
  return (
    <BundleScenariosGrid item xs={12}>
      <Typography variant="body2">
        <Grid container>
          <Grid item xs={labelGridSize}>
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
              {customSpan}
            </LabelItem>
          </Grid>
          <Grid item xs={fieldGridSize}>
            {typeof renderField === 'function' ? renderField() : null}
          </Grid>
        </Grid>
      </Typography>
    </BundleScenariosGrid>
  );
};

export default BundleScenariosGridItem;
