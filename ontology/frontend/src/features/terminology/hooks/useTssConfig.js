// SPDX-FileCopyrightText: 2025 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useTssConfigCtx } from "../config/TssConfigProvider";

export function useTssConfig() {
  // later you can read from env and merge, but for now just return the ctx
  return useTssConfigCtx();
}
