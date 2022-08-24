var getMapData = function(schema, table, column, bounds, callback) {
  let left = bounds.getEast();
  let right = bounds.getWest();
  let top = bounds.getNorth();
  let bottom = bounds.getSouth();

  //  SELECT ST_AsGeoJSON(ST_Collect(ST_Transform(column, 4326)))
  //  FROM (
  //    SELECT *
  //    FROM schema.table
  //    WHERE ST_IsValid(column)
  //    AND ST_Intersects(ST_Transform(column, 4326), ST_SetSRID(ST_GeomFromGeoJSON(bounds, 4326))
  //    LIMIT 250
  //  ) AS stuff

  $.ajax({
    url: "/api/v0/advanced/search",
    type: "POST",
    contentType: 'application/json',
    data:
            JSON.stringify({
              "query": {
                "fields": [
                  {
                    "type": "function",
                    "function": "ST_AsGeoJson",
                    "operands": [
                      {
                        "type": "function",
                        "function": "ST_Transform",
                        "operands": [
                          {
                            "type": "column",
                            "column": column,
                          },
                          {
                            "type": "value",
                            "value": 4326,
                          },
                        ],
                      },
                    ],
                  },
                ],
                "from": {
                  "type": "table",
                  "schema": schema,
                  "table": table,
                },
                "where": [
                  {
                    "type": "function",
                    "function": "ST_IsValid",
                    "operands": [
                      {
                        "type": "column",
                        "column": column,
                      },
                    ],
                  },
                  {
                    "type": "function",
                    "function": "ST_Intersects",
                    "operands": [
                      {
                        "type": "function",
                        "function": "ST_Transform",
                        "operands": [
                          {
                            "type": "column",
                            "column": column,
                          },
                          {
                            "type": "value",
                            "value": 4326,
                          },
                        ],
                      },
                      {
                        "type": "function",
                        "function": "ST_SetSRID",
                        "operands": [
                          {
                            "type": "function",
                            "function": "ST_GeomFromGeoJson",
                            "operands": [
                              {
                                "type": "value",
                                "value": JSON.stringify({
                                  "type": "Polygon",
                                  "coordinates": [
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
                            "type": "value",
                            "value": 4326,
                          },
                        ],
                      },
                    ],
                  },
                ],
                "limit": 250,

              },
            }),
    success: callback,
  });
};
