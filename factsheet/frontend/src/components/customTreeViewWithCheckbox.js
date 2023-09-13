import React, { useState } from 'react';
import CheckboxTree from 'react-checkbox-tree';
import 'react-checkbox-tree/lib/react-checkbox-tree.css';
import '../styles/react-checkbox-tree.css';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CheckBoxOutlinedIcon from '@mui/icons-material/CheckBoxOutlined';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import EditIcon from '@mui/icons-material/Edit';
import Typography from '@mui/material/Typography';

export default function CustomTreeViewWithCheckBox(props) {
  const {
    data,
    flat,
    title,
    size,
    handler,
   } = props;

  const [expanded, setExpanded] = useState([]);
  const [checked, setChecked] = useState(props.checked.map(i => i.label));
  const handleChange = (checked) => {
    setChecked(checked);
    handler(checked, data);
  };
  
  return (
    <Box>
      <Typography variant="subtitle1" gutterBottom style={{ marginTop:'30px', marginBottom:'10px' }}>
        {title}
      </Typography>
      <Box style={{ backgroundColor:'#FCFCFC', marginTop :'5px', height: size, overflow: 'auto', 'border':'1px solid #cecece', 'borderRadius': '2px', width: '50%' }}>
        <CheckboxTree
            nodes={data}
            checked={checked}
            expanded={expanded}
            onCheck={(checked) => handleChange(checked)}
            onExpand={(expanded) => setExpanded(expanded)}
            icons={{
              check: <CheckBoxIcon />,
              uncheck: <CheckBoxOutlineBlankIcon />,
              expandClose: <KeyboardArrowRightIcon />,
              expandOpen: <KeyboardArrowDownIcon />,
              halfCheck:  <CheckBoxOutlinedIcon />,
            }}
            showNodeIcon={false}
            optimisticToggle={false}
            noCascade={true}
          />
      </Box>
      <Box
          mt={3}
          sx={{
            'marginTop': '10px',
            'overflow': 'auto',
            'height': '100%',
            // 'border': '1px dashed #cecece',
            'overflow': 'scroll',
            'borderRadius': '5px',
            // 'backgroundColor':'#FCFCFC'
          }}
        >
          {checked.map((v) => (
            <Chip size='small' key={v}  label={v} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px' }}/>
          ))}


      </Box>
    </Box>  
  );
}