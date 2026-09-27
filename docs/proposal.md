# Course Homework Proposal

## 1. Dataset

I will use the UCI Bike Sharing Dataset, specifically the hourly one (hour.csv), which contains hourly rental counts from the Capital Bikeshare system in Washington, DC during 2011-2012, with calendar and weather information. Original file has 17379 rows and 17 columns, 12 numeric/coded predictors for initial model, a date used for splitting, a record ID, two rental-count columns excluded from training and one target.

- Source: https://www.kaggle.com/datasets/sriramm2010/uci-bike-sharing-data?resource=download

- License: CC BY-SA 4.0

- Full definitions and caveats: docs/DATA_DICTIONARY.md

| Column | Meaning and unit | Plausible range/handling |
| - | - | - |
| instant | Record id, integer | Positive integer, exclude |
| dteday | Calendar date | 2011-01-01 to 2012-12-31, split by time |
| season | Coded season category | 1-4 |
| yr | year code | 0=2011, 1=2012 |
| mnth | Month, category | 1-12 |
| hr | Hour of day, hours | 0-23 |
| holiday | Holiday indicator | 0 or 1 |
| weekday | Day-of-week code | 0-6 |
| workingday | Non-weekend, non-holiday indicator | 0 or 1 |
| weathersit | Weather category | 1-4 |
| temp | Normalized air temperature, unitless | 0-1, not raw °C |
| atemp | Normalized perceived temperature, unitless | 0-1, not raw °C|
| hum | Normalized relative humidity, unitless | 0-1 |
| windspeed | Normalized wind speed, unitless | 0-1 |
| casual | Casual rentals, bike/hour | Nonnegatice, exclude(leakage) |
| registered | Registered rentals, bike/hour |  Nonnegatice, exclude(leakage) |
| cnt | Total rentals, bikes/hour | Target, observed 1-977 |

## 2. Prediciton task

My task is supervised regression: predict total bike rentals in an hour (cnt) using time, calendar, weather conditions. An hourly estimate could help the operator anticipate demand and plan bicycle availability. Objective is system-wide hourly demand.

## 3. Suitability check

The 1.1 MB CSV is comfortably small for my 24 GB laptop and suitable for a quick sckóikit-learn baseline. I had confirmed this by local loading and training time. The data has real date axis, making chronological training and testing and later monitoring batches possible. Important caveats are target leakage, wather fields not being normalized and observation covering only 1 system during 2011-2012. I will check missing values and repeated timestamps, the time series should not be assumed to contain every possible hour.

## Base idea

Initial model will be scikit-learn's RandomForestRegressor with 50 estimators, and a fixed random seed for reproducibility. Primary evaluation metric will be Root Mean Squared Error, which expresses prediction errors in bikes rented/ hour and penalizes large errors more heavily. Chronological train/test split will be used to evaluate the model on later observations.

