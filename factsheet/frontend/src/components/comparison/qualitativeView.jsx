// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useState } from "react";
import Grid from "@mui/material/Grid";
import FormGroup from "@mui/material/FormGroup";
import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";
import OptionBox from "../../styles/oep-theme/components/optionBox";
import ComparisonBoardItems from "../comparisonBoardItems.jsx";
import {
  datasetHref,
  datasetDisplay,
} from "../scenarioBundleUtilityComponents/comparisonUtils";

const Criteria = [
  "Scenario abstract",
  "Study name",
  "Study abstract",
  "Study descriptors",
  "Scenario types",
  "Regions",
  "Interacting regions",
  "Scenario years",
  "Input datasets",
  "Output datasets",
];

const QualitativeView = ({ scenarios }) => {
  const [selectedCriteria, setSelectedCriteria] = useState([
    "Study descriptors",
    "Scenario types",
    "Study name",
  ]);

  const handleCriteria = (event) => {
    if (event.target.checked) {
      if (!selectedCriteria.includes(event.target.name)) {
        setSelectedCriteria([...selectedCriteria, event.target.name]);
      }
    } else {
      const filteredCriteria = selectedCriteria.filter(
        (i) => i !== event.target.name
      );
      setSelectedCriteria(filteredCriteria);
    }
  };

  return (
    <Grid item xs={12}>
      <OptionBox>
        <h2>Criteria</h2>
        <FormGroup>
          <div>
            {Criteria.map((item) => (
              <FormControlLabel
                key={item}
                control={<Checkbox size="medium" color="primary" />}
                checked={selectedCriteria.includes(item)}
                onChange={handleCriteria}
                label={item}
                name={item}
              />
            ))}
          </div>
        </FormGroup>
      </OptionBox>
      <ComparisonBoardItems
        key={`qualitative-${scenarios.map((s) => s.data.uid).join(",")}`}
        elements={scenarios}
        c_aspects={selectedCriteria}
        datasetHref={datasetHref}
        datasetDisplay={datasetDisplay}
      />
    </Grid>
  );
};

export default QualitativeView;
