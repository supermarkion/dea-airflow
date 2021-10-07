#!/usr/bin/env bash
set -ex

airflow dags list-runs -d deletion_utility_select_dataset_in_years -v > run_delete_dataset_result.txt

if grep -rniw './run_delete_dataset_result.txt' -e 'Failed'; then
   echo "Tests failed, both dag run for delete_datasets_in_years should pass."
   exit 1
fi

airflow dags list-runs -d deletion_utility_datacube_dataset_location -v > run_delete_location_result.txt

if (( $(grep -wc "failed" run_delete_location_result.txt) != 2 )) ; then
   echo "Tests failed, there should be 2 failed dag runs for utility_delete_location"
   exit 1
fi

if (( $(grep -wc "success" run_delete_location_result.txt) != 1 )); then
   echo "Tests failed, there should be 1 success dag run for utility_delete_location"
   exit 1
fi