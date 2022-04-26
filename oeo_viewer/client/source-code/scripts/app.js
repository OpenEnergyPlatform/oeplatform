import React, { Component } from "react";
import ReactDOM from "react-dom";
import {
  BrowserRouter as Router,
  Route,
  Link,
  withRouter
} from "react-router-dom";
import AutoGrid from "./components/presentational/grid";
import Login from "./components/functional/login";
import PlayGround from "./components/functional/playGround";
import "../styles/index.scss";

const header = () => {
  return (
    <ul>
      <li>
        <Link to="/about">About</Link>
      </li>
      <li>
        <Link to="/login">Login</Link>
      </li>
      <li>
        <Link to="/main">Main</Link>
      </li>
      <li>
        <Link to="/tree">Tree View</Link>
      </li>
    </ul>
  );
};

const login = () => {
  return <AutoGrid centerContent={<Login />} />;
};

const about = () => {
  return "About";
};

class App extends Component {
  render() {
    return (
      <PlayGround />
    );
  }
}

export default App;
