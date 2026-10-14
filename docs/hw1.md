# HW1 evidence

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
