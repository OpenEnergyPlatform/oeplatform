import React from "react";
import { makeStyles } from "@material-ui/core/styles";
import BottomNavigation from "@material-ui/core/BottomNavigation";
import BottomNavigationAction from "@material-ui/core/BottomNavigationAction";

const useStyles = makeStyles({
  root: {
    width: 500
  }
});

export default function CustomBottomNavigation(props) {
  const classes = useStyles();
  const { elements, handler, value } = props;

  const items = [];
  for (const [index, element] of elements.entries()) {
    items.push(
      <BottomNavigationAction
        key={index}
        label={element.label}
        icon={element.icon}
      />
    );
  }

  return (
    <BottomNavigation
      value={value}
      onChange={handler}
      showLabels
      className={classes.root}
    >
      {items}
    </BottomNavigation>
  );
}
