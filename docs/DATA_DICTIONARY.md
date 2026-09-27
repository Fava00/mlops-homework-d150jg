# Data Dictionary — UCI Bike sharing dataset (hourly)

Document your data like a domain expert would. You will rarely be the expert on
your data; find and write down that knowledge. See the course example for the
expected depth: `datasets/diabetes-pima.md` in the course materials.

## Overview

- Dataset name / source / license:
    UCI Bike Sharing Dataset, hourly Capital Bikeshare rental counts in Washington, DC. (2011-2012). https://www.kaggle.com/datasets/sriramm2010/uci-bike-sharing-data?resource=download. CC BY-SA 4.0
- Rows / features:
    17379 rows, 17 CSV columns: 13 candidate calendar/weather predictors, a record ID, two rental-count columns, one target. Target leakage, casual+registered=cnt
- Task: regression — predict total rentals in an hour, target column: cnt.
- Target range: 1-977 rentals/hour in the original hourly file, mean is approximately 189.

## Features

| Column | Meaning | Unit | Plausible range | Untrustworthy? (missing/sentinel) | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| instant | Record index | integer ID | 1-17379 | No known missing sentinel | identifier, not an operational input |
| dteday | Date of the observed hour | YYYY-MM-DD | 2011-01-01 to 2012-12-31 | No known missing sentinel | Establish order and chronological train/test splits together with hr column |
| season | Encoded season | category | 1-4 | Invalid outside 1-4 integer | 1=winter, 2=spring, 3=summer, 4=fall |
| yr | Year of observation | category | 0 or 1 | No known missing sentinel | 0=2011, 1=2012 |
| mnth | Month of observation | month number | 1-12 | No known missing sentinel | Cyclical |
| hr | Hour of observation | hour number | 0-23 | No known missing sentinel | 0=midnight, 23=11 pm |
| holiday | Whether the date is a holiday | Boolean | 0 or 1 | No known missing sentinel | 1=holiday, 0=not holiday |
| weekday | Day of the week | category | 0-6 | No known missing sentinel | 0=Sunday through 6=Saturday, Cyclical |
| workingday | Whether date is neither weekend nor holiday |Boolean | 0 or 1 | No known missing sentinel | 1=working day, 0=weekend/holiday, related to weekday and holiday |
| weathersit | Encoded weather conditions | category | 1-4 | Invalid values outside 1-4, integer | 1=clear/few clouds, 2=mist/cloudy, 3=light snow or rain, 4=heavy precipitation or severe conditions |
| temp | Normalized air temperature | normalized °C | 0-1 | 0 can be valid | UCI Scaling: (Temp in °C+8) / 47, not raw celsius value |
| atemp | Normalized perceived temperature | normalized °C | 0-1 | 0 can be valid | UCI Scaling (perc. temperature in °C+16) / 66, Not a raw Celsius value |
| hum | Relative humidity, normalized | fraction | 0-1 | 0 needs investigation, not automatic replacement | Multiply by 100 for percent relative humidity. |
| windspeed | Normalized wind speed | normalized speed | 0-1 | 0 can mean calm wind | Original speed values divided by 67, not specify the speed unit |
| casual | Rentals by casual users during the hour | rentals/hpur | nonnegativ integer | No known missing sentinel | Component of target, exclude from prediction |
| registered | Rentals by registerd users during the hour (target) | rentals/hour | nonnegativ integer | No known missing sentinel | Component of target, exclude from prediction |
| cnt | Total rentals during the hour (target) | rentals/hour | nonnegativ integer | No known missing sentinel | cnt = casual + registered, 0 is possible, but not in original file |


## Known quirks / caveats

- Direct target leakage: cnt = casual ! registered. Never include casual or registered among predictors.

- No reported cell-level missing values, but not every hour is represented. CSV is not guranteed to have an observation for all 24 hours of every day.

- Weather values are normalized. temp, atemp, hum, windspeed do not use physical units in CSV. A zero is not automatically missing-value sentinel. Unexpected ranges should be caught by later.

- Time-dependant demand: commute hours, holidays, weekends, seasons, year-to-year changes affect rentals. Chronological split for realistic future-demand evaluation.


