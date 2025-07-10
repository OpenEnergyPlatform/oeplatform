// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import StudyChip from '../styles/oep-theme/components/studyChip';
import palette from '../styles/oep-theme/palette.js';
import variables from '../styles/oep-theme/variables.js';
import StudyKeywords from './scenarioBundleUtilityComponents/StudyDescriptors';
import handleOpenURL from './scenarioBundleUtilityComponents/handleOnClickTableIRI.jsx';
import HtmlTooltip from '../styles/oep-theme/components/tooltipStyles';

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
  lineHeight: variables.lineHeight.sm,
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

const getListStyle = (isDraggingOver) => ({
  background: isDraggingOver ? 'white' : 'white',
  display: 'flex',
  overflow: 'auto',
  width: '100%',
  minHeight: '20rem',
});

export default function ComparisonBoardItems(props) {
  const { elements, c_aspects } = props;

  const [state, setState] = useState({ items: elements });
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setState({ items: elements });
  }, [elements]);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 30); // allow DOM to stabilize
    return () => clearTimeout(timer);
  }, []);

  const onDragEnd = (result) => {
    if (!result.destination || result.destination.index === result.source.index) return;

    const newItems = reorder(state.items, result.source.index, result.destination.index);
    setState({ items: newItems });
  };

  if (!mounted || !state.items?.length) return null;

  return (
    <div style={{ overflow: 'auto', marginBottom: variables.spacing[6] }}>
      <DragDropContext onDragEnd={onDragEnd}>
        <Droppable droppableId="droppable-scenarios" direction="horizontal">
          {(provided, snapshot) => (
            <div
              ref={provided.innerRef}
              {...provided.droppableProps}
              style={getListStyle(snapshot.isDraggingOver)}
            >
              {state.items.map((item, index) => {
                const uid = String(item?.data?.uid);
                if (!uid) return null;

                return (
                  <Draggable key={uid} draggableId={uid} index={index}>
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
                        {/* --- DRAGGABLE CONTENT HERE --- */}
                        <div
                          style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: '4rem',
                            marginBottom: variables.spacing[3],
                            backgroundColor:
                              index === 0
                                ? palette.background.highlight
                                : palette.background.lighter,
                            color:
                              index === 0
                                ? palette.primary.contrastText
                                : palette.text.primary,
                          }}
                        >
                          <Typography variant="h6">
                            {index === 0 ? <b>{item.acronym}</b> : item.acronym}
                          </Typography>
                          <Typography variant="caption">
                            {index === 0 ? 'Base scenario' : ''}
                          </Typography>
                        </div>

                        <div style={{ height: '60vh', overflow: 'auto' }}>
                          {c_aspects.includes('Study name') && (
                            <div style={aspectStyle}>
                              <Typography variant="subtitle2" gutterBottom>
                                <b>Study name:</b>
                              </Typography>
                              <Typography variant="body2">
                                {item.data.study_label}
                              </Typography>
                            </div>
                          )}

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

                      {c_aspects.includes("Study descriptors") && <div style={aspectStyle}>
                        <Typography variant="subtitle2" gutterBottom component="div">
                          <b>Study descriptors:</b>
                        </Typography>
                        {item.data.study_descriptors.map((study_descriptor) => (
                          <StudyChip
                            key={study_descriptor}
                            index={index}
                            label={study_descriptor}
                            included={state.items[0].data.study_descriptors.includes(study_descriptor)}
                            onClick={() => {
                              handleOpenURL((StudyKeywords.find((item) => item[0] === study_descriptor))[1]);
                            }}
                          />
                        ))}
                      </div>}
                      {c_aspects.includes("Scenario types") && <div style={aspectStyle}>
                        <Typography variant="subtitle2" gutterBottom component="div">
                          <b>Scenario types:</b>
                        </Typography>

                        {item.data.scenario_descriptors.map((scenario_descriptor) => (
                          <StudyChip
                            key={scenario_descriptor[0]}
                            index={index}
                            label={scenario_descriptor[0]}
                            included={state.items[0].data.scenario_descriptors.some(desc => desc[0].includes(scenario_descriptor[0]))}
                            onClick={() => {
                              handleOpenURL(scenario_descriptor[1]);
                            }}
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
                          <HtmlTooltip
                           key={input_dataset[0]}
                           style={{ marginLeft: '10px' }}
                           placement="top"
                           title={
                             <React.Fragment>
                               <div>
                                 {input_dataset[0]}
                                 {/* Add any other dataset information here if needed */}
                               </div>
                             </React.Fragment>
                           }
                          >
                            <div>
                              <StudyChip
                                key={input_dataset[0]}
                                index={index}
                                label={input_dataset[0]}
                                included={state.items[0].data.input_datasets.some(ds => ds[2] === input_dataset[2])}
                                onClick={() => {
                                  handleOpenURL(input_dataset[1]);
                                }}
                              />
                            </div>
                          </HtmlTooltip>
                        ))}
                      </div>}

                      {c_aspects.includes("Output datasets") && <div style={aspectStyle}>
                        <Typography variant="subtitle2" gutterBottom component="div">
                          <b>Output datasets:</b>
                        </Typography>
                        {item.data.output_datasets.map((output_dataset) => (
                          <HtmlTooltip
                            key={output_dataset[0]}
                            style={{ marginLeft: '10px' }}
                            placement="top"
                            title={
                              <React.Fragment>
                                <div>
                                  {output_dataset[0]}
                                  {/* Add any other dataset information here if needed */}
                                </div>
                              </React.Fragment>
                            }
                          >
                            <div>
                              <StudyChip
                                key={output_dataset[0]}
                                index={index}
                                label={output_dataset[0]}
                                included={state.items[0].data.output_datasets.some(ds => ds[2] === output_dataset[2])}
                                onClick={() => {
                                  handleOpenURL(output_dataset[1]);
                                }}
                              />
                            </div>
                          </HtmlTooltip>
                        ))}
                      </div>}
                        </div>
                      </div>
                    )}
                  </Draggable>
                );
              })}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </DragDropContext>
    </div>
  );
}
