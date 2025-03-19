/*! 
* SPDX-FileCopyrightText: 2020 Johann Wagner <johannwagner>
* SPDX-FileCopyrightText: 2022 Christian Winger <wingechr>
* SPDX-FileCopyrightText: oeplatform <https://github.com/OpenEnergyPlatform/oeplatform/>
* SPDX-License-Identifier: MIT
*/

$(".tag-checkbox").on('click', (e) => {
  $(e.target.parentElement).toggleClass("tag-checkbox-checked", e.target.checked);
});
