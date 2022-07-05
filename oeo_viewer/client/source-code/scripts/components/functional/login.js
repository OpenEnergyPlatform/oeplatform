import React, { Component } from "react";
import "babel-polyfill";
import { styled } from "@material-ui/styles";
import Typography from "@material-ui/core/Typography";
import Box from "@material-ui/core/Box";
import { BrowserRouter as Router, Route, Link } from "react-router-dom";

import styledComponent from "styled-components";

import CustomTextField from "../presentational/customTextField";
import CustomTypography from "../presentational/customTypography";
import CustomSubmitButton from "../presentational/customSubmitButton";

import mainLogo from "../../../statics/network.svg";

const SectionContainer = styledComponent.div`
  display: flex;
  flex-direction: column;
  padding: 10px;
  align-items: center;
`;

class Login extends Component {
  state = {
    response: "",
    userName: "",
    password: "",
    responseToPost: ""
  };

  componentDidMount() {
    this.callApi()
      .then(res => this.setState({ response: res.express }))
      .catch(err => console.log(err));
  }

  callApi = async () => {
    const response = await fetch("/api/hello");
    const body = await response.json();
    if (response.status !== 200) throw Error(body.message);

    return body;
  };

  handleSubmit = async e => {
    e.preventDefault();
    const response = await fetch("/api/world", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ userName: this.state.userName })
    });
    const body = await response.text();

    this.setState({ responseToPost: body });
  };

  render() {
    return (
      <div>
        <SectionContainer>
          <img
            src={mainLogo}
            alt="fireSpot"
            style={{ width: "75px", padding: "10px" }}
          />
          <CustomTypography variant="h5" text={this.state.response} />
          <CustomTypography variant="subtitle2" text={"DKE-OVGU"} />
          <Box component="span" m={5} />
          <form onSubmit={this.handleSubmit}>
            <CustomTextField
              id="outlined-userName"
              label="User-name"
              value={this.state.userName}
              onChange={e => this.setState({ userName: e.target.value })}
              margin="normal"
              variant="outlined"
            />
            <CustomTextField
              id="outlined-pass"
              label="Password"
              value={this.state.password}
              onChange={e => this.setState({ password: e.target.value })}
              margin="normal"
              variant="outlined"
              type="password"
            />
            <CustomSubmitButton caption={"Login"} type={"submit"} />
          </form>
          <CustomTypography
            variant="subtitle1"
            text={this.state.responseToPost}
          />
          <CustomTypography
            variant="subtitle2"
            text={"All rights reserved - OVGU "}
          />
          <Link to="/main">Main</Link>
        </SectionContainer>
      </div>
    );
  }
}

export default Login;
