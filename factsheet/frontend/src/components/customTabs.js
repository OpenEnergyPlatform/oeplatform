import React, { useState, useEffect } from 'react';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import { makeStyles, Theme } from '@material-ui/core/styles';
import palette from '../styles/oep-theme/palette';

import '../styles/App.css';
import variables from '../styles/oep-theme/variables';

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

export default function CustomTabs(props) {
  const { factsheetObjectHandler, items } = props;
  const [value, setValue] = useState(0);
  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };
  const useStyles = makeStyles((theme: Theme) => ({
    root: {
      flexGrow: 1,
      backgroundColor: theme.palette.background.paper,
    },
    tab: {
      background: theme.palette.grey[100],
      color: palette.text.link,
      fontWeight: theme.typography.fontWeightBold,
      border: `1px solid ${palette.border}`,
      minHeight: 'fit-content',
      padding: theme.spacing(1),

      '&:first-of-type': {
        borderTopLeftRadius: variables.borderRadius,
        borderBottomLeftRadius: variables.borderRadius
      },
      '&:last-of-type': {
        borderTopRightRadius: variables.borderRadius,
        borderBottomRightRadius: variables.borderRadius
      },
      '&:not(:last-of-type)': {
        borderRight: 'none'
      },
      '&.Mui-selected': {
        background: palette.primary.dark,
        border: `1px solid ${palette.primary.dark}`,
        color: palette.primary.contrastText
      }
    },
  }));
  const classes = useStyles();
  const tabClasses = {root: classes.tab};
  return (
    <Box >
      <Box className={classes.root}>
        <Tabs value={value} 
          onChange={handleChange} 
          allowScrollButtonsMobile 
          scrollButtons 
          classes={'tabs'} 
          variant="fullWidth"
          TabIndicatorProps={{
            style: {
              display: 'none'
            }
          }}
        >
          {items.titles.map((item, index) => {
            return <Tab label={item} {...arrayProps(index)}  sx={{ textTransform :"none" }} classes={tabClasses}/>;
            })}
        </Tabs>
      </Box>
      <Box>
        {items.contents.map((content, index) => {
          return <TabPanel value={value} index={index}>
            {content}
          </TabPanel>;
          })}
      </Box>
    </Box>
  );
}
