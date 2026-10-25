# Included data

`examples/` contains twelve authored synthetic match instances. Every instance
includes gzipped Home/Away metric tracking CSVs and an instance.json with a match
ID, run ID, simulated clock, shirt numbers, fictional teams and source description.
All twelve use 25 Hz tracking on a 105 × 68 m pitch. None is a real match or a real
player dataset. `synthetic/` retains the original 10 Hz fixture for the single-run
entry point; it is different from the newer suite.

Gzip compression is lossless and pandas reads these files directly. Do not rename
the files to imply Premier League, World Cup, or real player provenance.

The source code in Scripts/run_example_suite.py generates every included example.
No third-party tracking or footage is redistributed. PFF match files are not
included in Basel's linked repository; Metrica's public games are anonymized and
Last Row warns that its named-player tracking lacks research accuracy.
