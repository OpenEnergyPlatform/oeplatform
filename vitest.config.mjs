// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Vitest config scoped to the Open Peer Review frontend. The `include` is
// deliberately narrow so vitest does not pick up unrelated suites (the bootstrap
// theming specs, the factsheet React tests, etc.). Pure store/selectors run in
// the node environment; add an environment override (jsdom/happy-dom) when DOM
// tests are introduced for the UI modules.
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["dataedit/static/peer_review/**/*.test.js"],
    environment: "node",
  },
});