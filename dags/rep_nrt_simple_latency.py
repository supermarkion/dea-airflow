"""
# Simple latency metric on nrt products: AWS ODC -> AIRFLOW -> Reporting DB

This DAG extracts latest timestamp values for a list of products in AWS ODC. It:
 * Connects to AWS ODC.
 * Runs multiple tasks (1 per product type) querying the latest timestamps for each from AWS ODC.
 * TODO: Inserts a summary of latest timestamps into the reporting DB.

"""

import logging
from datetime import datetime as dt
from datetime import timedelta, timezone

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.hooks.postgres_hook import PostgresHook

from infra.connections import DB_ODC_READER_CONN

log = logging.getLogger("airflow.task")

odc_pg_hook = PostgresHook(postgres_conn_id=DB_ODC_READER_CONN)

default_args = {
    "owner": "Tom McAdam",
    "depends_on_past": False,
    "start_date": days_ago(0),
    "email": ["tom.mcadam@ga.gov.au"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "rep_nrt_simple_latency",
    description="DAG for simple latency metric on nrt products: AWS ODC -> AIRFLOW -> Reporting DB",
    tags=["reporting"],
    default_args=default_args,
    schedule_interval=timedelta(minutes=15),
)

SELECT_BY_PRODUCT_AND_TIME_RANGE = """
    SELECT
        dataset.id,
        dataset.added AS indexed_time,
        agdc.common_timestamp(dataset.metadata #>> '{extent,center_dt}'::text[]) as satellite_acquisition_time,
        agdc.common_timestamp(dataset.metadata #>> '{system_information,time_processed}'::text[]) AS processing_time
    FROM agdc.dataset
        JOIN agdc.dataset_type ON dataset_type.id = dataset.dataset_type_ref
    WHERE
        dataset.archived IS NULL
    AND
        dataset_type.name = %s
    AND
        dataset.added >= %s
    AND
        dataset.added <= %s;
"""

with dag:

    # product list to extract the metric for, could potentially be part of dag configuration and managed in airflow UI
    products_list = ["s2a_nrt_granule", "s2b_nrt_granule"]

    def nrt_simple_latency(execution_date, product_name, **kwargs):
        """
        Task to query AWS ODC with supplied `product_name` and insert a summary of latest timestamps into reporting DB
        """

        log.info(
            "Starting Task for: {}@{}".format(product_name, execution_date.isoformat())
        )

        # open the connection to the AWS ODC and get a cursor
        cursor = odc_pg_hook.get_conn().cursor()

        # caluclate a start and end time for the AWS ODC query
        end_time = execution_date
        start_time = end_time - timedelta(days=3)

        # extact a processing and acquisition timestamps from AWS for product and timerange, print logs of query and row count
        cursor.execute(
            SELECT_BY_PRODUCT_AND_TIME_RANGE, (product_name, start_time, end_time)
        )
        log.info("ODC Executed SQL: {}".format(cursor.query.decode()))
        log.info("ODC query returned: {} rows".format(cursor.rowcount))

        # TODO: Logic to iterate through rows and find the latest processing and satellite aquisition times
        # for row in cursor:
        #     id, indexed_time, satellite_acquisition_time, processing_time = row
        #     print(id, indexed_time.isoformat(), indexed_time.astimezone(timezone.utc).isoformat())

        # TODO: after finding latest processing and satellite aquisition times they will be inserted into reporting database here

    def create_task(product_name):
        """
        Function to generate PythonOperator tasks with id based on `product_name`
        """
        return PythonOperator(
            task_id="nrt-simple-latency_" + product_name,
            python_callable=nrt_simple_latency,
            op_kwargs={"product_name": product_name},
            provide_context=True,
        )

    [create_task(product_name) for product_name in products_list]
