# Run BeyondTouch locally

## View saved results

Download this repository ZIP and unzip it. Open `docs/index.html` in a normal web
browser. Select any example to open its replay. No install, API key or server is
needed for these prebuilt results.

## Recalculate

Use Python 3.12 and install NumPy, pandas and Pillow. Python's standard `unittest`
runner is used, so pytest is not required. GitHub Desktop, Node, a GPU, FFmpeg,
SciPy and Azure credentials are not needed for this metrics pipeline.

### macOS and Linux

Open Terminal in the unzipped BeyondTouch folder:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python Scripts/run_example_suite.py --sample-rate 50 --output outputs/examples --workers 2
python Scripts/verify_example_suite.py --results outputs/examples
```

### Windows

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe Scripts/run_example_suite.py --sample-rate 50 --output outputs/examples --workers 2
.venv\Scripts\python.exe Scripts/verify_example_suite.py --results outputs/examples
```

Open `outputs/examples/index.html` to inspect the recalculated gallery. The suite
can take several minutes because it runs every scenario at two grid resolutions.
Use `--workers 1` if memory or CPU is limited. The supplied results used Python
3.12.14; exact observed package versions are recorded in requirements-tested.txt.
For the same dependency versions, install that file instead of requirements.txt.

For one quicker example first:

```sh
python Scripts/run_movement_sequence.py --output outputs/first
```

That entry point uses the original 10 Hz, 3.5-second fixture. The new 12-example
suite uses 50 Hz and a 3.48-second endpoint. Do not compare them as identical inputs.

To recompute a stored suite window from its files:

```sh
python Scripts/run_movement_sequence.py \
  --home data/examples/BT-SYN-01/home.csv.gz \
  --away data/examples/BT-SYN-01/away.csv.gz \
  --runner Home_11 --receiver Home_10 --carrier Home_8 \
  --start 0 --end 3.48 --output outputs/from-csv
```

This reproduces numeric metrics, but the generic CSV command has no match identity
metadata. Use the suite command to regenerate the complete labelled gallery.

Python installers: https://www.python.org/downloads/
Virtual environments: https://docs.python.org/3/library/venv.html

## Optional local server

If your browser disallows local script files, serve the repository locally:

```sh
python -m http.server 8765 --bind 127.0.0.1
```

Then open http://127.0.0.1:8765/docs/index.html. A restricted execution environment
may prohibit opening a server; a normal local terminal is the intended setup.
