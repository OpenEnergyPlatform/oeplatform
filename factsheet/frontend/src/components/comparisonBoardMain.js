import React, { useState } from 'react';
import ComparisonBoardItem from "./comparisonBoardItem";
import { Box } from "@mui/system";

const ComparisonBoardMain = (props) => {
  const { items } = props;

  return (
    <Box sx={{ 
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      maxWidth: '100%',
      overflow: 'auto',
      height: '75vh'
     }}>
       <ComparisonBoardItem />
       <ComparisonBoardItem />
       <ComparisonBoardItem />
       <ComparisonBoardItem />
       <ComparisonBoardItem />
       <ComparisonBoardItem />
       <ComparisonBoardItem />
       <ComparisonBoardItem />
    </Box>
  );
};

export default ComparisonBoardMain;
