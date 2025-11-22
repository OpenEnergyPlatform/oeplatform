/* eslint-disable max-len */
/*
SPDX-FileCopyrightText: 2025 Christian Winger <https://github.com/wingechr> © Öko-Institut e.V.
SPDX-FileCopyrightText: 2025 Martin Glauer <https://github.com/MGlauer> © Otto-von-Guericke-Universität Magdeburg
SPDX-FileCopyrightText: 2025 Tom Heimbrodt <https://github.com/tom-heimbrodt>

SPDX-License-Identifier: AGPL-3.0-or-later
*/
/* eslint-enable max-len */

var getMapData = function (table, column, bounds, callback) {
  let left = bounds.getEast();
  let right = bounds.getWest();
  let top = bounds.getNorth();
  let bottom = bounds.getSouth();

  window.reverseUrl("api:advanced-search").then((url) => {
    $.ajax({
      url: url,
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({
        query: {
          fields: [
            {
              type: "function",
              function: "ST_AsGeoJson",
              operands: [
                {
                  type: "function",
                  function: "ST_Transform",
                  operands: [
                    {
                      type: "column",
                      column: column,
                    },
                    {
                      type: "value",
                      value: 4326,
                    },
                  ],
                },
              ],
            },
          ],
          from: {
            type: "table",
            table: table,
          },
          where: [
            {
              type: "function",
              function: "ST_IsValid",
              operands: [
                {
                  type: "column",
                  column: column,
                },
              ],
            },
            {
              type: "function",
              function: "ST_Intersects",
              operands: [
                {
                  type: "function",
                  function: "ST_Transform",
                  operands: [
                    {
                      type: "column",
                      column: column,
                    },
                    {
                      type: "value",
                      value: 4326,
                    },
                  ],
                },
                {
                  type: "function",
                  function: "ST_SetSRID",
                  operands: [
                    {
                      type: "function",
                      function: "ST_GeomFromGeoJson",
                      operands: [
                        {
                          type: "value",
                          value: JSON.stringify({
                            type: "Polygon",
                            coordinates: [
                              [
                                [left, top],
                                [right, top],
                                [right, bottom],
                                [left, bottom],
                                [left, top],
                              ],
                            ],
                          }),
                        },
                      ],
                    },
                    {
                      type: "value",
                      value: 4326,
                    },
                  ],
                },
              ],
            },
          ],
          limit: 250,
        },
      }),
      success: callback,
    });
  });
};
