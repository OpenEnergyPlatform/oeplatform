import React, { Component } from "react";

import BottomNavigation from "@material-ui/core/BottomNavigation";
import BottomNavigationAction from "@material-ui/core/BottomNavigationAction";
import HistoryIcon from "@material-ui/icons/History";
import CloudUploadIcon from "@material-ui/icons/CloudUpload";
import FilterTiltShiftIcon from "@material-ui/icons/FilterTiltShift";
import SettingsIcon from "@material-ui/icons/Settings";
import SpriteText from "three-spritetext";
import CustomBottomNavigation from "../presentational/customButtomNavigation";
import CustomDialog from "../presentational/customDialog";
import CustomTabs from "../presentational/customTabs";
import AutoGrid from "../presentational/grid";
import Layout from "./layout";

import { getColors } from "../../utils";

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

  renderButtomNav() {
    return (
      <CustomBottomNavigation
        elements={[
          { label: "Load", icon: <CloudUploadIcon /> },
          { label: "Constraint", icon: <FilterTiltShiftIcon /> },
          { label: "Settings", icon: <SettingsIcon /> },
          { label: "History", icon: <HistoryIcon /> }
        ]}
        handler={this.bottomNavigatorHandler}
        value={this.state.currentNavSelection}
      />
    );
  }
  render() {
    return (
      <div>
        <AutoGrid centerContent={<Layout />} />
        <CustomDialog
          handleDialogOpen={this.handleSettingDialogOpen}
          handleDialogClose={this.handleSettingDialogClose}
          open={this.state.openSettingDialog}
          content={<CustomTabs />}
        />
      </div>
    );
  }
}

export default PlayGround;
