// SPDX-FileCopyrightText: 2025 Adel Memariani <https://github.com/adelmemariani> © Otto-von-Guericke-Universität Magdeburg
// SPDX-FileCopyrightText: 2025 Bryan Lancien <https://github.com/bmlancien> © Reiner Lemoine Institut
// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import Typography from '@mui/material/Typography';
import StudyChip from '../styles/oep-theme/components/studyChip';
import palette from '../styles/oep-theme/palette.js';
import variables from '../styles/oep-theme/variables.js';
import StudyKeywords from './scenarioBundleUtilityComponents/StudyDescriptors';
import handleOpenURL from './scenarioBundleUtilityComponents/handleOnClickTableIRI.jsx';
import HtmlTooltip from '../styles/oep-theme/components/tooltipStyles';

const OEP_ORIGIN = window.location.origin;

// Convert dataset dict -> absolute or external URL
function datasetHref(ds) {
  if (!ds?.url) return null;
  if (typeof ds.url !== 'string') return null;

  if (ds.url.startsWith('http://') || ds.url.startsWith('https://')) return ds.url;
  return `${OEP_ORIGIN}/${ds.url.replace(/^\/+/, '')}`;
}

function datasetDisplay(ds) {
  return ds?.label || ds?.table_name || ds?.external_id || ds?.url || 'Dataset';
}

// Backwards-compatible: accept old tuple format too
function normalizeDatasetItem(item) {
  if (!item) return {};
  if (Array.isArray(item)) {
    const [label, url, tableName] = item;
    return {
      label,
      url,
      kind: tableName ? 'oep_table' : 'unknown',
      table_name: tableName || null,
      external_id: null,
    };
  }
  return item;
}

// stable dataset id for React keys & comparisons
function datasetId(ds) {
  if (!ds) return null;
  // prefer table_name for internal
  if (ds.kind === 'oep_table' && ds.table_name) return `tbl:${ds.table_name}`;
  // for databus / external use URL
  if (ds.url) return `url:${ds.url}`;
  if (ds.external_id) return `ext:${ds.external_id}`;
  if (ds.label) return `lbl:${ds.label}`;
  return null;
}

// robust inclusion check relative to base scenario (index 0)
function isDatasetIncluded(baseDatasets, ds) {
  const base = (baseDatasets || []).map(normalizeDatasetItem);

  // internal: compare table_name if present
  if (ds.kind === 'oep_table' && ds.table_name) {
    return base.some(b => (b.kind === 'oep_table' && b.table_name && b.table_name === ds.table_name));
  }

  // external/databus: compare url
  if (ds.url) {
    return base.some(b => b.url && b.url === ds.url);
  }

  // fallback: compare external_id or label
  if (ds.external_id) {
    return base.some(b => b.external_id && b.external_id === ds.external_id);
  }
  if (ds.label) {
    return base.some(b => b.label && b.label === ds.label);
  }
  return false;
}


function resolveStudyDescriptor(value) {
  if (!value) return { label: '-', iri: null };

  const v = String(value);

  // StudyKeywords entries look like: [label, iri]
  const byLabel = StudyKeywords.find(([label]) => label === v);
  if (byLabel) return { label: byLabel[0], iri: byLabel[1] };

  const byIri = StudyKeywords.find(([, iri]) => iri === v);
  if (byIri) return { label: byIri[0], iri: byIri[1] };

  // Fallback: show a human-ish short label, still click the original value if it looks like a URL
  const short = v.split('/').pop()?.replace(/_/g, ' ') || v;
  const iri = v.startsWith('http://') || v.startsWith('https://') ? v : null;

  return { label: short, iri };
}

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

  const baseScenario = state.items[0];

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
                const uid = String(item?.data?.uid || '');
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
                        {/* header */}
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
                              <Typography variant="subtitle2" gutterBottom component="div">
                                <b>Study name:</b>
                              </Typography>
                              <Typography variant="body2">
                                {item?.data?.study_label || '-'}
                              </Typography>
                            </div>
                          )}

                          {c_aspects.includes('Study abstract') && (
                            <div style={aspectStyle}>
                              <Typography variant="subtitle2" gutterBottom component="div">
                                <b>Study abstract:</b>
                              </Typography>
                              <Typography variant="body2">
                                {item?.data?.study_abstract || '-'}
                              </Typography>
                            </div>
                          )}

                          {c_aspects.includes('Scenario abstract') && (
                            <div style={aspectStyle}>
                              <Typography variant="subtitle2" gutterBottom component="div">
                                <b>Scenario abstract:</b>
                              </Typography>
                              <Typography variant="body2">
                                {item?.data?.abstract || '-'}
                              </Typography>
                            </div>
                          )}

                          {c_aspects.includes('Study descriptors') && (
                            <div style={aspectStyle}>
                              <Typography variant="subtitle2" gutterBottom component="div">
                                <b>Study descriptors:</b>
                              </Typography>
                              {(() => {
                                const baseResolved = (baseScenario?.data?.study_descriptors || []).map(resolveStudyDescriptor);
                                const baseIriSet = new Set(baseResolved.map(x => x.iri).filter(Boolean));
                                const baseLabelSet = new Set(baseResolved.map(x => x.label).filter(Boolean));

                                return (item?.data?.study_descriptors || []).map((raw) => {
                                  const { label, iri } = resolveStudyDescriptor(raw);

                                  // included: prefer iri comparison, fallback to label comparison
                                  const included = (iri && baseIriSet.has(iri)) || baseLabelSet.has(label);

                                  return (
                                    <StudyChip
                                      key={iri || label}
                                      index={index}
                                      label={label}
                                      included={included}
                                      onClick={() => {
                                        if (iri) handleOpenURL(iri);
                                      }}
                                    />
                                  );
                                });
                              })()}
                            </div>
                          )}

                          {c_aspects.includes('Scenario types') && (
                            <div style={aspectStyle}>
                              <Typography variant="subtitle2" gutterBottom component="div">
                                <b>Scenario types:</b>
                              </Typography>

                              {(item?.data?.scenario_descriptors || []).map((scenario_descriptor) => (
                                <StudyChip
                                  key={scenario_descriptor?.[0] || JSON.stringify(scenario_descriptor)}
                                  index={index}
                                  label={scenario_descriptor?.[0] || '-'}
                                  included={(baseScenario?.data?.scenario_descriptors || []).some(
                                    (desc) => desc?.[0] && scenario_descriptor?.[0] && desc[0] === scenario_descriptor[0]
                                  )}
                                  onClick={() => {
                                    if (scenario_descriptor?.[1]) handleOpenURL(scenario_descriptor[1]);
                                  }}
                                />
                              ))}
                            </div>
                          )}

                          {c_aspects.includes('Regions') && (
                            <div style={aspectStyle}>
                              <Typography variant="subtitle2" gutterBottom component="div">
                                <b>Regions:</b>
                              </Typography>
                              {(item?.data?.regions || []).map((region) => (
                                <StudyChip
                                  key={region}
                                  index={index}
                                  label={region}
                                  included={(baseScenario?.data?.regions || []).includes(region)}
                                />
                              ))}
                            </div>
                          )}

                          {c_aspects.includes('Interacting regions') && (
                            <div style={aspectStyle}>
                              <Typography variant="subtitle2" gutterBottom component="div">
                                <b>Interacting regions:</b>
                              </Typography>
                              {(item?.data?.interacting_regions || []).map((interacting_region) => (
                                <StudyChip
                                  key={interacting_region}
                                  index={index}
                                  label={interacting_region}
                                  included={(baseScenario?.data?.interacting_regions || []).includes(interacting_region)}
                                />
                              ))}
                            </div>
                          )}

                          {c_aspects.includes('Scenario years') && (
                            <div style={aspectStyle}>
                              <Typography variant="subtitle2" gutterBottom component="div">
                                <b>Scenario years:</b>
                              </Typography>
                              {(item?.data?.scenario_years || []).map((scenario_year) => (
                                <StudyChip
                                  key={String(scenario_year)}
                                  index={index}
                                  label={String(scenario_year)}
                                  included={(baseScenario?.data?.scenario_years || []).some(
                                    y => String(y) === String(scenario_year)
                                  )}
                                />
                              ))}
                            </div>
                          )}

                          {c_aspects.includes('Input datasets') && (
                            <div style={aspectStyle}>
                              <Typography variant="subtitle2" gutterBottom component="div">
                                <b>Input datasets:</b>
                              </Typography>

                              {(item?.data?.input_datasets || [])
                                .map(normalizeDatasetItem)
                                .map((ds, idx2) => {
                                  const href = datasetHref(ds);
                                  const label = datasetDisplay(ds);
                                  const key = datasetId(ds) || `input-${uid}-${idx2}`;

                                  return (
                                    <HtmlTooltip
                                      key={key}
                                      style={{ marginLeft: '10px' }}
                                      placement="top"
                                      title={
                                        <React.Fragment>
                                          <div>
                                            {label}
                                            {ds.kind === 'databus' ? ' (Databus)' : ''}
                                          </div>
                                          {ds.table_name && <div><b>Table:</b> {ds.table_name}</div>}
                                          {ds.external_id && <div><b>External ID:</b> {ds.external_id}</div>}
                                          {href && <div style={{ wordBreak: 'break-all' }}>{href}</div>}
                                        </React.Fragment>
                                      }
                                    >
                                      <div>
                                        <StudyChip
                                          index={index}
                                          label={label}
                                          included={isDatasetIncluded(baseScenario?.data?.input_datasets, ds)}
                                          onClick={() => {
                                            if (href) handleOpenURL(href);
                                          }}
                                        />
                                      </div>
                                    </HtmlTooltip>
                                  );
                                })}
                            </div>
                          )}

                          {c_aspects.includes('Output datasets') && (
                            <div style={aspectStyle}>
                              <Typography variant="subtitle2" gutterBottom component="div">
                                <b>Output datasets:</b>
                              </Typography>

                              {(item?.data?.output_datasets || [])
                                .map(normalizeDatasetItem)
                                .map((ds, idx2) => {
                                  const href = datasetHref(ds);
                                  const label = datasetDisplay(ds);
                                  const key = datasetId(ds) || `output-${uid}-${idx2}`;

                                  return (
                                    <HtmlTooltip
                                      key={key}
                                      style={{ marginLeft: '10px' }}
                                      placement="top"
                                      title={
                                        <React.Fragment>
                                          <div>
                                            {label}
                                            {ds.kind === 'databus' ? ' (Databus)' : ''}
                                          </div>
                                          {ds.table_name && <div><b>Table:</b> {ds.table_name}</div>}
                                          {ds.external_id && <div><b>External ID:</b> {ds.external_id}</div>}
                                          {href && <div style={{ wordBreak: 'break-all' }}>{href}</div>}
                                        </React.Fragment>
                                      }
                                    >
                                      <div>
                                        <StudyChip
                                          index={index}
                                          label={label}
                                          included={isDatasetIncluded(baseScenario?.data?.output_datasets, ds)}
                                          onClick={() => {
                                            if (href) handleOpenURL(href);
                                          }}
                                        />
                                      </div>
                                    </HtmlTooltip>
                                  );
                                })}
                            </div>
                          )}
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
