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
