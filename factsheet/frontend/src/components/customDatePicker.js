import * as React from 'react';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { DesktopDatePicker } from '@mui/x-date-pickers/DesktopDatePicker';
import { MobileDatePicker } from '@mui/x-date-pickers/MobileDatePicker';
import dayjs from 'dayjs';

export default function CustomDatePicker(props) {
  const { label, yearOnly } = props;
  const [value, setValue] = React.useState(dayjs('2022-04-07'));

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Stack spacing={1} style={{ width: '90%', marginTop: '-40px' }}>
        {yearOnly ?
          <DesktopDatePicker
            label={label}
            value={'2022-04-07'}
            views={["year"]}
            renderInput={(params) => <TextField {...params} />}
          />
          :<DesktopDatePicker
            label={label}
            inputFormat="MM/DD/YYYY"
            value={value}
            onChange={(newValue) => {
              setValue(newValue);
            }}
            renderInput={(params) => <TextField {...params} />}
          />
        }
      </Stack>
    </LocalizationProvider>
  );
}
