"""Re-runnable benchmarks for the Open Energy Platform.

Each benchmark states its own requirements, because they do not agree. A
benchmark that measures a live server over the network has to run from a
machine with the uplink and the reference data, not merely from one that can
boot the platform -- so `bulk_upload` is standard-library only and independent
of Django settings. One that measures a view in-process is the opposite:
`model_factsheets` asks Django's own test runner for a throwaway database,
seeds a corpus into it, and needs the platform's settings plus a reachable
Postgres -- and nothing else.

That second kind is the point of `model_factsheets`: measuring the Model
Factsheet list page on production costs one of four mod_wsgi processes for
~400 s, a quarter of the platform for nearly seven minutes.
"""
