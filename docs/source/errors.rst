================================
Errors and Response Status Codes
================================

The OEP returns standard http status codes. Not all of them are Errors. There is a full list on Wikipedia (https://en.wikipedia.org/wiki/List_of_HTTP_status_codes ). The ones you may encounter more frequently are:
    * ``200`` **OK** This is the standard response for successful HTTP requests. When using the api to query a table, the OEP will return this status if the table does indeed exist.
    * ``201`` **Created** The OEP will return this e.g. when you have successfully created a table.
    * ``400`` **Bad Request** The OEP cannot process the request, because of a malformed query, use of an unsupported syntax or some other faulty user input.
    * ``403`` **Forbidden** The OEP understands the request, but the current user is not allowed to perform the action. This may be the case when you try to write to a table that is in a different schema than model_draft, you did not log in for a certain action, or you did not provide your key for a data upload.
    * ``404`` **Not Found** The requested resource or page does not exist or is not available.
    * ``500`` **Internal Server Error** Something unexpected happened and no more specific message is suitable. These should be rare, but if they do occur, a developer will receive a mail about it, so they can try to fix the issue.
