import React, { useState } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { List, ListItem, ListItemText, makeStyles } from '@material-ui/core';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

const useStyles = makeStyles({
  list: {
    backgroundColor: '#f7f7f7',
    borderRadius: '5px',
    padding: '10px',
  },
  item: {
    backgroundColor: '#04678F20',
    borderRadius: '5px',
    marginBottom: '5px',
  },
});

const ComparisonBoardItem = () => {
  const [items, setItems] = useState([
    { id: 'item-1', content: 'Item 1' },
    { id: 'item-2', content: 'Item 2' },
    { id: 'item-3', content: 'Item 3' },
    { id: 'item-4', content: 'Item 4' },
    { id: 'item-5', content: 'Item 5' },
    { id: 'item-6', content: 'Item 6' },
    { id: 'item-7', content: 'Item 7' },
    { id: 'item-8', content: 'Item 8' },
    { id: 'item-9', content: 'Item 9' },
    { id: 'item-10', content: 'Item 10' },
    { id: 'item-11', content: 'Item 11' },
    { id: 'item-12', content: 'Item 12' },
    { id: 'item-13', content: 'Item 13' },
    { id: 'item-14', content: 'Item 14' },
    { id: 'item-15', content: 'Item 15' },
  ]);

  const classes = useStyles();

  const onDragEnd = (result) => {
    if (!result.destination) return;
    const newItems = Array.from(items);
    const [reorderedItem] = newItems.splice(result.source.index, 1);
    newItems.splice(result.destination.index, 0, reorderedItem);
    setItems(newItems);
  };

  return (
    <Box  style={{
        backgroundColor: '#f7f7f7',
        borderRadius: '5px',
        margin : '5px',
        paddingTop: '60px',
      }}>
        <DragDropContext onDragEnd={onDragEnd} >
        <ListItem  
            style={{
              backgroundColor: '#04678F',
              marginLeft : '15px',
              padding: '10px',
              borderRadius: '5px',
              color: 'white',
              width:'92%'
            }}>
            <Typography variant="subtitle1" gutterBottom style={{ marginTop: '10px' }}>
              <b>{ 'Factsheet Name' }</b>
            </Typography>
          </ListItem>
        <Droppable droppableId="my-droppable">
            {(provided) => (
            <List className={classes.list} {...provided.droppableProps} ref={provided.innerRef}
                  style={{
                    flex: '1 1 auto',
                    minWidth: '500px',
                    maxWidth: '600px',
                    margin: '5px',
                    padding: '10px',
                    overflow: 'auto',
                    height: '70vh'
                  }}
            >
                {items.map((item, index) => (
                <Draggable key={item.id} draggableId={item.id} index={index}>
                    {(provided) => (
                    <ListItem
                        className={classes.item}
                        {...provided.draggableProps}
                        {...provided.dragHandleProps}
                        ref={provided.innerRef}
                    >
                      <ListItemText>
                          <Typography variant="subtitle2" gutterBottom style={{ marginTop: '10px' }}>
                            {index} : { item.content}
                          </Typography>
                      </ListItemText>
                    </ListItem>
                    )}
                </Draggable>
                ))}
                {provided.placeholder}
            </List>
            )}
        </Droppable>
        </DragDropContext>
    </Box>
  );
};

export default ComparisonBoardItem;
