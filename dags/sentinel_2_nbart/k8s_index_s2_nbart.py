"""
# Sentinel-2 indexing automation

DAG to periodically index Sentinel-2 NBART data from SQS Queues into the odc database.

This DAG uses k8s executors and in cluster with relevant tooling
and configuration installed.

"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.kubernetes.secret import Secret
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from infra.sqs_queues import SENTINEL_2_ARD_INDEXING_SQS_QUEUE_NAME_ODC_DB
from infra.variables import (
    DB_DATABASE,
    DB_HOSTNAME,
    SECRET_ODC_WRITER_NAME,
    SENTINEL_2_ARD_INDEXING_AWS_USER_SECRET,
    STATSD_HOST,
    STATSD_PORT,
)

from infra.images import INDEXER_IMAGE

DEFAULT_ARGS = {
    "owner": "Damien Ayers",
    "depends_on_past": False,
    "start_date": datetime(2020, 6, 1),
    "email": ["damien.ayers@ga.gov.au"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "env_vars": {
        "DB_HOSTNAME": DB_HOSTNAME,
        "DB_DATABASE": DB_DATABASE,
    },
    # Lift secrets into environment variables
    "secrets": [
        Secret(
            "env",
            "DB_USERNAME",
            SECRET_ODC_WRITER_NAME,
            "postgres-username",
        ),
        Secret(
            "env",
            "DB_PASSWORD",
            SECRET_ODC_WRITER_NAME,
            "postgres-password",
        ),
        Secret(
            "env",
            "AWS_DEFAULT_REGION",
            SENTINEL_2_ARD_INDEXING_AWS_USER_SECRET,
            "AWS_DEFAULT_REGION",
        ),
        Secret(
            "env",
            "AWS_ACCESS_KEY_ID",
            SENTINEL_2_ARD_INDEXING_AWS_USER_SECRET,
            "AWS_ACCESS_KEY_ID",
        ),
        Secret(
            "env",
            "AWS_SECRET_ACCESS_KEY",
            SENTINEL_2_ARD_INDEXING_AWS_USER_SECRET,
            "AWS_SECRET_ACCESS_KEY",
        ),
    ],
}

with DAG(
    "k8s_index_s2_nbart",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 */1 * * *",
    doc_md=__doc__,
    catchup=False,
    tags=["k8s", "s2_nbart"],
) as dag:

    INDEXING = KubernetesPodOperator(
        namespace="processing",
        image=INDEXER_IMAGE,
        image_pull_policy="Always",
        arguments=[
            "sqs-to-dc",
            "--stac",
            "--statsd-setting",
            f"{STATSD_HOST}:{STATSD_PORT}",
            "--skip-lineage",
            "--absolute",
            SENTINEL_2_ARD_INDEXING_SQS_QUEUE_NAME_ODC_DB,
            "s2a_ard_granule s2b_ard_granule",
        ],
        labels={"step": "sqs-dc-indexing"},
        name="datacube-index-s2-nbart",
        task_id="indexing-task",
        get_logs=True,
        is_delete_operator_pod=True,
    )
