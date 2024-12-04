from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View  # noqa:F401

from databus.databus import register_oep_table

# Create your views here.


class DatabusRegister(View, LoginRequiredMixin):
    def get(self, request, schema, table):
        return render(
            request,
            "databus/partials/register.html",
            {"schema": schema, "table": table},
        )

    def post(self, request, schema, table):
        if not schema or not table:
            return JsonResponse({"error": "Invalid schema or table"}, status=400)

        try:
            register_oep_table(schema_name=schema, table_name=table, version="initial")
            return render(
                request,
                "databus/partials/register-success.html",
                {"success": f"Table {table} registered in schema {schema}"},
            )
        except Exception as e:
            return HttpResponse({"error": str(e)}, status=500)
