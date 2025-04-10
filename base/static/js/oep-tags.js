// SPDX-FileCopyrightText: 2025 Christian Winger <c@wingechr.de>
// SPDX-FileCopyrightText: 2025 Johann Wagner <johann@wagnerdevelopment.de>
//
// SPDX-License-Identifier: MIT

$(".tag-checkbox").on('click', (e) => {
  $(e.target.parentElement).toggleClass("tag-checkbox-checked", e.target.checked);
});
