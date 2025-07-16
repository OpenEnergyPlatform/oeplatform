// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

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

  '& .header-style h1': {
    paddingLeft: variables.spacing[2],
    color: palette.text.primary,
    fontSize: variables.fontSize.lg,
    fontWeight: theme.typography.fontWeightRegular
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

export default function BreadcrumbsNavGrid({ acronym, id, mode, subheaderContent }) {
  return (
    <BreadcrumbsNav container>
      <Container maxWidth="false">
        <Grid item xs={12} className='header-style'>
          <span>
            <ListAltOutlinedIcon />
          </span>
          <h1>Scenario Bundles</h1>
        </Grid>
        <Grid item xs={12} className='header-substyle'>
          {subheaderContent ? (
            <span>{subheaderContent}</span>
          ) : (
            <span>
              {id === "new" ? "new/" : mode + " /"}
            </span>
          )}
          {acronym}
        </Grid>
      </Container>
    </BreadcrumbsNav>
  );
}
