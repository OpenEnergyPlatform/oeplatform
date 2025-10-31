// SPDX-FileCopyrightText: 2025 Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later
export function updateClientStateDict(fieldKey, state) {
  window.state_dict = window.state_dict ?? {};
  window.state_dict[fieldKey] = state;
}


let getFieldStateImpl = (fieldKey) => {
  console.warn(`getFieldState is not defined yet. Can't get state for fieldKey: ${fieldKey}`);
  return null;
};

export function setGetFieldState(fn) {
  getFieldStateImpl = fn;
}

export function getFieldState(fieldKey) {
  return getFieldStateImpl(fieldKey);
}
