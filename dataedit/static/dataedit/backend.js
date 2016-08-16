__type__: 'OEP-Backend' // e.g. elasticsearch

// Initial load of dataset including initial set of records
fetch: function(dataset)
{
    $.post("localhost:8080/api/search", function(data, status){
        alert("Data: " + data + "\nStatus: " + status);
    });
    {
      // (optional) Set of record data
      // Either an array of arrays *or* an array of objects corresponding to initial set of records for this object
      // May not provided if data only returned by query
      records: [...]

      // (optional) Set of field data
      // Either an array of string or an array of objects corresponding to Field specification (see `Field` above)
      fields: { ... } // as per recline.Model.Field

      // (optional) metadata fields to set on the Dataset object
      metadata: { title: ..., id: ... etc }

      // boolean indicating whether to use a local memory store for managing this dataset
      useMemoryStore: true
    }
}

// Query the backend for records returning them in bulk.
// This method will be used by the Dataset.query method to search the backend
// for records, retrieving the results in bulk.
query: function(queryObj, dataset)

// Save changes to the backend
save: function(changes, dataset)