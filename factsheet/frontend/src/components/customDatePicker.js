import * as React from 'react';
import dayjs from 'dayjs';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { DesktopDatePicker } from '@mui/x-date-pickers/DesktopDatePicker';
import { MobileDatePicker } from '@mui/x-date-pickers/MobileDatePicker';

export default function CustomDatePicker(props) {
  const { label, yearOnly } = props;
  const [value, setValue] = React.useState(dayjs('2022-10-11T21:11:54'));

  const handleChange = (newValue) => {
    setValue(newValue);
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Stack spacing={3} style={{ width: '90%' }}>
        {yearOnly ?
          <DesktopDatePicker
            label={label}
            value={value}
            onChange={handleChange}
            renderInput={(params) => <TextField {...params} />}
            views={["year"]}
          />
          :<DesktopDatePicker
            label={label}
            value={value}
            onChange={handleChange}
            renderInput={(params) => <TextField {...params} />}
            inputFormat="MM/DD/YYYY"
          />
        }
      </Stack>
    </LocalizationProvider>
  );
}
