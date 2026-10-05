// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// Dynamic replacement for the former hardcoded `StudyKeywords` array
// (StudyDescriptors.js). Study descriptors now come from the OEO, served by
// `scenario-bundles/populate_factsheets_elements/` as `study_descriptors`,
// strictly the terms annotated `oekg annotation == "study descriptor"`.
// Same shape as before: an array of [label, iri, definition] triples.
//
// The endpoint is fetched once and shared across every consumer via a
// module-level cache (WF-04: one source, one cache).

import { useEffect, useState } from 'react';
import axios from 'axios';
import conf from '../../conf.json';

let cache = null; // resolved [label, iri, definition][] once loaded
let inflight = null; // shared in-flight promise so N mounts trigger one request

function load() {
  if (cache) return Promise.resolve(cache);
  if (!inflight) {
    inflight = axios
      .get(conf.toep + 'scenario-bundles/populate_factsheets_elements/')
      .then(({ data }) => {
        cache = (data && data.study_descriptors) || [];
        return cache;
      })
      .catch(() => {
        inflight = null; // allow a retry on the next mount
        return [];
      });
  }
  return inflight;
}

// Synchronous accessor for non-component code (e.g. plain helper functions).
// Returns [] until the list has loaded; pair with the hook in the component so
// a re-render happens once it arrives.
export function getStudyDescriptors() {
  return cache || [];
}

// React hook: returns the descriptor list, [] until loaded, and re-renders the
// component once the fetch resolves.
export default function useStudyDescriptors() {
  const [descriptors, setDescriptors] = useState(cache || []);
  useEffect(() => {
    let alive = true;
    load().then((d) => {
      if (alive) setDescriptors(d);
    });
    return () => {
      alive = false;
    };
  }, []);
  return descriptors;
}
