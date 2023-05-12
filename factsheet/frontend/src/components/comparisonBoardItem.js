import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import Chip from '@mui/material/Chip';

const reorder = (list, startIndex, endIndex) => {
  const result = Array.from(list);
  const [removed] = result.splice(startIndex, 1);
  result.splice(endIndex, 0, removed);
  return result;
};

const grid = 10;

const getItemStyle = (isDragging, draggableStyle) => ({
  userSelect: 'none',
  padding: grid * 2,
  margin: `0 ${grid}px 0 0`,
  marginTop: '30px',
  marginBottom: '30px',
  background: isDragging ? '#488AC740' : '#87AFC740',
  minWidth: '32%',
  height: '85%',
  borderRadius: '5px',
  overflow: 'auto',
  border: '1px solid black',
  ...draggableStyle,
});

const getListStyle = isDraggingOver => ({
  background: isDraggingOver ? '#C2DFFF40' : '#E5E4E240',
  display: 'flex',
  padding: grid,
  overflow: 'auto',
  width: '100%',
  height: '70vh'
});

export default function  ComparisonBoardItem (props) {
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
  return (
    <div style={{ width: '100%', overflow: 'auto'}}>
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
                        provided.draggableProps.style
                      )}
                    >
                      <Typography variant="h6" gutterBottom component="div">
                        <b>{item.content}</b>
                      </Typography>
                      <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '20px' }}>
                          <b>Descriptors:</b> 
                        </Typography>
                        <div style={{ marginBottom: '20px'}} >
                          {item['descriptors'].map((v) => (
                            <Chip size='small' key={v}  label={v} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: '#ffffff' }}/>
                          ))}
                        </div>
                        <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '20px' }}>
                          <b>Sectors:</b> 
                        </Typography>
                        <div style={{ marginBottom: '20px'}} >
                          {item['sectors'].map((v) => (
                            <Chip size='small' key={v}  label={v} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: '#ffffff'}}/>
                          ))}
                        </div>
                        <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '20px' }}>
                          <b>Energy carriers:</b> 
                        </Typography>
                        <div style={{ marginBottom: '20px'}} >
                          {item['enrgy-carriers'].map((v) => (
                            <Chip size='small' key={v.label}  label={v.label} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: '#ffffff' }}/>
                          ))}
                        </div>
                        <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '20px' }}>
                          <b>Enrgy transformation processes:</b> 
                        </Typography>
                        <div style={{ marginBottom: '20px'}} >
                          {item['enrgy-transformation-processes'].map((v) => (
                            <Chip size='small' key={v.label}  label={v.label} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: '#ffffff' }}/>
                          ))}
                        </div>
                        <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '20px' }}>
                          <b>Models:</b> 
                        </Typography>
                        <div style={{ marginBottom: '20px'}} >
                          {item['models'].map((v) => (
                            <Chip size='small' key={v.name}  label={v.name} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: '#ffffff' }}/>
                          ))}
                        </div>
                        <Divider />
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '20px' }}>
                          <b>Frameworks:</b> 
                        </Typography>
                        <div style={{ marginBottom: '20px'}} >
                          {item['frameworks'].map((v) => (
                            <Chip size='small' key={v.name}  label={v.name} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: '#ffffff' }}/>
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