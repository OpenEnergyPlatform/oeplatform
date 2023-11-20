import React, { useState } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import Typography from '@mui/material/Typography';
import StudyChip from '../styles/oep-theme/components/studyChip';
import palette from '../styles/oep-theme/palette';
import variables from '../styles/oep-theme/variables';

const reorder = (list, startIndex, endIndex) => {
  const result = Array.from(list);
  const [removed] = result.splice(startIndex, 1);
  result.splice(endIndex, 0, removed);
  return result;
};

const aspectStyle = { 
  marginBottom: variables.spacing[0],
  padding: variables.spacing[3],
  color: palette.text.primary,
  fontSize: variables.fontSize.sm,
  lineHeight: variables.lineHeight.sm
};

const getItemStyle = (isDragging, draggableStyle, index) => ({
  userSelect: 'none',
  padding: variables.spacing[0],
  margin: `${variables.spacing[0]} ${variables.spacing[3]} ${variables.spacing[0]} ${variables.spacing[0]}`,
  background: index === 0 ? palette.background.lighter : palette.background.white,
  width: '27rem',
  minWidth: '27rem',
  height: '100%',
  overflow: 'auto',
  border: variables.border.light,
  borderRadius: variables.borderRadius,
  ...draggableStyle,
});

const getListStyle = isDraggingOver => ({
  background: isDraggingOver ? 'white' : 'white',
  display: 'flex',
  overflow: 'auto',
  width: '100%',
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
    <div style={{ overflow: 'auto', marginBottom: variables.spacing[6] }}>
      <DragDropContext onDragEnd={onDragEnd}>
        <Droppable
          droppableId="droppable"
          direction="horizontal"
        >
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
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent:'center', height: '4rem', marginBottom: variables.spacing[3], backgroundColor: index === 0 ? palette.background.highlight : palette.background.lighter,  color: index === 0 ? palette.primary.contrastText : palette.text.primary }} >
                    
                      <Typography variant="h6">
                        { index === 0 ? <b>{item.acronym}</b> : item.acronym }
                      </Typography>
                      <Typography variant="caption">
                      { index === 0 ? 'Base scenario' : ''  }
                      </Typography>
                    </div> 

                    <div style={{ height: '60vh',overflow: 'auto', }}> 

                    
                      {c_aspects.includes("Study name") && <div style= {aspectStyle} >
                        <Typography variant="subtitle2" gutterBottom component="div">
                          <b>Study name:</b> 
                        </Typography>
                        <Typography variant="body2">
                          {item.data.study_label}
                        </Typography>
                      </div>}

                      {c_aspects.includes("Study abstract") &&<div style= {aspectStyle} >
                        <Typography variant="subtitle2" gutterBottom component="div">
                          <b>Study abstract:</b> 
                        </Typography>
                        <Typography variant="body2">
                          {item.data.study_abstract}
                        </Typography>
                      </div>}

                      {c_aspects.includes("Scenario abstract") && <div style= {{  marginBottom: '10px', padding: '10px' }} >
                        <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                          <b>Scenario abstract:</b> 
                        </Typography>
                        <Typography variant="body2">
                          {item.data.abstract}
                        </Typography>
                      </div>}

                      {c_aspects.includes("Descriptors") && <div style={aspectStyle}>
                        <Typography variant="subtitle2" gutterBottom component="div">
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

                      {c_aspects.includes("Regions") && <div style={aspectStyle}>
                        <Typography variant="subtitle2" gutterBottom component="div">
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

                      {c_aspects.includes("Interacting regions") && <div style={aspectStyle}>
                        <Typography variant="subtitle2" gutterBottom component="div">
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

                      {c_aspects.includes("Scenario years") && <div style={aspectStyle}>
                        <Typography variant="subtitle2" gutterBottom component="div">
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

                      {c_aspects.includes("Input datasets") && <div style={aspectStyle}>
                        <Typography variant="subtitle2" gutterBottom component="div">
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

                      {c_aspects.includes("Output datasets") && <div style={aspectStyle}>
                        <Typography variant="subtitle2" gutterBottom component="div">
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