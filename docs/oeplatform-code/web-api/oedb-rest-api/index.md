# Rest (http) API

!!! Info "We are still in the process of migrating this document!"
If you are looking for our former ReadTheDocs based documentation: We do not support it anymore and added a redirect to this page here.
Migrating the outdated documentation and updating the content will take some time. Please revisit this page later again.

In the meantime we suggest you to have a look at our Courses & Tutorials available in the [Academy](https://openenergyplatform.github.io/academy/tutorials/).

## What the Rest-API offers

When working with data, it is very helpful to be able to implement programmatic solutions for managing data resources. The Rest API provides such functionality by opening the underlying database of the OEP website via HTTP. Users can access data tables under specific IRI's and retrieve various information artefacts. Following the REST specification, the common JSON format is used to transfer the data. External applications can easily process such JSON data and also upload new data to the database. This document provides information on the so called API Endpoint specification. This Information is relevant to use the CRUD functionality of the REST-API.

## Open API

Below you see a draft version of the OpenAPI-based. It is the documentation for all HTTP-API endpoints and in the future it can be used to test out the API.

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>API Documentation</title>
    <link rel="stylesheet" type="text/css" href="../dist/swagger-ui.css">
    <script src="../dist/swagger-ui-bundle.js"></script>
    <script src="../dist/swagger-ui-standalone-preset.js"></script>
</head>
<body>
<div id="swagger-ui"></div>
<script>
    window.onload = function() {
      // Initialize SwaggerUI
      const ui = SwaggerUIBundle({
        url: "./schema.json",
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        plugins: [
          SwaggerUIBundle.plugins.DownloadUrl
        ],
        layout: "StandaloneLayout"
      })
    }
</script>
</body>
</html>
