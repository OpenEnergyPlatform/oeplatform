/*
* SPDX-FileCopyrightText: 2020 Jonas Huber <jh-RLI> © Reiner Lemoine Institut
* SPDX-FileCopyrightText: oeplatform <https://github.com/OpenEnergyPlatform/oeplatform/>
* SPDX-License-Identifier: MIT
*/

var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl)
})