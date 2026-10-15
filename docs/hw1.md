# HW1 evidence

## Local services (R2)

On 15 October 2026 the Compose configuration was extended using the supplied
Week 5 lab stack, which uses the same infrastructure as Week 4. No Week 5
validation functionality is included. The project keeps its existing
`bike-demand-hw1` name and `silo-data` volume so the two stored dataset versions
remain available. The existing Silo image also supplies `mcli` for the bucket
job; the project keeps its `SILO_*` variable names.

```text
docker compose up -d --wait --build
exit code: 0

SERVICE              STATE     HEALTH    EXIT CODE
mlflow               running   healthy   0
postgres             running   healthy   0
silo                 running   healthy   0
silo-create-bucket   exited              0
```

The bucket job now creates both `dvc-storage` and `mlflow-artifacts`, then
exits. MLflow waits for its successful completion and PostgreSQL readiness.
The server uses the course's pinned MLflow 3.13.0 dependencies. Actual passwords
are stored in ignored `.env`; `.env.example` contains placeholders.

## Dataset version 1

The original UCI hourly bike-sharing `data/hour.csv` is the first DVC version.
It has 17,379 data rows and 17 columns. `data/hour.csv.dvc` names MD5
`d50bd5a6f55131e72a7bedc334e2fce1` and size `1156736` bytes. The DVC
remote is `s3://dvc-storage` on the local Silo endpoint
`http://127.0.0.1:5510`. Its object is at
`s3://dvc-storage/files/md5/d5/0bd5a6f55131e72a7bedc334e2fce1`.

The local setup was verified on 14 October 2026:

```text
docker compose up -d --wait
Container bike-demand-hw1-silo-1 Healthy
Container bike-demand-hw1-silo-create-bucket-1 Healthy

uv run dvc push
1 file pushed

docker compose exec -T silo-create-bucket mcli ls silo/dvc-storage/files/md5/d5/0bd5a6f55131e72a7bedc334e2fce1
[2026-10-14 13:10:36 UTC] 1.1MiB STANDARD 0bd5a6f55131e72a7bedc334e2fce1
```

In PowerShell, load credentials into the process before `dvc push` or
`dvc pull`. Do not print them or commit `.env`:

```powershell
$lines = Get-Content .env
$env:AWS_ACCESS_KEY_ID = (($lines | Where-Object { $_ -match '^SILO_ACCESS_KEY=' }) -replace '^SILO_ACCESS_KEY=', '')
$env:AWS_SECRET_ACCESS_KEY = (($lines | Where-Object { $_ -match '^SILO_SECRET_KEY=' }) -replace '^SILO_SECRET_KEY=', '')
uv run dvc push
Remove-Item Env:AWS_ACCESS_KEY_ID,Env:AWS_SECRET_ACCESS_KEY
```

The remote definition in `.dvc/config` contains only the URL and endpoint, not
credentials. `.dvc/config.local`, `.dvc/cache`, `.dvc/tmp`, `.env`, and the raw
CSV are Git-ignored.

### Fresh-clone pull

I cloned commit `5486412` into a new local directory with `git clone --local
--no-hardlinks . <new-directory>`, copied only the Git-ignored `.env` there,
then ran `uv sync --all-groups` and `uv run dvc pull` with the AWS environment
variables set as above. The checkout had no `data/hour.csv` before the pull;
it had `data/hour.csv.dvc`.

```text
DATA_PRESENT=False
POINTER_PRESENT=True
uv run dvc pull
A       data\hour.csv
1 file fetched and 1 file added
Get-FileHash data/hour.csv -Algorithm MD5
MD5  D50BD5A6F55131E72A7BEDC334E2FCE1
(Import-Csv data/hour.csv | Measure-Object).Count
17379
uv run pytest -q
5 passed
```

This proves a fresh checkout can download version one from the existing local
Silo service. The bucket is stored in that service's Docker volume, so a new
machine with an empty Silo volume would need the object copied or a reachable
shared Silo server.

## Dataset version 2

Version two keeps all 17,379 observations but drops `instant` (an arbitrary row
ID), `casual` and `registered`. The latter two add exactly to the target `cnt`
in every row, so retaining them would leak the answer into training. The new
CSV has 14 columns and the pointer records MD5
`bcbdba906e4a9964cfafed8b14549a62`, size `944753` bytes. Its Silo object
is `s3://dvc-storage/files/md5/bc/bdba906e4a9964cfafed8b14549a62`.

```text
uv run dvc status data/hour.csv.dvc
modified: data/hour.csv
uv run dvc add data/hour.csv
uv run dvc push
1 file pushed
```

### Switching between committed versions (R5)

Version one is commit `5486412`; version two is commit `af5f928`. The following
commands were executed, restoring version two at the end:

```text
git checkout 5486412 -- data/hour.csv.dvc
uv run dvc checkout data/hour.csv
M       data\hour.csv
Get-FileHash data/hour.csv -Algorithm MD5
D50BD5A6F55131E72A7BEDC334E2FCE1

git checkout af5f928 -- data/hour.csv.dvc
uv run dvc checkout data/hour.csv
M       data\hour.csv
Get-FileHash data/hour.csv -Algorithm MD5
BCBDBA906E4A9964CFAFED8B14549A62
```

Git selects the pointer; DVC restores the bytes named by that pointer from its
cache. Both hashes were also confirmed present in Silo after extending the
Compose stack.
