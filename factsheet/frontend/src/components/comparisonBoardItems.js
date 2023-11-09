import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import Chip from '@mui/material/Chip';
import Checkbox from '@mui/material/Checkbox';
import HiveIcon from '@mui/icons-material/Hive';
import HiveOutlinedIcon from '@mui/icons-material/HiveOutlined';
import StudyChip from '../styles/oep-theme/components/studyChip';

const reorder = (list, startIndex, endIndex) => {
  const result = Array.from(list);
  const [removed] = result.splice(startIndex, 1);
  result.splice(endIndex, 0, removed);
  return result;
};

const grid = 10;

const getItemStyle = (isDragging, draggableStyle, index) => ({
  userSelect: 'none',
  padding: 0,
  margin: `0 ${grid}px 0 0`,
  marginTop: '5px',
  marginBottom: '5px',
  background: index === 0 ? '#F6F9FB' : '#FFFFFF',
  width: '25vw',
  height: '90%',
  overflow: 'auto',
  border: '1px solid #2972A6',
  ...draggableStyle,
});

const getListStyle = isDraggingOver => ({
  background: isDraggingOver ? 'white' : 'white',
  display: 'flex',
  overflow: 'auto',
  width: '200%',
  minHeight: '20rem',
});

export default function  ComparisonBoardItems (props) {
  const { elements, c_aspects } = props;
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
    <div style={{ overflow: 'auto' }}>
      <DragDropContext onDragEnd={onDragEnd}>
        <Droppable droppableId="droppable" direction="horizontal">
        {(provided, snapshot) => (
            <div
              ref={provided.innerRef}
              style={getListStyle(snapshot.isDraggingOver)}
              {...provided.droppableProps}
            > 
             {state.items.map((item, index) => (
                <Draggable key={item.data.uid} draggableId={item.data.uid} index={index}>
                  {(provided, snapshot) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                      {...provided.dragHandleProps}
                      style={getItemStyle(
                        snapshot.isDragging,
                        provided.draggableProps.style,
                        index
                      )
                    }
                    >
                    <div style={{ display: 'flex', height: '60px', marginBottom:'10px', flexDirection: 'column', backgroundColor: index === 0 ? '#2972A6' : '#F6F9FB',  color: index === 0 ? 'white' : 'black', alignItems: 'center', justifyContent:'center' }} >
                    
                      <Typography variant="h6">
                        { index === 0 ? <b>{item.acronym}</b> : item.acronym }
                      </Typography>
                      <Typography variant="caption">
                      { index === 0 ? 'Base scenario' : ''  }
                      </Typography>
                    </div> 

                    <div style={{ height: '60vh',overflow: 'auto', }}> 

                    
                      {c_aspects.includes("Study name") && <div style= {{  marginBottom: '10px', padding: '10px' }} >
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Study name:</b> 
                        </Typography>
                          {item.data.study_label}
                      </div>}

                      {c_aspects.includes("Study abstract") &&<div style= {{  marginBottom: '10px', padding: '10px' }} >
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Study abstract:</b> 
                        </Typography>
                          {item.data.study_abstract}
                      </div>}

                      <div style= {{  marginBottom: '10px', padding: '10px' }} >
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Abstract:</b> 
                        </Typography>
                          {item.data.abstract}
                      </div>

                      {c_aspects.includes("Descriptors") && <div style={{ marginBottom: '10px', padding: '10px' }}>
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Descriptors:</b>
                        </Typography>
                        {item.data.descriptors.map((descriptor) => (
                          <StudyChip 
                            key={descriptor}
                            index={index}
                            label={descriptor}
                            included={state.items[0].data.descriptors.includes(descriptor)}
                          />
                        ))}
                      </div>}

                      {c_aspects.includes("Regions") && <div style={{ marginBottom: '10px', padding: '10px' }}>
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Regions:</b>
                        </Typography>
                        {item.data.regions.map((region) => (
                          <StudyChip 
                            key={region}
                            index={index}
                            label={region}
                            included={state.items[0].data.regions.includes(region)}
                          />
                        ))}
                      </div>}

                      {c_aspects.includes("Interacting regions") && <div style={{ marginBottom: '10px', padding: '10px' }}>
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Interacting regions:</b>
                        </Typography>
                        {item.data.interacting_regions.map((interacting_region) => (
                          <StudyChip 
                            key={interacting_region}
                            index={index}
                            label={interacting_region}
                            included={state.items[0].data.interacting_regions.includes(interacting_region)}
                          />
                        ))}
                      </div>}

                      {c_aspects.includes("Scenario years") && <div style={{ marginBottom: '10px', padding: '10px' }}>
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Scenario years:</b>
                        </Typography>
                        {item.data.scenario_years.map((scenario_year) => (
                          <StudyChip 
                            key={scenario_year}
                            index={index}
                            label={scenario_year}
                            included={state.items[0].data.scenario_years.includes(scenario_year)}
                          />
                        ))}
                      </div>}

                      {c_aspects.includes("Input datasets") && <div style={{ marginBottom: '10px', padding: '10px' }}>
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Input datasets:</b>
                        </Typography>
                        {item.data.input_datasets.map((input_dataset) => (
                          <StudyChip 
                            key={input_dataset}
                            index={index}
                            label={input_dataset}
                            included={state.items[0].data.input_datasets.includes(input_dataset)}
                          />
                        ))}
                      </div>}

                      {c_aspects.includes("Output datasets") && <div style={{ marginBottom: '10px', padding: '10px' }}>
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Output datasets:</b>
                        </Typography>
                        {item.data.output_datasets.map((output_dataset) => (
                          <StudyChip 
                            key={output_dataset}
                            index={index}
                            label={output_dataset}
                            included={state.items[0].data.output_datasets.includes(output_dataset)}
                          />
                        ))}
                      </div>}

                    </div> 

                    </div> 
                  )}
                </Draggable>
              ))} 
            </div> 
            )}
        </Droppable>
      </DragDropContext> 
    </div> 
  );
}