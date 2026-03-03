// SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
// SPDX-FileCopyrightText: 2025 Johann Wagner <https://github.com/johannwagner>  © Otto-von-Guericke-Universität Magdeburg
//
// SPDX-License-Identifier: AGPL-3.0-or-later

$(".tag-checkbox").on('click', (e) => {
  $(e.target.parentElement).toggleClass("tag-checkbox-checked", e.target.checked);
});
