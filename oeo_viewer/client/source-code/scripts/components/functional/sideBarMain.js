import React from "react";
import { Header, Icon, Image, Menu, Segment, Sidebar } from "semantic-ui-react";
import { Button } from "semantic-ui-react";

const mainSideBar = param => {
  return (
    <Sidebar.Pushable as={Segment}>
      <Sidebar
        as={Menu}
        icon='labeled'
        animation="overlay"
        direction="left"
        vertical
        visible={param.leftMenuVisible}
        width="thin"
      >
        <Menu.Item as="a">
         <Icon name='chain' color="blue"/>
          Relation types
        </Menu.Item>
        <Menu.Item as="a">
          <Icon name='cube' color="blue"/>
          Modules
        </Menu.Item>
        <Menu.Item as="a">
          <Icon name='share square outline' color="blue"/>
          Imports
        </Menu.Item>
        <Menu.Item as="a">
          <Icon name='search' color="blue"/>
          Advanced Search
        </Menu.Item>
      </Sidebar>

      <Sidebar
        as={Menu}
        animation="overlay"
        direction="right"
        vertical
        visible={param.rightMenuVisible}
        width="thin"
      >
        <Menu.Item as="a">Settings</Menu.Item>
        <Menu.Item as="a">About</Menu.Item>
        <Menu.Item as="a">Info</Menu.Item>
      </Sidebar>

      <Sidebar
        as={Menu}
        animation="overlay"
        direction="bottom"
        icon="labeled"
        vertical
        visible={param.bottomMenuVisible}
        width="thin"
      >
        <Menu.Item as="a">Home</Menu.Item>
        <Menu.Item as="a">Channels</Menu.Item>
      </Sidebar>

      <Sidebar.Pusher>
        <Segment basic>
          <div>
            <div>{param.content}</div>
          </div>
        </Segment>
      </Sidebar.Pusher>
    </Sidebar.Pushable>
  );
};

export default mainSideBar;
