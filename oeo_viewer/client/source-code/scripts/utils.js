// SPDX-FileCopyrightText: 2025 Adel Memariani <memarian@haskell2go.iks.cs.ovgu.de>
// SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
// SPDX-FileCopyrightText: 2025 Jonas Huber <jonas.huber@rl-institut.de>
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
