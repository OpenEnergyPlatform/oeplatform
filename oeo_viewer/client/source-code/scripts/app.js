// SPDX-FileCopyrightText: 2025 Adel Memariani <adel.memariani@ovgu.de>
// SPDX-FileCopyrightText: 2025 Adel Memariani <memarian@haskell2go.iks.cs.ovgu.de>
//
// SPDX-License-Identifier: MIT

import React, { Component } from "react";
import Login from "./components/functional/login";
import PlayGround from "./components/functional/playGround";
import "../styles/index.scss";

class App extends Component {
  render() {
    return (
      <PlayGround />
    );
  }
}

export default App;
