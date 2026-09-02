"""Re-runnable benchmarks for the Open Energy Platform.

Each benchmark states what it needs, because they do not agree:

* `bulk_upload` is deliberately dependency-free (standard library only) and
  independent of Django settings -- it measures a live server over the
  network, so it must be runnable from a machine that has the uplink and the
  reference data, not only from a machine that can boot the platform.
* `model_factsheets` is the opposite: it asks Django's own test runner for a
  throwaway database, seeds production's measured shape into it and measures
  in-process, so it needs the platform's settings and a reachable Postgres --
  and nothing else. That is the point: measuring the Model Factsheet list
  page on production costs one of four mod_wsgi processes for ~400 s.
"""
