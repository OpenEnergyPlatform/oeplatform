// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Vitest config scoped to the suites this repo actually maintains. The
// `include` is deliberately narrow so vitest does not pick up unrelated suites
// (the bootstrap theming specs, the factsheet React tests, etc.). The default
// environment stays `node` for pure store/selectors; suites that need a DOM ask
// for one per file with an `@vitest-environment happy-dom` docblock, so a single
// browser-dependent module cannot slow every other test down.
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: [
      "dataedit/static/peer_review/**/*.test.js",
      "modelview/static/modelview/**/*.test.js",
    ],
    environment: "node",
  },
});
