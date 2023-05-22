import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import Chip from '@mui/material/Chip';
import Checkbox from '@mui/material/Checkbox';
import HiveIcon from '@mui/icons-material/Hive';
import HiveOutlinedIcon from '@mui/icons-material/HiveOutlined';

const reorder = (list, startIndex, endIndex) => {
  const result = Array.from(list);
  const [removed] = result.splice(startIndex, 1);
  result.splice(endIndex, 0, removed);
  return result;
};

const grid = 10;

const getItemStyle = (isDragging, draggableStyle, index) => ({
  userSelect: 'none',
  padding: grid * 2,
  margin: `0 ${grid}px 0 0`,
  marginTop: '10px',
  marginBottom: '10px',
  background: index === 0 ? '#488AC740' : '#87AFC740',
  minWidth: '28%',
  height: '90%',
  borderRadius: '5px',
  overflow: 'auto',
  border: '1px solid black',
  ...draggableStyle,
});

const getListStyle = isDraggingOver => ({
  background: isDraggingOver ? 'white' : 'white',
  display: 'flex',
  padding: grid,
  overflow: 'auto',
  width: '100%',
  height: '95%'
});

export default function  ComparisonBoardItems (props) {
  const { elements } = props;
  const [state, setState] = useState({ items : elements });

  function onDragEnd(result) {
    if (!result.destination) {
      return;
    }
    if (result.destination.index === result.source.index) {
      return;
    }
    const newItems = reorder(
      state.items,
      result.source.index,
      result.destination.index
    );
    setState({
      items: newItems,
    });
  }

  const label = { inputProps: { 'aria-label': 'Checkbox demo' } };

  return (
    <div style={{ overflow: 'auto'}}>
      <DragDropContext onDragEnd={onDragEnd}>
        <Droppable droppableId="droppable" direction="horizontal">
          {(provided, snapshot) => (
            <div
              ref={provided.innerRef}
              style={getListStyle(snapshot.isDraggingOver)}
              {...provided.droppableProps}
            >
              {state.items.map((item, index) => (
                <Draggable key={item.id} draggableId={item.id} index={index}>
                  {(provided, snapshot) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                      {...provided.dragHandleProps}
                      style={getItemStyle(
                        snapshot.isDragging,
                        provided.draggableProps.style,
                        index
                      )}
                    >

                      <div style={{ display: 'flex' }} >
                        { index === 0 ? <HiveIcon sx={{ fontSize: 40 }}  /> : <HiveOutlinedIcon sx={{ fontSize: 40 }} /> }
                        <Typography variant="h5" gutterBottom component="div" style={{ marginTop:'5px', marginBottom:'15px', height: '30px' }}>
                        { index === 0 ? <b>{item.content}</b> : item.content }
                        </Typography>
                      </div>
                      <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Institutions:</b> 
                        </Typography>
                        <div style={{ marginBottom: '5px', height: '30px'}} >
                          {item['institutions'].map((v, i) => (
                            <Chip size='small' key={v}  label={v} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                          ))}
                        </div>
                      <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Descriptors:</b> 
                        </Typography>
                        <div style={{ marginBottom: '5px', height: '70px', overflow: 'auto' }} >
                          {item['descriptors'].map((v, i) => (
                            <Chip size='small' key={v}  label={v} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                          ))}
                        </div>
                        <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Sectors:</b> 
                        </Typography>
                        <div style={{ marginBottom: '5px', height: '30px', overflow: 'auto' }} >
                          {item['sectors'].map((v) => (
                            <Chip size='small' key={v}  label={v} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: '#ffffff'}}/>
                          ))}
                        </div>
                        <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Energy carriers:</b> 
                        </Typography>
                        <div style={{ marginBottom: '5px', height: '50px', overflow: 'auto'}} >
                          {item['enrgy-carriers'].map((v) => (
                            <Chip size='small' key={v}  label={v} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                          ))}
                        </div>
                        <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Enrgy transformation processes:</b> 
                        </Typography>
                        <div style={{ marginBottom: '5px', height: '50px', overflow: 'auto'}} >
                          {item['enrgy-transformation-processes'].map((v) => (
                            <Chip size='small' key={v}  label={v} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                          ))}
                        </div>
                        <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                            <b>Scenarios:</b> 
                          </Typography>
                          <div style={{ marginBottom: '5px', height: '70px', overflow: 'auto'}} >
                            {item['scenarios'].map((v, i) => (
                               <div>
                                  <Chip size='small' key={v}  label={v} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                                  <Checkbox {...label} defaultChecked color={[0, 1].includes(item['id']) ? "error" : "success"}  sx={{color: 'red' }}/>  <Typography variant="caption">Target-driven</Typography>
                                  <Checkbox {...label} defaultChecked color="success"/><Typography variant="caption">Measure-driven</Typography>
                             </div>
                            ))}
                         
                          </div>
                        <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Scenario descriptors:</b> 
                        </Typography>
                        <div style={{ marginBottom: '5px', height: '50px', overflow: 'auto'}} >
                          {item['scenario-descriptors'].map((v, i) => (
                            <Chip size='small' key={v}  label={v} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                          ))}
                        </div>
                        <Divider />
                          <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                            <b>Regions:</b> 
                          </Typography>
                          <div style={{ marginBottom: '5px', height: '30px', overflow: 'auto'}} >
                            {item['region'].map((v, i) => (
                              <Chip size='small' key={v}  label={v} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                            ))}
                          </div>
                        <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Years:</b> 
                        </Typography>
                        <div style={{ marginBottom: '5px', height: '30px', overflow: 'auto'}} >
                          {item['scenario_years'].map((v, i) => (
                            <Chip size='small' key={v}  label={v} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor:'white' }}/>
                          ))}
                        </div>
                      <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Models:</b> 
                        </Typography>
                        <div style={{ marginBottom: '5px', height: '30px', overflow: 'auto'}} >
                          {item['models'].map((v) => (
                            <Chip size='small' key={v.name}  label={v} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: '#ffffff' }}/>
                          ))}
                        </div>
                        <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Frameworks:</b> 
                        </Typography>
                        <div style={{ marginBottom: '5px', height: '30px', overflow: 'auto'}} >
                          {item['frameworks'].map((v) => (
                            <Chip size='small' key={v.name}  label={v} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: '#ffffff' }}/>
                          ))}
                        </div>
                    </div>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </DragDropContext>
    </div>
  );
}