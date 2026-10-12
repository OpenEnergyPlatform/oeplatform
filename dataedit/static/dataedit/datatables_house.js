// SPDX-FileCopyrightText: 2026 Jonas Huber <https://github.com/jh-RLI> © Reiner Lemoine Institut
// SPDX-License-Identifier: AGPL-3.0-or-later

// DataTables on the house table (#2647). Load after jquery.dataTables.min.js
// and dataTables.bootstrap5.min.js, before any table is set up.
//
// The Bootstrap 5 integration's layout, with one change: the table (and,
// when it scrolls, DataTables' scroll head and body) sits inside the house
// table's one wrapper, `.table-container`, which draws its border and round
// corners. The controls above and the pager below stay outside it.
(function ($) {
  $.extend(true, $.fn.dataTable.defaults, {
    dom:
      "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +
      "<'row dt-row'<'col-sm-12'<'table-container'tr>>>" +
      "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
  });
})(jQuery);
