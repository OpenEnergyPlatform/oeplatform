// CustomTabs.tsx
import React, { useState } from 'react';
import { Box, Tabs, Tab, Typography } from '@mui/material';
import { styled } from '@mui/material/styles';
import palette from '../styles/oep-theme/palette';
import variables from '../styles/oep-theme/variables';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}
function TabPanel({ children, value, index, ...other }: TabPanelProps) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 2, pb: 2 }}>
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

const TabsWrapper = styled(Box)(({ theme }) => ({
  flexGrow: 1,
  backgroundColor: theme.palette.background.paper,
}));

const StyledTab = styled(Tab)(({ theme }) => ({
  background: theme.palette.grey[100],
  color: palette.text.link,
  fontWeight: theme.typography.fontWeightBold,
  border: `1px solid ${palette.border}`,
  minHeight: 'fit-content',
  padding: theme.spacing(1),
  textTransform: 'none',

  '&:first-of-type': {
    borderTopLeftRadius: variables.borderRadius,
    borderBottomLeftRadius: variables.borderRadius,
  },
  '&:last-of-type': {
    borderTopRightRadius: variables.borderRadius,
    borderBottomRightRadius: variables.borderRadius,
  },
  '&:not(:last-of-type)': {
    borderRight: 'none',
  },
  '&.Mui-selected': {
    background: palette.primary.dark,
    border: `1px solid ${palette.primary.dark}`,
    color: palette.primary.contrastText,
  },
}));

type CustomTabsProps = {
  factsheetObjectHandler?: any;
  items: {
    titles: string[];
    contents: React.ReactNode[];
  };
};

export default function CustomTabs({ factsheetObjectHandler, items }: CustomTabsProps) {
  const [value, setValue] = useState(0);
  const handleChange = (_: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
    if (factsheetObjectHandler) {
      factsheetObjectHandler(newValue);
    }
  };

  return (
    <Box>
      <TabsWrapper>
        <Tabs
          value={value}
          onChange={handleChange}
          variant="fullWidth"
          allowScrollButtonsMobile
          scrollButtons
          TabIndicatorProps={{ style: { display: 'none' } }}
        >
          {items.titles.map((label, idx) => (
            <StyledTab key={idx} label={label} {...arrayProps(idx)} />
          ))}
        </Tabs>
      </TabsWrapper>

      <Box>
        {items.contents.map((content, idx) => (
          <TabPanel key={idx} value={value} index={idx}>
            {content}
          </TabPanel>
        ))}
      </Box>
    </Box>
  );
}
