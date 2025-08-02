import * as common from "./peer_review.js";
import { selectState } from './peer_review.js';
window.selectState = selectState;

import { selectNextField } from './navigation.js'
window.selectNextField = selectNextField;

import { selectPreviousField } from './navigation.js'
window.selectPreviousField = selectPreviousField;

import { setGetFieldState } from './state_current_review.js';
import './opr_reviewer.js';
setGetFieldState((fieldKey) => {
  return window.state_dict?.[fieldKey] ?? null;
});
document.addEventListener('DOMContentLoaded', function () {
  common.initCurrentReview(config);
  common.peerReview(config, true);
});