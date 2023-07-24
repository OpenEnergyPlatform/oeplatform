const getColors = colorName => {
  const colors = {
    text: "#E0E0E0",
    backGround: "#263238",
    borders: "#E0E0E0",
    playGroundBackgroundColor: "#ffffff"
  };
  return colors[colorName];
};

export { getColors };
