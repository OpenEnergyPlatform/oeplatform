import * as React from 'react';
import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import MobileStepper from '@mui/material/MobileStepper';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import KeyboardArrowLeft from '@mui/icons-material/KeyboardArrowLeft';
import KeyboardArrowRight from '@mui/icons-material/KeyboardArrowRight';
import TextField from '@mui/material/TextField';

const steps = [
  {
    label: 'Author',
    description: `An author is an agent that creates or has created written work.`,
  },
  {
    label: 'Analysis scope',
    description:
      'An analysis scope is an information content entity that describes the boundaries of what a study or scenario covers.',
  },
  {
    label: 'Study region',
    description: `A study region is a spatial region that is under investigation and consists entirely of one or more subregions.`,
  },
  {
    label: 'Data set',
    description: `A data item that is an aggregate of other data items of the same type that have something in common. Averages and distributions can be determined for data sets.`,
  },
];

export default function Wizard(props) {
  const { graphData } = props;

  const theme = useTheme();
  const [activeStep, setActiveStep] = React.useState(0);
  const maxSteps = steps.length;

  const [oekg, setOekg] = React.useState(graphData);

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };


  return (
    <Box sx={{ flexGrow: 1 }} className="bg_img">
      <Paper
        square
        elevation={0}
        sx={{
          display: 'flex',
          alignItems: 'center',
          height: 50,
          pl: 2,
          bgcolor: '#4189B5',
          color: 'white'
        }}
      >
        <Typography component={'span'} variant={'h6'}>{steps[activeStep].label}</Typography>
      </Paper>
      <Box sx={{ height: 800, width: '100%', p: 2 }}>
        <div>
          <div>
            {steps[activeStep].description}
          </div>
          <div className="wizard_element-div">
            <TextField className="wizard_element" id="outlined-basic" label="Label" variant="outlined" />
          </div>
          <div className="wizard_element-div">
            <TextField className="wizard_element" id="outlined-basic" label="Value" variant="outlined" />
          </div>
          <div className="wizard_element-div">
            <TextField className="wizard_element" id="outlined-basic" label="URL" variant="outlined" />
          </div>
        </div>
      </Box>
      <MobileStepper
        variant="text"
        steps={maxSteps}
        position="static"
        activeStep={activeStep}
        nextButton={
          <Button
            size="small"
            variant="contained"
            onClick={handleNext}
            disabled={activeStep === maxSteps - 1}
          >
            Next
            {theme.direction === 'rtl' ? (
              <KeyboardArrowLeft />
            ) : (
              <KeyboardArrowRight />
            )}
          </Button>
        }
        backButton={
          <Button variant="contained" size="small" onClick={handleBack} disabled={activeStep === 0}>
            {theme.direction === 'rtl' ? (
              <KeyboardArrowRight />
            ) : (
              <KeyboardArrowLeft />
            )}
            Back
          </Button>
        }
      />
    </Box>
  );
}
