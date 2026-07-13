// ComparisonBoardMain.tsx
import React, { useState, useEffect } from "react";
import Grid from "@mui/material/Grid";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { Link } from "react-router-dom";
import Button from "@mui/material/Button";
import axios from "axios";
import conf from "../conf.json";
import Container from "@mui/material/Container";
import Toolbar from "@mui/material/Toolbar";
import { Tooltip } from "@mui/material";
import ArrowRightIcon from "@mui/icons-material/ArrowRight";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import ManageSearchIcon from "@mui/icons-material/ManageSearch";
import EqualizerIcon from "@mui/icons-material/Equalizer";
import BreadcrumbsNavGrid from "../styles/oep-theme/components/breadcrumbsNavigation.jsx";

// Import our new sub-components
import QualitativeView from "./comparison/qualitativeView.jsx";
import QuantitativeView from "./comparison/quantitativeView.jsx";
// PROTOTYPE (wayfinder WF-07): multi-source selection variants on the
// Registry (beta) tab, ?variant=A|B|C|0. Falls back to RegistryComparison in
// production builds; remove with the prototype.
import MultiSourcePrototype from "./comparison/prototype_multisource/MultiSourcePrototype.jsx";
// PROTOTYPE (WF-07 reaction round 6): content for the previously dead
// "How it works?" button — when the prototype folds into the real view,
// keep the dialog and re-home it.
import HowItWorksDialog from "./comparison/prototype_multisource/HowItWorks.jsx";

const ComparisonBoardMain = ({ params }) => {
  const [scenarios, setScenarios] = useState([]);
  const [alignment, setAlignment] = useState("Qualitative");
  const [howOpen, setHowOpen] = useState(false);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const scenarios_uid_json = JSON.stringify(params);
        const { data } = await axios.get(
          conf.toep + `scenario-bundles/get_scenarios/`,
          {
            params: { scenarios_uid: scenarios_uid_json },
          }
        );
        setScenarios(data);
      } catch (error) {
        console.error("Failed to fetch scenarios", error);
      }
    };
    fetchInitialData();
  }, [params]);

  return (
    scenarios.length !== 0 && (
      <Grid
        container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
      >
        <BreadcrumbsNavGrid subheaderContent="Comparison" />

        {/* PROTOTYPE (WF-07 reaction, item 1): the Registry workbench needs
            the full viewport width — the lg2 container blocks it. */}
        <Container maxWidth={alignment === "Registry" ? false : "lg2"}>
          {/* TOP TOOLBAR */}
          <Toolbar sx={{ marginBottom: (theme) => theme.spacing(4) }}>
            <Grid container justifyContent="space-between" spacing={2}>
              <Grid item xs={12} md={4}>
                <Tooltip title="Back to main page">
                  <Link to={`scenario-bundles/main`}>
                    <Button variant="outlined" size="small" sx={{ mr: 1 }}>
                      <ArrowBackIcon />
                    </Button>
                  </Link>
                </Tooltip>
              </Grid>
              <Grid item xs={6} md={4}></Grid>
              <Grid item xs={6} md={4}>
                <Button
                  color="primary"
                  variant="text"
                  size="small"
                  startIcon={<ArrowRightIcon />}
                  onClick={() => setHowOpen(true)}
                >
                  How it works?
                </Button>
                <HowItWorksDialog
                  open={howOpen}
                  onClose={() => setHowOpen(false)}
                  alignment={alignment}
                />
              </Grid>
              <Grid item xs={4}></Grid>
              <Grid item xs={6}>
                <ToggleButtonGroup
                  color="primary"
                  value={alignment}
                  exclusive
                  onChange={(e, newAlignment) =>
                    newAlignment && setAlignment(newAlignment)
                  }
                  size="large"
                >
                  <ToggleButton style={{ width: "250px" }} value="Qualitative">
                    <ManageSearchIcon /> Qualitative
                  </ToggleButton>
                  <ToggleButton style={{ width: "250px" }} value="Quantitative">
                    <EqualizerIcon /> Quantitative
                  </ToggleButton>
                  <ToggleButton style={{ width: "250px" }} value="Registry">
                    <EqualizerIcon /> Registry (beta)
                  </ToggleButton>
                </ToggleButtonGroup>
              </Grid>
              <Grid item xs={2}></Grid>
            </Grid>
          </Toolbar>

          {/* VIEW ROUTING */}
          {alignment === "Qualitative" && (
            <QualitativeView scenarios={scenarios} />
          )}
          {alignment === "Quantitative" && (
            <QuantitativeView scenarios={scenarios} />
          )}
          {alignment === "Registry" && <MultiSourcePrototype />}
        </Container>
      </Grid>
    )
  );
};

export default ComparisonBoardMain;
