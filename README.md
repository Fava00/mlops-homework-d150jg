# My MLOps Project

Your semester-long project for **Lifecycle of Artificial Intelligence Systems**.
You start from this minimal, working baseline and grow it into a full MLOps
project across HW1–HW5 — see [`HOMEWORK.md`](HOMEWORK.md).

This repo is **separate from the course materials**. The course repo (lectures,
labs, datasets, homework briefs) you read and do the labs in; *this* repo is your
own project, on your own dataset, and is what gets graded.

## What's here

```
src/mlops_project/   config.py · data.py · model.py · cli.py   (a simple baseline pipeline)
src/main.py          entry point
tests/               smoke tests that pass on synthetic data (no dataset needed)
data/                put your dataset here (see data/README.md)
docs/                DATA_DICTIONARY.md (fill it in) + your proposal
.env.example         configuration — copy to .env
```

The baseline trains a scikit-learn `StandardScaler` + (logistic or linear)
regression on a CSV you point it at — classification or regression, set by
`PROBLEM_TYPE`. It's deliberately simple; the course is about the lifecycle, not
the model.

## Quick start

```bash
cp .env.example .env          # set DATA_PATH, TARGET_COLUMN, PROBLEM_TYPE
uv sync --all-groups
uv run pytest -v              # green immediately (synthetic data)
# drop your dataset in data/ and:
uv run python src/main.py     # baseline metrics on your data
```

Prerequisites: `uv` (https://docs.astral.sh/uv/) and Python 3.12+ (uv installs it).

## Next

1. Add your dataset to `data/` and document it in `docs/DATA_DICTIONARY.md`.
2. Write your one-page proposal in `docs/proposal.md` (Week 2 milestone).
3. Follow [`HOMEWORK.md`](HOMEWORK.md) from HW1 onward.

## HW1 pipeline

With the services running and the dataset restored, run `uv run dvc repro`.
The three stages can also be run by hand:

```powershell
uv run python -m mlops_project.pipeline prepare
uv run python -m mlops_project.pipeline train
uv run python -m mlops_project.pipeline evaluate
```

`params.yaml` sets the split date and Random Forest hyperparameters. Training
uses observations before 1 July 2012; evaluation uses all subsequent hours.
This is a chronological holdout, and its results describe that particular
future period. The pipeline uses 12 calendar/weather predictors and excludes
the date, row ID and the two components of the target. The date is used only
to establish the split and ordering.

Training logs parameters, the model, Git commit, verified DVC MD5 and Silo
object URI to the `bike-demand-hw1` experiment. Evaluation adds RMSE, MAE and
R² to that same run and writes `metrics/metrics.json`. Run both stages to
finish an experiment. `uv run dvc metrics show` displays the local metrics.
The earlier generic template entry point is retained; use the commands above
for the HW1 pipeline.

## HW1: services and dataset storage

The project uses the UCI hourly bike-sharing data to predict `cnt`, the number
of rentals in an hour. `data/hour.csv` is tracked by DVC rather than Git. Its
pointer is [`data/hour.csv.dvc`](data/hour.csv.dvc): MD5
`bcbdba906e4a9964cfafed8b14549a62`, size **944,753 bytes**, with
**17,379 data rows and 14 columns**. Version one of the pointer named the
original 17-column CSV; version two removes `instant`, `casual` and
`registered` before training.

Copy `.env.example` to `.env` and replace the Silo and PostgreSQL credential
placeholders with unique values. Use a URL-safe PostgreSQL password as explained
in `.env.example`. Start the services with `docker compose up -d --wait`.
Compose builds the tracking server from `mlflow.Dockerfile` on first use.
The long-running services should be healthy; `silo-create-bucket` should exit
successfully with code 0 after creating the data and artifact buckets.

| Service | Host port | Address |
| --- | --- | --- |
| MLflow | 5500 | http://localhost:5500 |
| Silo S3 API | 5510 | http://localhost:5510 |
| Silo console | 5511 | http://localhost:5511 |
| PostgreSQL | 5532 | localhost:5532 |

This is
the same 55xx port block as the course labs, so stop a lab stack before starting
this one. The Compose project has its own explicit name, `bike-demand-hw1`.
Run `docker compose down` to stop it while retaining the data and experiments.
`docker compose down -v` deletes the storage volumes, including DVC objects and
MLflow runs, so it must not be used for a routine shutdown.

For DVC commands, set `AWS_ACCESS_KEY_ID` from `SILO_ACCESS_KEY` and
`AWS_SECRET_ACCESS_KEY` from `SILO_SECRET_KEY` in the Git-ignored `.env`, then
run `uv run dvc push` or `uv run dvc pull`. See [`docs/hw1.md`](docs/hw1.md)
for the PowerShell commands and verification output. Credentials are never
stored in `.dvc/config`.
