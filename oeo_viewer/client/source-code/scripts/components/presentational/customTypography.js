// SPDX-FileCopyrightText: 2025 Adel Memariani <memarian@haskell2go.iks.cs.ovgu.de>
//
// SPDX-License-Identifier: MIT

import React from "react";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";

import { getColors } from "../../utils";

const CssTypography = withStyles({
  root: {
    color: getColors("text")
  }
})(Typography);

export default function CustomizedTypography(props) {
  return <CssTypography variant={props.variant}> {props.text} </CssTypography>;
}
