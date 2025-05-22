import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, Checkbox, FormControlLabel, Box, Slider, Stack, TextField
} from '@mui/material';
import { LocalizationProvider, DesktopDatePicker } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import CustomAutocompleteWithoutAddNew from './customAutocompleteWithoutAddNew';
import StudyKeywords from './scenarioBundleUtilityComponents/StudyDescriptors';
import FilterFeedbackBanner from './filterFeedbackBanner';

export default function FactsheetFilterDialog({
  open,
  onClose,
  onConfirm,
  institutions,
  authors,
  fundingSources,
  selectedInstitution,
  selectedAuthors,
  selectedFundingSource,
  startDateOfPublication,
  endDateOfPublication,
  scenarioYearValue,
  selectedStudyKeywords,
  setSelectedInstitution,
  setSelectedAuthors,
  setSelectedFundingSource,
  setStartDateOfPublication,
  setEndDateOfPublication,
  setScenarioYearValue,
  setSelectedStudyKewords,
  feedbackOpen,
  feedbackType,
  setFeedbackOpen,
  setFeedbackType,

}) {
  const [scenarioYearTouched, setScenarioYearTouched] = useState(false);
  const [publicationDateTouched, setPublicationDateTouched] = useState(false);


  const handleStudyKeywords = (event) => {
    if (event.target.checked) {
      if (!selectedStudyKeywords.includes(event.target.name)) {
        setSelectedStudyKewords([...selectedStudyKeywords, event.target.name]);
      }
    } else {
      const filtered = selectedStudyKeywords.filter(i => i !== event.target.name);
      setSelectedStudyKewords(filtered);
    }
  };

    const isFilterEmpty =
    selectedInstitution.length === 0 &&
    selectedAuthors.length === 0 &&
    selectedFundingSource.length === 0 &&
    selectedStudyKeywords.length === 0 &&
    !scenarioYearTouched &&
    !publicationDateTouched;

  return (
    <Dialog maxWidth="md" open={open} style={{ height: '85vh', overflow: 'auto' }}>
      <DialogTitle><b>Please define the criteria for selecting factsheets.</b></DialogTitle>
      <DialogContent>
        {feedbackType === 'noFilters' && feedbackOpen && (
          <FilterFeedbackBanner
            open={feedbackOpen}
            onClose={() => setFeedbackOpen()}
            type={feedbackType}
          />
        )}

        <CustomAutocompleteWithoutAddNew
          bgColor="white"
          width="100%"
          type="institution"
          showSelectedElements
          manyItems
          optionsSet={institutions}
          kind="Which institutions are you interested in?"
          handler={setSelectedInstitution}
          selectedElements={selectedInstitution}
        />
        <CustomAutocompleteWithoutAddNew
          bgColor="white"
          width="100%"
          type="author"
          showSelectedElements
          manyItems
          optionsSet={authors}
          kind="Which authors are you interested in?"
          handler={setSelectedAuthors}
          selectedElements={selectedAuthors}
        />
        <CustomAutocompleteWithoutAddNew
          bgColor="white"
          width="100%"
          type="Funding source"
          showSelectedElements
          manyItems
          optionsSet={fundingSources}
          kind="Which funding sources are you interested in?"
          handler={setSelectedFundingSource}
          selectedElements={selectedFundingSource}
        />

        <div style={{ marginTop: "20px" }}>Date of publication:</div>
        <div style={{ display: 'flex', marginTop: "10px" }}>
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <Stack spacing={3} style={{ width: '90%' }}>
              <DesktopDatePicker
                label="Start"
                views={['year']}
                value={startDateOfPublication}
                renderInput={(params) => <TextField {...params} />}
                onChange={(newValue) => {
                    const year = new Date(newValue).getFullYear();
                    setStartDateOfPublication(year.toString());
                    setPublicationDateTouched(true);
                }}
              />
            </Stack>
          </LocalizationProvider>
          <LocalizationProvider dateAdapter={AdapterDayjs}>
            <Stack spacing={3} style={{ width: '90%', marginLeft: '10px' }}>
              <DesktopDatePicker
                label="End"
                views={['year']}
                value={endDateOfPublication}
                renderInput={(params) => <TextField {...params} />}
                onChange={(newValue) => {
                    const year = new Date(newValue).getFullYear();
                    setEndDateOfPublication(year.toString());
                    setPublicationDateTouched(true);
                }}
              />
            </Stack>
          </LocalizationProvider>
        </div>

        <div style={{ marginTop: "20px" }}>
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 1,
              maxHeight: '200px',
              overflowY: 'auto',
              marginTop: '10px',
            }}
          >
            {StudyKeywords.map(([keyword]) => (
              <FormControlLabel
                key={keyword}
                control={<Checkbox size="small" color="default" />}
                checked={selectedStudyKeywords.includes(keyword)}
                onChange={handleStudyKeywords}
                label={keyword}
                name={keyword}
                sx={{ width: 'calc(33% - 8px)' }}
              />
            ))}
          </Box>
        </div>

        <div style={{ marginTop: "20px" }}>
            <div>Scenario years:</div>
            <Slider
            value={scenarioYearValue}
            onChange={(e, val) => {
                setScenarioYearValue(val);
                setScenarioYearTouched(true);
            }}
            valueLabelDisplay="auto"
            min={2000}
            max={2200}
            />
        </div>
      </DialogContent>

      <DialogActions>
        <Button
          variant="contained"
          onClick={() => {
            if (isFilterEmpty) {
              setFeedbackType('noFilters');
              setFeedbackOpen(true);
              return;
            }
            onConfirm();
          }}
        >
          Confirm
        </Button>
        <Button variant="outlined" onClick={onClose}>Cancel</Button>
      </DialogActions>
    </Dialog>
  );
}
