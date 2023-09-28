import ReactDOM from "react-dom";
import React, { useState, useRef, useEffect } from "react";
import PropTypes from "prop-types";
import { Container, Header, List } from "semantic-ui-react";
import { Button, Divider } from "semantic-ui-react";

import App from "./app.js";

import MainSideBar from "./components/functional/sideBarMain.js";
import oepIcon from "../statics/oep.png";

import "semantic-ui-css/semantic.min.css";

function MainApp(ref) {
  const [leftSideBarStatus, setLeftSideBarstatus] = useState(false);
  const [rightSideBarStatus, setRightSideBarstatus] = useState(false);
  const [bottomSideBarStatus, setbottomSideBarstatus] = useState(false);

  function toggleLeftMenu() {
    setLeftSideBarstatus(!leftSideBarStatus);
  }

  function toggleRightMenu() {
    setRightSideBarstatus(!rightSideBarStatus);
  }

  function toggleBottomMenu() {
    setbottomSideBarstatus(!bottomSideBarStatus);
  }

  return (
      <div style={{ height: "100vh", width: "100vw" }}>
          {<App />}
      </div>
  );
}

ReactDOM.render(<MainApp />, document.getElementById("app"));
