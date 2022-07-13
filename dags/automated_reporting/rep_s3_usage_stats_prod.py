# -*- coding: utf-8 -*-

"""
aws usage stats dag prod
"""

# The DAG object; we'll need this to instantiate a DAG
from airflow import DAG
from airflow.kubernetes.secret import Secret
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from datetime import datetime as dt, timedelta
from infra.variables import REPORTING_IAM_DEA_S3_SECRET
from infra.variables import REPORTING_DB_SECRET

default_args = {
    "owner": "Ramkumar Ramagopalan",
    "depends_on_past": False,
    "start_date": dt(2022, 3, 19),
    "email": ["ramkumar.ramagopalan@ga.gov.au"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "secrets": [
        Secret("env", "ACCESS_KEY", REPORTING_IAM_DEA_S3_SECRET, "ACCESS_KEY"),
        Secret("env", "SECRET_KEY", REPORTING_IAM_DEA_S3_SECRET, "SECRET_KEY"),
        Secret("env", "DB_HOST", REPORTING_DB_SECRET, "DB_HOST"),
        Secret("env", "DB_NAME", REPORTING_DB_SECRET, "DB_NAME"),
        Secret("env", "DB_PORT", REPORTING_DB_SECRET, "DB_PORT"),
        Secret("env", "DB_USER", REPORTING_DB_SECRET, "DB_USER"),
        Secret("env", "DB_PASSWORD", REPORTING_DB_SECRET, "DB_PASSWORD"),
    ],
}

dag = DAG(
    "rep_aws_usage_stats_prod",
    description="DAG for aws usage stats prod",
    tags=["reporting"],
    default_args=default_args,
    schedule_interval="0 14 * * *",  # daily at 1am AEDT
)

with dag:
    JOBS1 = [
        "echo AWS Usage job started: $(date)",
        "pip install ga-reporting-etls==2.0.5",
        "aws-usage-ingestion",
    ]
    aws_s3_usage_stats_ingestion = KubernetesPodOperator(
        namespace="processing",
        image="python:3.8-slim-buster",
        arguments=["bash", "-c", " &&\n".join(JOBS1)],
        name="aws_s3_usage_stats_ingestion",
        is_delete_operator_pod=True,
        in_cluster=True,
        task_id="aws_s3_usage_stats_ingestion",
        get_logs=True,
        env_vars={
            "REPORTING_BUCKET": "s3-server-access-logs-schedule",
        },
        execution_timeout=timedelta(minutes=30),
    )
    aws_s3_usage_stats_ingestion