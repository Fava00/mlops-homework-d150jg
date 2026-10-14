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
CSV are Git-ignored. A fresh-clone `dvc pull` check and version two will be
recorded after this first pointer commit.
