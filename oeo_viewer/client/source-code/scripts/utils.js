// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani>
// SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr>
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI>
//
// SPDX-License-Identifier: MIT

const getColors = (colorName) => {
  const colors = {
    text: "#E0E0E0",
    backGround: "#263238",
    borders: "#E0E0E0",
    playGroundBackgroundColor: "#ffffff",
  };
  return colors[colorName];
};

export {getColors};
