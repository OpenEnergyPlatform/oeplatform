import { styled } from '@mui/material/styles';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';

// === A “vertical tab” that used to come from makeStyles(tab) ===
export const VerticalTab = styled(Tab)(({ theme }) => ({
  background: '#e3eaef',
  border: '1px solid #cecece',
  marginBottom: 5,
  textTransform: 'none',
  '&.Mui-selected': {
    background: '#001c30e6',
    color: '#fff',
  },
}));

// === Wrapper under the tabs for your AddIcon button ===
export const AddTabWrapper = styled(Box)({
  textAlign: 'center',
  marginTop: 5,
  padding: '0 10px',
});
