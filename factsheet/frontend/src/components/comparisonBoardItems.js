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
  padding: 0,
  margin: `0 ${grid}px 0 0`,
  marginTop: '10px',
  marginBottom: '10px',
  background: index === 0 ? '#F6F9FB' : '#FFFFFF',
  width: '30%',
  height: '90%',
  overflow: 'auto',
  border: '1px solid #2972A6',
  ...draggableStyle,
});

const getListStyle = isDraggingOver => ({
  background: isDraggingOver ? 'white' : 'white',
  display: 'flex',
  padding: grid,
  overflow: 'auto',
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
    <div style={{ overflow: 'auto', padding:'10px' }}>
      <DragDropContext onDragEnd={onDragEnd}>
        <Droppable droppableId="droppable" direction="horizontal">
        {(provided, snapshot) => (
            <div
              ref={provided.innerRef}
              style={getListStyle(snapshot.isDraggingOver)}
              {...provided.droppableProps}
            > 
             {state.items.map((item, index) => (
                <Draggable key={item.acronym} draggableId={item.acronym} index={index}>
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

                   <div style= {{  marginBottom: '10px', padding: '10px' }} >
                      <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                        <b>Abstract:</b> 
                      </Typography>
                        {item.data.abstract}
                    </div>

                    {c_aspects.includes("Descriptors") && <div style= {{  marginBottom: '10px', padding: '10px' }} >
                      <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                        <b>Descriptors:</b> 
                      </Typography>
                      {item.data.descriptors.map((descriptor) => (
                        index === 0 ? 
                        <Chip  color="default"  size='small' key={descriptor}  label={descriptor} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                        :
                        state.items[0].data.descriptors.includes(descriptor) ?
                        <Chip  color="success"  size='small' key={descriptor}  label={descriptor} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                        :
                        <Chip  color="error"  size='small' key={descriptor}  label={descriptor} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                      ) )}
                    </div>}
                    
                    {c_aspects.includes("Regions") && <div style= {{  marginBottom: '10px', padding: '10px' }} >
                      <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                        <b>Regions:</b> 
                      </Typography>
                      {item.data.regions.map(region => (
                        index === 0 ? 
                        <Chip color="default" size='small' key={region}  label={region} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                        :
                        state.items[0].data.regions.includes(region) ?
                        <Chip color="success" size='small' key={region}  label={region} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                        :<Chip  color="error" size='small' key={region}  label={region} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                        ) )}
                    </div>
                    }

                    {c_aspects.includes("Interacting regions") && <div style= {{marginBottom: '10px', padding: '10px' }} >
                      <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                        <b>Interacting regions:</b> 
                      </Typography>
                      {item.data.interacting_regions.map(interacting_region => (
                        index === 0 ? 
                        <Chip color="default" size='small' key={interacting_region}  label={interacting_region} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                        :
                        state.items[0].data.interacting_regions.includes(interacting_region) ?
                        <Chip color="success" size='small' key={interacting_region}  label={interacting_region} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                        :
                        <Chip color="error" size='small' key={interacting_region}  label={interacting_region} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                      ) )}
                    </div>}

                    {c_aspects.includes("Scenario years") && <div style= {{ marginBottom: '10px', padding: '10px'}} >
                      <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                        <b>Scenario years:</b> 
                      </Typography>
                      {item.data.scenario_years.map(scenario_year => (
                        index === 0 ? 
                        <Chip color="default" size='small' key={scenario_year}  label={scenario_year} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                        :
                        state.items[0].data.scenario_years.includes(scenario_year) ?
                        <Chip color="success" size='small' key={scenario_year}  label={scenario_year} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                        :
                        <Chip color="error" size='small' key={scenario_year}  label={scenario_year} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                      ) )}
                    </div>}

                   {c_aspects.includes("Input datasets") && <div style= {{ marginBottom: '10px', padding: '10px' }} >
                      <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                        <b>Input datasets:</b> 
                      </Typography>
                      {item.data.input_datasets.map(input_dataset => (
                        index === 0 ? 
                        <Chip color="default" size='small' key={input_dataset}  label={input_dataset} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                        :
                        state.items[0].data.input_datasets.includes(input_dataset) ?
                        <Chip color="success" size='small' key={input_dataset}  label={input_dataset} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                        :
                        <Chip color="error" size='small' key={input_dataset}  label={input_dataset} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                      ) )}
                    </div>}

                   { c_aspects.includes("Output datasets") && <div style= {{  marginBottom: '10px', padding: '10px' }} >
                      <Typography variant="subtitle2" gutterBottom component="div" style={{ marginTop: '5px' }}>
                        <b>Output datasets:</b> 
                      </Typography>
                      {item.data.output_datasets.map(output_dataset => (
                        index === 0 ? 
                        <Chip  color="default" size='small' key={output_dataset}  label={output_dataset} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                        :
                        state.items[0].data.output_datasets.includes(output_dataset) ?
                        <Chip  color="success" size='small' key={output_dataset}  label={output_dataset} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                        :
                        <Chip  color="error" size='small' key={output_dataset}  label={output_dataset} variant="outlined" sx={{ 'marginBottom': '5px', 'marginTop': '5px', 'marginLeft': '5px', backgroundColor: 'white' }}/>
                      ) )}
                    </div>}

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