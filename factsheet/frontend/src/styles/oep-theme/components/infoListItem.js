// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: MIT

import { Grid } from '@mui/material';
import { styled } from '@mui/material/styles';
import variables from '../variables';

const InfoListItemContainer = styled(Grid)(({ theme }) => ({
  padding: `${theme.spacing(1)} ${theme.spacing(0)}`,

  '& > :first-child span:first-of-type': {
    fontWeight: theme.typography.fontWeightBold,
    marginRight: `${theme.spacing(1)}`,
    verticalAlign: 'top'
  },
  '& > :last-child': {
    paddingTop: `${theme.spacing(0)} !important`,
    lineHeight: theme.typography.body1.lineHeight
  }
}));

const InfoListItem = (props) => {
  return <InfoListItemContainer container {...props} />;
};

export default InfoListItem;
