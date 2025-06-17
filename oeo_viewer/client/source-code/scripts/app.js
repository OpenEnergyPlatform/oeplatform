// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani>
// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani>
//
// SPDX-License-Identifier: AGPL-3.0-or-later

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
