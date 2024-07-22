import React, { Component } from "react";
import Layout from "./layout";


class PlayGround extends Component {
  constructor(props) {
    super(props);
  }

  state = {
    currentNavSelection: "",
    openSettingDialog: false
  };

  bottomNavigatorHandler = (event, newValue) => {
    this.setState({ currentNavSelection: newValue });
    if (newValue === 2) {
      this.setState({ openSettingDialog: true });
    }
  };

  handleSettingDialogOpen = status => {
    this.setState({ openSettingDialog: true });
  };
  handleSettingDialogClose = status => {
    this.setState({ openSettingDialog: false });
  };

  render() {
    return (
        <Layout />
    );
  }
}

export default PlayGround;
