import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

const CardRow = ({ rowKey, rowValue }) => {
  return (
    <Stack
      direction="row"
      justifyContent="flex-start"
      alignItems="flex-start"
      spacing={2}
    >
      <Typography sx={{ fontWeight: 'bold', minWidth: '12rem' }}>
        {rowKey}
      </Typography>
      <Typography>
        {rowValue}
      </Typography>
    </Stack>
  )
}

export default CardRow;