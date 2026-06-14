// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
//
// SPDX-License-Identifier: AGPL-3.0-or-later

// P0 of the registry-driven refactor (see Obsidian "10 - Frontend Refactor Plan").
// Fetches the Dimension Property Registry contract from GET /oekg/registry/ once
// per page load and caches it. The contract is the shared vocabulary the
// comparison view uses to build filters + dynamic SPARQL (no hardcoded terms).

import { useEffect, useState } from "react";
import axios from "axios";
import conf from "../../conf.json";

let _cache = null; // module-scope: one fetch per page load
let _inflight = null;

export async function fetchRegistry() {
  if (_cache) return _cache;
  if (!_inflight) {
    _inflight = axios
      .get(conf.dimensionRegistry)
      .then((res) => {
        _cache = res.data;
        return _cache;
      })
      .finally(() => {
        _inflight = null;
      });
  }
  return _inflight;
}

export default function useRegistry() {
  const [registry, setRegistry] = useState(_cache);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    if (!_cache) {
      fetchRegistry()
        .then((r) => active && setRegistry(r))
        .catch((e) => active && setError(e));
    }
    return () => {
      active = false;
    };
  }, []);

  return { registry, loading: !registry && !error, error };
}