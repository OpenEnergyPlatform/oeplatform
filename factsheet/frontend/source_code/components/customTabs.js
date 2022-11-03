import React, { useState, useEffect } from 'react';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';



interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}



function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          <Typography>{children}</Typography>
        </Box>
      )}
    </div>
  );
}

function arrayProps(index: number) {
  return {
    id: `simple-tab-${index}`,
    'aria-controls': `simple-tabpanel-${index}`,
  };
}

export default function CustomTabs(props) {
  const { factsheetObjectHandler, items } = props;
  const [value, setValue] = useState(0);




  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  return (
    <Box sx={{ 'marginTop': '10px', 'marginLeft': '10px', 'marginRight': '10px','paddingTop': '10px', 'paddingBottom': '10px', 'border': '1px solid #cecece', 'height':'70vh', 'overflow': 'auto'  }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={value} onChange={handleChange}  variant="scrollable" allowScrollButtonsMobile scrollButtons>
          {items.titles.map((item, index) => {
            return <Tab label={item} {...arrayProps(index)} />;
            })}
        </Tabs>
      </Box>
      {items.contents.map((content, index) => {
        return <TabPanel value={value} index={index}>
          {content}
        </TabPanel>;
        })}
    </Box>
  );
}
