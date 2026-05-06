// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useState, useEffect } from "react";
import ReactECharts from "echarts-for-react";
import Grid from "@mui/material/Grid";
import Button from "@mui/material/Button";
import axios from "axios";
import conf from "../../conf.json";
import Checkbox from "@mui/material/Checkbox";
import { Box, Tooltip } from "@mui/material";
import Chip from "@mui/material/Chip";
import Typography from "@mui/material/Typography";
import FormControl from "@mui/material/FormControl";
import SendIcon from "@mui/icons-material/Send";
import LinearProgress from "@mui/material/LinearProgress";
import Autocomplete from "@mui/material/Autocomplete"; // <-- NEW
import TextField from "@mui/material/TextField"; // <-- NEW
import Tabs, { tabsClasses } from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Snackbar from "@mui/material/Snackbar";
import Alert from "@mui/material/Alert";
import variables from "../../styles/oep-theme/variables.js";
import CSRFToken from "../csrfToken.js";

import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Paper from "@mui/material/Paper";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import BarChartIcon from "@mui/icons-material/BarChart";
import TableViewIcon from "@mui/icons-material/TableView";
import IconButton from "@mui/material/IconButton";
import DownloadIcon from "@mui/icons-material/Download";

import { findSharedElements } from "../scenarioBundleUtilityComponents/comparisonUtils";

const oepBlue = "#005a91";

const scientificPalette = [
  "#1f77b4",
  "#ff7f0e",
  "#2ca02c",
  "#d62728",
  "#9467bd",
  "#8c564b",
  "#e377c2",
  "#7f7f7f",
  "#bcbd22",
  "#17becf",
  "#aec7e8",
  "#ffbb78",
  "#98df8a",
  "#ff9896",
  "#c5b0d5",
];

const getAcronym = (str) => {
  if (!str) return "";
  let cleanStr = str.replace(/\([^)]*\)/g, "").trim();
  const words = cleanStr.split(/[\s\-_,:]+/).filter((w) => w.length > 0);
  if (words.length === 0) return str.substring(0, 3).toUpperCase();
  if (words.length === 1) return words[0].substring(0, 3).toUpperCase();
  return words
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .substring(0, 4);
};

const termCache = {};

const resolveTermFromTIB = async (uri) => {
  if (termCache[uri]) return termCache[uri];
  const shortForm = uri.split("/").pop().split(":").pop();
  const officialIri = `https://openenergyplatform.org/ontology/oeo/${shortForm}`;
  const encodedIri = encodeURIComponent(officialIri);
  const baseUrl =
    import.meta.env.VITE_TSS_API_BASE?.replace(/\/$/, "") ||
    "https://api.terminology.tib.eu/api";
  const ontology = import.meta.env.VITE_TSS_DEFAULT_ONTOLOGY || "oeo";

  const fetchFromEndpoint = async (endpoint) => {
    try {
      const response = await axios.get(
        `${baseUrl}/ontologies/${ontology}/${endpoint}?iri=${encodedIri}`
      );
      if (response.data && response.data._embedded) {
        const items = response.data._embedded[endpoint];
        if (items && items.length > 0) {
          const item = items[0];
          return {
            label: item.label,
            description:
              item.description && item.description.length > 0
                ? item.description.join(" ")
                : "No official definition provided in the ontology.",
            type: endpoint,
          };
        }
      }
      return null;
    } catch (error) {
      return null;
    }
  };

  let termInfo = await fetchFromEndpoint("terms");
  if (!termInfo) termInfo = await fetchFromEndpoint("individuals");
  if (!termInfo) termInfo = await fetchFromEndpoint("properties");

  if (termInfo) {
    termCache[uri] = termInfo;
    return termInfo;
  } else {
    const fallback = {
      label: shortForm,
      description: "Term not found in Terminology Service.",
      type: "unknown",
    };
    termCache[uri] = fallback;
    return fallback;
  }
};

const SemanticChip = ({ textLabel, dictionary }) => {
  const uri = Object.keys(dictionary).find((k) => dictionary[k] === textLabel);
  const info = termCache[uri] || { description: "Loading..." };
  return (
    <Tooltip
      title={
        <Typography variant="body2" sx={{ p: 0.5 }}>
          {info.description}
        </Typography>
      }
      arrow
      placement="top"
      componentsProps={{
        tooltip: {
          sx: {
            bgcolor: "background.paper",
            color: "text.primary",
            boxShadow: 2,
            border: "1px solid",
            borderColor: "divider",
            "& .MuiTooltip-arrow": {
              color: "background.paper",
              "&::before": { border: "1px solid", borderColor: "divider" },
            },
          },
        },
      }}
    >
      <Chip
        label={textLabel}
        size="small"
        variant="outlined"
        sx={{
          cursor: "help",
          fontWeight: "bold",
          borderColor: oepBlue,
          color: oepBlue,
          bgcolor: "background.paper",
        }}
      />
    </Tooltip>
  );
};

// --- NEW: Custom Dropdown Component with Autocomplete, Search, & Select All ---
const FilterDropdown = ({ label, options, selectedValues, onChange }) => {
  const isAllSelected =
    options.length > 0 && selectedValues.length === options.length;
  const isIndeterminate =
    selectedValues.length > 0 && selectedValues.length < options.length;

  return (
    <Autocomplete
      multiple
      limitTags={2} // Limits chips shown when un-focused to save vertical space
      size="small"
      options={["[Select All]", ...options]}
      disableCloseOnSelect
      getOptionLabel={(option) =>
        option === "[Select All]" ? "Select All" : option
      }
      value={selectedValues}
      onChange={(event, newValue) => {
        if (newValue.includes("[Select All]")) {
          if (isAllSelected) {
            onChange([]); // Reset all
          } else {
            onChange([...options]); // Select all
          }
        } else {
          onChange(newValue);
        }
      }}
      renderOption={(props, option) => {
        const { key, ...otherProps } = props;

        // Special render for the 'Select All' toggle
        if (option === "[Select All]") {
          return (
            <li
              key={key}
              {...otherProps}
              style={{ borderBottom: "1px solid #ccc", fontWeight: "bold" }}
            >
              <Checkbox
                style={{ marginRight: 8 }}
                checked={isAllSelected}
                indeterminate={isIndeterminate}
              />
              Select All
            </li>
          );
        }

        // Standard render for normal options
        return (
          <li key={key} {...otherProps}>
            <Checkbox
              style={{ marginRight: 8 }}
              checked={selectedValues.includes(option)}
            />
            {option}
          </li>
        );
      }}
      renderInput={(params) => (
        <TextField {...params} label={label} placeholder="Search..." />
      )}
      sx={{
        m: 1,
        width: { xs: "90%", md: "31%" },
        bgcolor: "background.paper",
      }}
    />
  );
};

const QuantitativeView = ({ scenarios }) => {
  const [outputTableNames, setoutputTableNames] = useState([]);
  const [scenariosInTables, setScenariosInTables] = useState([]);
  const [categoryNames, setCategoryNames] = useState([]);
  const [gasesNames, setGasesNames] = useState([]);
  const [countryNames, setCountryNames] = useState([]);

  const [scenarioDict, setScenarioDict] = useState({});
  const [categoryDict, setCategoryDict] = useState({});
  const [gasDict, setGasDict] = useState({});

  const [selectedOutputDatasets, setSelectedOutputDatasets] = useState([]);
  const [selectedScenarios, setSelectedScenarios] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [selectedGas, setSelectedGas] = useState([]);
  const [selectedCountries, setSelectedCountries] = useState([]);

  const [sparqOutput, setSparqlOutput] = useState([]);
  const [scenarioYear, setScenarioYear] = useState([]);
  const [scenarioYears, setScenarioYears] = useState([]);
  const [units, SetUnits] = useState([]);

  const [echartsOption, setEchartsOption] = useState({});
  const [tableData, setTableData] = useState({ dimensions: [], source: [] });
  const [viewMode, setViewMode] = useState("chart");

  const [loading, setLoading] = useState(false);
  const [showChart, setShowChart] = useState(false);
  const [showTitle, setShowTitle] = useState(false);
  const [openEmptyResultDialog, setOpenEmptyResultDialog] = useState(false);

  useEffect(() => {
    if (scenarios && scenarios.length > 0) {
      const ScenariosOutputTableNames = scenarios.map((obj) =>
        (obj?.data?.output_datasets || [])
          .filter((ds) => ds?.kind === "oep_table" && ds?.table_name)
          .map((ds) => ds.table_name)
      );
      setoutputTableNames(
        Array.from(new Set(ScenariosOutputTableNames.flat()))
      );
    }
  }, [scenarios]);

  useEffect(() => {
    setShowTitle(false);
    sendGetScenariosQuery();
    sendGetCategoriesQuery();
    sendGetGasQuery();
    sendGetCountriesQuery();
    setSelectedCategories([]);
    setSelectedScenarios([]);
    setSelectedGas([]);
    setSelectedCountries([]);
  }, [selectedOutputDatasets]);

  // Cleaned up onChange handlers for the new Autocomplete logic
  const handleOutputDatasetsChange = (vals) => setSelectedOutputDatasets(vals);
  const handleScenariosChange = (vals) => setSelectedScenarios(vals);
  const handleCategoriesChange = (vals) => setSelectedCategories(vals);
  const handleGasChange = (vals) => setSelectedGas(vals);
  const handleCountriesChange = (vals) => setSelectedCountries(vals);

  const handleViewModeChange = (e, newMode) => {
    if (newMode !== null) setViewMode(newMode);
  };
  const handleEmptyResultMessageClose = (event, reason) => {
    if (reason === "clickaway") return;
    setOpenEmptyResultDialog(false);
  };

  const handleDownloadCSV = () => {
    if (!tableData.source || tableData.source.length === 0) return;
    const unitStr = units.length > 0 ? units[0].replace(/\r/g, " ") : "";
    const gasHeaders = selectedGas;
    const headers = [
      "Country",
      "Table",
      "Scenario",
      "Sector",
      ...gasHeaders,
      "Unit",
    ];
    let csvContent = headers.map((h) => `"${h}"`).join(",") + "\n";

    tableData.source
      .filter((row) => !row.isSpacer)
      .forEach((row) => {
        let rowValues = [
          `"${row.Country}"`,
          `"${row.Table || ""}"`,
          `"${row.Scenario || ""}"`,
          `"${row.Sector || ""}"`,
        ];
        gasHeaders.forEach((gas) => {
          let val = row[gas];
          if (typeof val === "number") val = val.toFixed(2);
          else if (!val) val = 0;
          rowValues.push(`"${val}"`);
        });
        rowValues.push(`"${unitStr}"`);
        csvContent += rowValues.join(",") + "\n";
      });

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `scenario_data_${scenarioYear[0] || "export"}.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const sendGetCountriesQuery = async () => {
    setLoading(true);
    const data_tabels = selectedOutputDatasets.map((elem) => '"' + elem + '"');
    const query = `PREFIX oeo: <https://openenergyplatform.org/ontology/oeo/> SELECT DISTINCT ?country_code ?table_name WHERE { ?s oeo:OEO_00020221 ?country_code . ?s oeo:OEO_00000504 ?table_name . ${data_tabels.length > 0 ? `FILTER(?table_name IN ( ${data_tabels.join(", ")} ) ).` : ""}}`;
    try {
      const response = await axios.post(conf.obdi, query, {
        headers: {
          "X-CSRFToken": CSRFToken(),
          Accept: "application/sparql-results+json",
          "Content-Type": "application/sparql-query",
        },
      });
      const bindings = response.data.results.bindings;
      const countriesByTable = bindings.reduce((acc, obj) => {
        const country = obj.country_code.value.split("/").pop();
        const tableName = obj.table_name.value;
        if (!acc[tableName]) acc[tableName] = new Set();
        acc[tableName].add(country);
        return acc;
      }, {});
      const allTableNames = Object.values(countriesByTable);
      let commonCountries = new Set();
      if (allTableNames.length > 0)
        commonCountries = allTableNames.reduce(
          (acc, set) => new Set([...acc].filter((c) => set.has(c))),
          allTableNames[0]
        );
      setCountryNames(Array.from(commonCountries).sort());
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const sendGetScenariosQuery = async () => {
    setLoading(true);
    const query = `PREFIX oeo: <https://openenergyplatform.org/ontology/oeo/> SELECT DISTINCT ?scenario WHERE { ?s oeo:OEO_00020226 ?scenario . }`;
    try {
      const response = await axios.post(conf.obdi, query, {
        headers: {
          "X-CSRFToken": CSRFToken(),
          Accept: "application/sparql-results+json",
          "Content-Type": "application/sparql-query",
        },
      });
      const uniqueUris = [
        ...new Set(
          response.data.results.bindings.map((obj) => obj.scenario.value)
        ),
      ];
      const newDict = {};
      const labels = [];
      for (const uri of uniqueUris) {
        const termInfo = await resolveTermFromTIB(uri);
        newDict[uri] = termInfo.label;
        labels.push(termInfo.label);
      }
      setScenarioDict(newDict);
      setScenariosInTables(labels.sort());
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const sendGetCategoriesQuery = async () => {
    setLoading(true);
    const data_tabels = selectedOutputDatasets.map((elem) => '"' + elem + '"');
    const query = `PREFIX oeo: <https://openenergyplatform.org/ontology/oeo/> SELECT DISTINCT ?category ?table_name WHERE { ?s oeo:has_sector_division ?category . ?s oeo:OEO_00000504 ?table_name . ${data_tabels.length > 0 ? `FILTER(?table_name IN ( ${data_tabels.join(", ")} ) ).` : ""}}`;
    try {
      const response = await axios.post(conf.obdi, query, {
        headers: {
          "X-CSRFToken": CSRFToken(),
          Accept: "application/sparql-results+json",
          "Content-Type": "application/sparql-query",
        },
      });
      const categoriesObj = response.data.results.bindings;
      const categoriesByTable = categoriesObj.reduce((acc, obj) => {
        const category = obj.category.value;
        const tableName = obj.table_name.value;
        if (!acc[tableName]) acc[tableName] = new Set();
        acc[tableName].add(category);
        return acc;
      }, {});
      const allTableNames = Object.values(categoriesByTable);
      let commonCategories = new Set();
      if (allTableNames.length > 0)
        commonCategories = allTableNames.reduce((acc, categoriesSet) => {
          return new Set(
            [...acc].filter((category) => categoriesSet.has(category))
          );
        }, allTableNames[0]);
      const uniqueUris = Array.from(commonCategories);
      const newDict = {};
      const labels = [];
      for (const uri of uniqueUris) {
        const termInfo = await resolveTermFromTIB(uri);
        newDict[uri] = termInfo.label;
        labels.push(termInfo.label);
      }
      setCategoryDict(newDict);
      setCategoryNames(labels.sort());
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const sendGetGasQuery = async () => {
    setLoading(true);
    const data_tabels = selectedOutputDatasets.map((elem) => '"' + elem + '"');
    const query = `PREFIX oeo: <https://openenergyplatform.org/ontology/oeo/> SELECT DISTINCT ?gas ?table_name WHERE { ?s oeo:OEO_00010121 ?gas . ?s oeo:OEO_00000504 ?table_name . ${data_tabels.length > 0 ? `FILTER(?table_name IN ( ${data_tabels.join(", ")} ) ).` : ""}}`;
    try {
      const response = await axios.post(conf.obdi, query, {
        headers: {
          "X-CSRFToken": CSRFToken(),
          Accept: "application/sparql-results+json",
          "Content-Type": "application/sparql-query",
        },
      });
      const gasesObj = response.data.results.bindings;
      const gasesByTable = gasesObj.reduce((acc, obj) => {
        const gas = obj.gas.value;
        const tableName = obj.table_name.value;
        if (!acc[tableName]) acc[tableName] = new Set();
        acc[tableName].add(gas);
        return acc;
      }, {});
      const allTableNames = Object.values(gasesByTable);
      let commonGases = new Set();
      if (allTableNames.length > 0)
        commonGases = allTableNames.reduce((acc, gasesSet) => {
          return new Set([...acc].filter((gas) => gasesSet.has(gas)));
        }, allTableNames[0]);
      const uniqueUris = Array.from(commonGases);
      const newDict = {};
      const labels = [];
      for (const uri of uniqueUris) {
        const termInfo = await resolveTermFromTIB(uri);
        newDict[uri] = termInfo.label;
        labels.push(termInfo.label);
      }
      setGasDict(newDict);
      setGasesNames(labels.sort());
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleYearChange = (event, newValue, index, dataOverride = null) => {
    setLoading(true);
    const dataToUse = dataOverride || sparqOutput;

    if (dataToUse.length !== 0) {
      const extractedUnits = [
        ...new Set(dataToUse.map((obj) => obj.unit?.value).filter(Boolean)),
      ];
      if (extractedUnits.length > 0) SetUnits(extractedUnits);
      const displayUnit =
        extractedUnits.length > 0 ? extractedUnits[0].replace(/\r/g, " ") : "";

      const distinctTables = [
        ...new Set(dataToUse.map((obj) => obj.table_name.value)),
      ];
      const isMultipleTables = distinctTables.length > 1;
      const filtered_output = dataToUse.filter(
        (item) => item.year.value == newValue
      );

      const countryTotals = {};
      const globalUniqueCountries = [
        ...new Set(
          dataToUse.map((item) => item.country_code.value.split("/").pop())
        ),
      ];
      globalUniqueCountries.forEach((country) => {
        countryTotals[country] = filtered_output
          .filter((obj) => obj.country_code?.value.split("/").pop() === country)
          .reduce((sum, r) => sum + parseFloat(r.value.value), 0);
      });
      globalUniqueCountries.sort((a, b) => countryTotals[b] - countryTotals[a]);

      let distinctYears = isMultipleTables
        ? distinctTables.map((tbl) => [
            ...new Set(
              dataToUse
                .filter((el) => el.table_name.value === tbl)
                .map((obj) => obj.year.value)
            ),
          ])
        : [...new Set(dataToUse.map((obj) => obj.year.value))].sort();
      const sharedYears = isMultipleTables
        ? findSharedElements(distinctYears).sort()
        : distinctYears;
      const newScenarioYears = [...scenarioYears];
      newScenarioYears[index] = sharedYears;
      setScenarioYears(newScenarioYears);
      const newScenarioYear = [...scenarioYear];
      newScenarioYear[index] = newValue;
      setScenarioYear(newScenarioYear);

      const dimensions = ["Country_Axis", ...selectedGas];
      const seriesConfig = [];

      selectedGas.forEach((gasString, i) => {
        seriesConfig.push({
          type: "bar",
          stack: "total",
          name: gasString,
          itemStyle: { color: scientificPalette[i % scientificPalette.length] },
          barCategoryGap: "5%",
          label: {
            show: true,
            position: "inside",
            formatter: (params) =>
              typeof params.value[gasString] === "number" &&
              params.value[gasString] >= 1
                ? Math.round(params.value[gasString])
                : "",
          },
        });
      });

      const source = [];
      let spacerCount = 0;
      const loopTables = isMultipleTables ? distinctTables : [null];

      const barsPerGroup =
        loopTables.length *
        selectedScenarios.length *
        selectedCategories.length;
      const middleIndex = Math.floor((barsPerGroup - 1) / 2);

      globalUniqueCountries.forEach((country, cIdx) => {
        let barIndex = 0;

        loopTables.forEach((tableName) => {
          selectedScenarios.forEach((scenarioString) => {
            selectedCategories.forEach((catString) => {
              let labelParts = [];
              if (isMultipleTables) labelParts.push(getAcronym(tableName));
              if (selectedScenarios.length > 1)
                labelParts.push(getAcronym(scenarioString));
              if (selectedCategories.length > 1)
                labelParts.push(getAcronym(catString));

              let subLabel = labelParts.join("-");
              let uniqueAxisLabel = country + "\u200B".repeat(spacerCount++);

              let row = {
                Country_Axis: uniqueAxisLabel,
                Country: country,
                Table: tableName,
                Scenario: scenarioString,
                Sector: catString,
                AcronymLabel: subLabel,
                isMiddleOfGroup: barIndex === middleIndex,
                barsInGroup: barsPerGroup,
                isSpacer: false,
              };

              selectedGas.forEach((gasString) => {
                const matchingRows = filtered_output.filter(
                  (obj) =>
                    (!tableName || obj.table_name.value === tableName) &&
                    categoryDict[obj.category.value] === catString &&
                    gasDict[obj.gas.value] === gasString &&
                    scenarioDict[obj.scenario.value] === scenarioString &&
                    obj.country_code.value.split("/").pop() === country
                );
                row[gasString] = matchingRows.reduce(
                  (sum, r) => sum + parseFloat(r.value.value),
                  0
                );
              });

              source.push(row);
              barIndex++;
            });
          });
        });

        if (cIdx < globalUniqueCountries.length - 1) {
          let spacerRow = {
            Country_Axis: "\u00A0".repeat(spacerCount++),
            isSpacer: true,
          };
          selectedGas.forEach((g) => (spacerRow[g] = 0));
          source.push(spacerRow);
        }
      });

      setTableData({ dimensions, source });

      const option = {
        tooltip: {
          trigger: "axis",
          axisPointer: { type: "shadow" },
          formatter: function (params) {
            if (!params.length || params[0].data.isSpacer) return "";
            const data = params[0].data;
            let html = `<div style="padding:4px;"><strong>${data.Country}</strong><br/>`;
            if (isMultipleTables && data.Table)
              html += `<span style="font-size:11px;color:#666;">Table: ${data.Table}</span><br/>`;
            if (selectedScenarios.length > 0)
              html += `<span style="font-size:11px;color:#666;">Scenario: ${data.Scenario}</span><br/>`;
            if (selectedCategories.length > 0)
              html += `<span style="font-size:11px;color:#666;">Sector: ${data.Sector}</span><br/>`;
            html += `<hr style="margin:6px 0; border:0; border-top:1px solid #ccc;"/>`;

            let hasData = false;
            params.forEach((p) => {
              if (p.value[p.seriesName] > 0) {
                html += `${p.marker} <b>${p.seriesName}:</b> ${p.value[p.seriesName].toFixed(2)}<br/>`;
                hasData = true;
              }
            });
            if (!hasData)
              html += `<span style="font-size:11px;color:#999;">No data</span>`;
            html += `</div>`;
            return html;
          },
        },
        legend: { show: true, type: "scroll", bottom: 0 },
        dataZoom: [
          {
            type: "slider",
            show: true,
            xAxisIndex: [0],
            bottom: 30,
            height: 20,
          },
        ],
        grid: { left: "1%", right: "2%", bottom: "22%", containLabel: true },
        dataset: { dimensions, source },
        xAxis: {
          type: "category",
          axisTick: { alignWithLabel: true },
          axisLabel: {
            interval: 0,
            fontSize: 11,
            lineHeight: 16,
            formatter: function (value, index) {
              const row = source[index];
              if (!row || row.isSpacer) return "";

              if (row.barsInGroup === 1) {
                return row.AcronymLabel
                  ? `{country|${row.Country}}\n${row.AcronymLabel}`
                  : `{country|${row.Country}}`;
              } else {
                if (row.isMiddleOfGroup) {
                  return `${row.AcronymLabel}\n\n{country|${row.Country}}`;
                }
                return row.AcronymLabel;
              }
            },
            rich: {
              country: { fontWeight: "bold", fontSize: 12, color: oepBlue },
            },
          },
        },
        yAxis: {
          type: "value",
          name: displayUnit,
          nameLocation: "middle",
          nameGap: 50,
        },
        series: seriesConfig,
      };

      setEchartsOption(option);
      setLoading(false);
      setShowChart(true);
      setShowTitle(true);
    } else {
      setLoading(false);
      setShowChart(false);
      setOpenEmptyResultDialog(true);
    }
  };

  const sendQuery = async (index) => {
    setShowChart(false);
    setShowTitle(false);
    setSparqlOutput([]);
    setScenarioYears([]);
    setLoading(true);
    const data_tabels = selectedOutputDatasets.map((elem) => '"' + elem + '"');
    const formatForSparql = (uri) => {
      if (uri.startsWith("http")) return `<${uri}>`;
      if (uri.startsWith("OEO_")) return `oeo:${uri}`;
      return `"${uri}"`;
    };

    const categoriesFilter = Object.keys(categoryDict)
      .filter((uri) => selectedCategories.includes(categoryDict[uri]))
      .map(formatForSparql);
    const gasesFilter = Object.keys(gasDict)
      .filter((uri) => selectedGas.includes(gasDict[uri]))
      .map(formatForSparql);
    const scenariosFilter = Object.keys(scenarioDict)
      .filter((uri) => selectedScenarios.includes(scenarioDict[uri]))
      .map(formatForSparql);
    const countriesFilter = selectedCountries.map(
      (c) =>
        `<https://www.omg.org/spec/LCC/Countries/ISO3166-1-CountryCodes/${c}>`
    );

    const main_query = `PREFIX obo: <http://purl.obolibrary.org/obo/>
    PREFIX ou: <http://opendata.unex.es/def/ontouniversidad#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX oeo: <https://openenergyplatform.org/ontology/oeo/>
    PREFIX llc:  <https://www.omg.org/spec/LCC/Countries/ISO3166-1-CountryCodes/>
    SELECT DISTINCT ?s ?value ?country_code ?year ?category ?gas ?table_name ?unit ?scenario WHERE {
      ?s oeo:OEO_00020221 ?country_code . ?s oeo:OEO_00020224 ?year . ?s oeo:OEO_00140178 ?value . ?s oeo:OEO_00000504 ?table_name .
      ?s oeo:has_sector_division ?category . ?s oeo:OEO_00020226 ?scenario . ?s oeo:OEO_00010121 ?gas . ?s oeo:OEO_00040010 ?unit .
      ${data_tabels.length > 0 ? `FILTER(?table_name IN (${data_tabels.join(", ")})) .` : ""}
      ${scenariosFilter.length > 0 ? `FILTER(?scenario IN (${scenariosFilter.join(", ")})) .` : ""}
      ${gasesFilter.length > 0 ? `FILTER(?gas IN (${gasesFilter.join(", ")})) .` : ""}
      ${categoriesFilter.length > 0 ? `FILTER(?category IN (${categoriesFilter.join(", ")})) .` : ""}
      ${countriesFilter.length > 0 ? `FILTER(?country_code IN (${countriesFilter.join(", ")})) .` : ""}
    }`;

    try {
      const response = await axios.post(conf.obdi, main_query, {
        headers: {
          "X-CSRFToken": CSRFToken(),
          Accept: "application/sparql-results+json",
          "Content-Type": "application/sparql-query",
        },
      });
      const fetchedData = response.data.results.bindings;
      setSparqlOutput(fetchedData);
      if (fetchedData.length !== 0) {
        const distinctUnits = [
          ...new Set(fetchedData.map((obj) => obj.unit.value)),
        ];
        SetUnits(distinctUnits);
        const distinctYears = [
          ...new Set(fetchedData.map((obj) => obj.year.value)),
        ].sort();
        const firstYear = distinctYears.includes("2025")
          ? "2025"
          : distinctYears[0]?.toString();
        handleYearChange(null, firstYear, index, fetchedData);
      } else {
        setLoading(false);
        setShowChart(false);
        setOpenEmptyResultDialog(true);
      }
    } catch (error) {
      console.error(error);
      setLoading(false);
      setShowChart(false);
      setOpenEmptyResultDialog(true);
    }
  };

  const isTooComplex =
    selectedScenarios.length > 1 &&
    selectedCategories.length > 1 &&
    selectedGas.length > 1;

  return (
    <Grid container spacing={2}>
      <Grid item lg={6} sx={{ borderLeft: variables.border.light, px: 2 }}>
        <Alert severity="warning">
          <Chip label="Early Access" color="error" />
          <p>
            The quantitative scenario projection comparison serves illustration
            purposes.
          </p>
        </Alert>
      </Grid>
      <Grid item lg={6} sx={{ borderLeft: variables.border.light, px: 2 }}>
        <Alert severity="info">
          <p>
            The Open Energy Knowledge Graph enables this comparison based on
            OEMetadata annotations.
          </p>
        </Alert>
      </Grid>

      <Grid item xs={12}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <FilterDropdown
              label="Output table(s)"
              options={outputTableNames}
              selectedValues={selectedOutputDatasets}
              onChange={handleOutputDatasetsChange}
            />
            <FilterDropdown
              label="Scenario"
              options={scenariosInTables}
              selectedValues={selectedScenarios}
              onChange={handleScenariosChange}
            />
            <FilterDropdown
              label="Sector(s)"
              options={categoryNames}
              selectedValues={selectedCategories}
              onChange={handleCategoriesChange}
            />
            <FilterDropdown
              label="Gas(es)"
              options={gasesNames}
              selectedValues={selectedGas}
              onChange={handleGasChange}
            />
            <FilterDropdown
              label="Country(ies)"
              options={countryNames}
              selectedValues={selectedCountries}
              onChange={handleCountriesChange}
            />
          </Grid>

          <Grid
            item
            xs={12}
            sx={{
              display: "flex",
              justifyContent: "flex-end",
              flexDirection: "column",
              alignItems: "flex-end",
            }}
          >
            <Button
              sx={{ m: 1, width: 70, marginRight: "30px" }}
              size="medium"
              variant="outlined"
              endIcon={<SendIcon />}
              onClick={() => sendQuery(0)}
              disabled={
                isTooComplex ||
                selectedOutputDatasets.length === 0 ||
                selectedScenarios.length === 0 ||
                selectedCategories.length === 0 ||
                selectedGas.length === 0 ||
                selectedCountries.length === 0
              }
            >
              Submit
            </Button>
            {isTooComplex && (
              <Typography variant="caption" color="error" sx={{ mr: 4 }}>
                Selection too complex. Please limit Scenarios, Sectors, or Gases
                to avoid overlapping data.
              </Typography>
            )}
          </Grid>

          <Grid item xs={12} sx={{ display: "flex", justifyContent: "center" }}>
            {showTitle === true && (
              <Box
                sx={{
                  display: "flex",
                  flexWrap: "wrap",
                  alignItems: "center",
                  gap: 1,
                  justifyContent: "center",
                  my: 2,
                }}
              >
                <Typography variant="body1" color="text.secondary">
                  Showing
                </Typography>
                {selectedGas.map((gas, i) => (
                  <React.Fragment key={gas}>
                    <SemanticChip textLabel={gas} dictionary={gasDict} />
                    {i < selectedGas.length - 1 && (
                      <Typography variant="body2" color="text.secondary">
                        and
                      </Typography>
                    )}
                  </React.Fragment>
                ))}

                {/* --- FIX: Display Unit directly after the selected Gases --- */}
                {units.length > 0 && (
                  <>
                    <Typography variant="body1" color="text.secondary">
                      in
                    </Typography>
                    <Chip
                      label={units[0].replace(/\r/g, " ")}
                      size="small"
                      variant="filled"
                      sx={{ fontWeight: "bold" }}
                    />
                  </>
                )}

                <Typography variant="body1" color="text.secondary">
                  from
                </Typography>
                {selectedCategories.map((cat, i) => (
                  <React.Fragment key={cat}>
                    <SemanticChip textLabel={cat} dictionary={categoryDict} />
                    {i < selectedCategories.length - 1 && (
                      <Typography variant="body2" color="text.secondary">
                        and
                      </Typography>
                    )}
                  </React.Fragment>
                ))}
                <Typography variant="body1" color="text.secondary">
                  for
                </Typography>
                {selectedScenarios.map((scen, i) => (
                  <React.Fragment key={scen}>
                    <SemanticChip textLabel={scen} dictionary={scenarioDict} />
                    {i < selectedScenarios.length - 1 && (
                      <Typography variant="body2" color="text.secondary">
                        and
                      </Typography>
                    )}
                  </React.Fragment>
                ))}
              </Box>
            )}
          </Grid>

          {showChart === true && (
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    bgcolor: "background.paper",
                    px: 2,
                  }}
                >
                  <Tabs
                    onChange={(e, number) => handleYearChange(e, number, 0)}
                    value={scenarioYear[0]}
                    variant="scrollable"
                    scrollButtons
                  >
                    {scenarioYears[0]?.map((year, idx) => (
                      <Tab
                        label={year}
                        key={year}
                        value={scenarioYears[0][idx]}
                      />
                    ))}
                  </Tabs>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                    <IconButton
                      onClick={handleDownloadCSV}
                      title="Download data as CSV"
                      color="primary"
                    >
                      <DownloadIcon />
                    </IconButton>
                    <ToggleButtonGroup
                      value={viewMode}
                      exclusive
                      onChange={handleViewModeChange}
                      size="small"
                    >
                      <ToggleButton value="chart" aria-label="chart view">
                        <BarChartIcon />
                      </ToggleButton>
                      <ToggleButton value="table" aria-label="table view">
                        <TableViewIcon />
                      </ToggleButton>
                    </ToggleButtonGroup>
                  </Box>
                </Box>
              </Grid>

              <Grid item xs={12}>
                {viewMode === "chart" ? (
                  <Box sx={{ height: "600px", width: "100%", mt: 2 }}>
                    <ReactECharts
                      option={echartsOption}
                      style={{ height: "100%", width: "100%" }}
                      notMerge={true}
                    />
                  </Box>
                ) : (
                  <Box sx={{ px: 4, py: 2 }}>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell align="left">
                              <strong>Country</strong>
                            </TableCell>
                            {selectedOutputDatasets.length > 1 && (
                              <TableCell align="left">
                                <strong>Table</strong>
                              </TableCell>
                            )}
                            {selectedScenarios.length > 0 && (
                              <TableCell align="left">
                                <strong>Scenario</strong>
                              </TableCell>
                            )}
                            {selectedCategories.length > 0 && (
                              <TableCell align="left">
                                <strong>Sector</strong>
                              </TableCell>
                            )}
                            {selectedGas.map((gas, i) => (
                              <TableCell key={i} align="right">
                                <strong>{gas}</strong>
                              </TableCell>
                            ))}
                            <TableCell align="right">
                              <strong>Unit</strong>
                            </TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {tableData.source
                            .filter((row) => !row.isSpacer)
                            .map((row, rowIndex) => (
                              <TableRow key={rowIndex}>
                                <TableCell align="left">
                                  {row.Country}
                                </TableCell>
                                {selectedOutputDatasets.length > 1 && (
                                  <TableCell align="left">
                                    {row.Table}
                                  </TableCell>
                                )}
                                {selectedScenarios.length > 0 && (
                                  <TableCell align="left">
                                    {row.Scenario}
                                  </TableCell>
                                )}
                                {selectedCategories.length > 0 && (
                                  <TableCell align="left">
                                    {row.Sector}
                                  </TableCell>
                                )}
                                {selectedGas.map((gas, colIndex) => {
                                  const val = row[gas];
                                  return (
                                    <TableCell key={colIndex} align="right">
                                      {typeof val === "number"
                                        ? val.toFixed(2)
                                        : val === 0
                                          ? "0.00"
                                          : val}
                                    </TableCell>
                                  );
                                })}
                                <TableCell align="right">
                                  {units.length > 0
                                    ? units[0].replace(/\r/g, " ")
                                    : ""}
                                </TableCell>
                              </TableRow>
                            ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Box>
                )}
              </Grid>
            </Grid>
          )}
        </Grid>
      </Grid>
      <Grid item xs={12}>
        {loading == true && (
          <Box sx={{ paddingTop: "10px" }}>
            <LinearProgress />
          </Box>
        )}
      </Grid>
      <Grid item xs={12}>
        <Snackbar
          open={openEmptyResultDialog}
          autoHideDuration={6000}
          onClose={handleEmptyResultMessageClose}
        >
          <Alert
            variant="filled"
            onClose={handleEmptyResultMessageClose}
            severity="success"
            sx={{ width: "100%" }}
          >
            <div>
              There is still <strong>no data</strong> for the selected filters.
            </div>
          </Alert>
        </Snackbar>
      </Grid>
    </Grid>
  );
};

export default QuantitativeView;
