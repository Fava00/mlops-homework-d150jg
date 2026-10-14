# data/

Put your project dataset here (e.g. `data/dataset.csv`) and set `DATA_PATH` in
`.env`. Until then, `uv run python src/main.py` will tell you the file is
missing — that's expected. The tests run on synthetic data, so `pytest` is green
without a dataset.

From **HW1 (Week 5)**, `hour.csv` is versioned with **DVC + Silo** instead of
being committed directly to Git. This folder contains a `.dvc` pointer; run
`dvc pull` after starting the local Silo stack to restore the raw file.

Document your data in `docs/DATA_DICTIONARY.md` before you start building.
