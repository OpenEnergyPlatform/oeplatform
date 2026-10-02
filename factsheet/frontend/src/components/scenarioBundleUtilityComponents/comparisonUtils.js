// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// comparisonUtils.js
export const OEP_ORIGIN = window.location.origin;

export function datasetHref(ds) {
  if (!ds?.url) return null;
  if (ds.url.startsWith("http://") || ds.url.startsWith("https://"))
    return ds.url;
  return `${OEP_ORIGIN}/${ds.url.replace(/^\/+/, "")}`;
}

export function datasetDisplay(ds) {
  return ds?.label || ds?.table_name || ds?.external_id || ds?.url || "Dataset";
}

export const generateRandomColor = () => {
  let color;
  do {
    color = `#${Math.floor(Math.random() * 16777215)
      .toString(16)
      .padStart(6, "0")}`;
  } while (color === "#000000" || parseInt(color.slice(1), 16) <= 0x222222);
  return color;
};

export const randomColors = Array.from({ length: 50 }, generateRandomColor);

export function findSharedElements(lists) {
  return lists.reduce((shared, currentList) => {
    return shared.filter((value) => currentList.includes(value));
  });
}

export function divideByTableNameValue(items) {
  return items.reduce((acc, obj) => {
    const tableNameValue = obj.table_name.value;
    if (!acc[tableNameValue]) {
      acc[tableNameValue] = [];
    }
    acc[tableNameValue].push(obj);
    return acc;
  }, {});
}

export const gas_dictionary = {
  OEO_00000025: "Methane (CH4)",
  OEO_00000027: "Nitrous_oxide (N2O2)",
  OEO_00000026: "Nitrogen Trifluoride (NF3)",
  OEO_00000219: "Hydrofluorocarbon (HFC)",
  OEO_00000006: "Carbon dioxide (CO2)",
  OEO_00000322: "Perfluorocarbon (PFC)",
  OEO_00000038: "Sulphur hexafluoride (SF6)",
  Total_GHGs: "Total GHGs",
  Total_ESD_GHGs: "Total ESD GHGs",
  Total_ETS_GHGs: "Total ETS GHGs",
  Total_ESR_GHGs: "Total ESR GHGs",
};

export const scenarios_disctionary = {
  OEO_00020310: "without measures scenario (WOM)",
  OEO_00020311: "with existing measures scenario (WEM)",
  OEO_00020312: "with additional measures scenario (WAM)",
};
