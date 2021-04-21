"""
# Sentinel-2_nrt Archiving automation

DAG to periodically archive Sentinel-2 NRT data.

This DAG uses k8s executors and in cluster with relevant tooling
and configuration installed.
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.kubernetes.secret import Secret
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator

from textwrap import dedent

from infra.images import INDEXER_IMAGE
from subdags.subdag_ows_views import ows_update_extent_subdag

from infra.variables import (
    DB_DATABASE,
    DB_HOSTNAME,
    REGION,
    SECRET_ODC_WRITER_NAME,
)
from airflow.operators.subdag_operator import SubDagOperator
from subdags.subdag_explorer_summary import (
    explorer_refresh_stats_subdag,
)
from sentinel_2_nrt.env_cfg import (
    ARCHIVE_CONDITION,
    ARCHIVE_PRODUCTS,
)
from infra.podconfig import ONDEMAND_NODE_AFFINITY


DAG_NAME = "sentinel_2_nrt_archive"

ARCHIVE_BASH_COMMAND = [
    "bash",
    "-c",
    dedent(
        """
        for product in %s; do
            echo "Archiving product: $product"
            datacube dataset search -f csv "product=$product time in %s" > /tmp/to_kill.csv;
            cat /tmp/to_kill.csv | awk -F',' '{print $1}' | sed '1d' > /tmp/to_kill.list;
            echo "Datasets count to be archived"
            wc -l /tmp/to_kill.list;
            cat /tmp/to_kill.list | xargs datacube dataset archive
        done;
    """
    )
    % (ARCHIVE_PRODUCTS, ARCHIVE_CONDITION),
]

# DAG CONFIGURATION
DEFAULT_ARGS = {
    "owner": "Pin Jin",
    "depends_on_past": False,
    "start_date": datetime(2020, 6, 14),
    "email": ["pin.jin@ga.gov.au"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "env_vars": {
        # TODO: Pass these via templated params in DAG Run
        "DB_HOSTNAME": DB_HOSTNAME,
        "DB_DATABASE": DB_DATABASE,
        "AWS_DEFAULT_REGION": REGION,
    },
    # Lift secrets into environment variables
    "secrets": [
        Secret("env", "DB_USERNAME", SECRET_ODC_WRITER_NAME, "postgres-username"),
        Secret("env", "DB_PASSWORD", SECRET_ODC_WRITER_NAME, "postgres-password"),
    ],
}

# THE DAG
dag = DAG(
    dag_id=DAG_NAME,
    doc_md=__doc__,
    default_args=DEFAULT_ARGS,
    schedule_interval="0 1 * * *",  # daily at 1am
    catchup=False,
    tags=["k8s", "sentinel-2", "archive"],
)

with dag:

    ARCHIVE_EXTRANEOUS_DS = KubernetesPodOperator(
        namespace="processing",
        image=INDEXER_IMAGE,
        arguments=ARCHIVE_BASH_COMMAND,
        labels={"step": "ds-arch"},
        name="datacube-dataset-archive",
        task_id="archive-nrt-datasets",
        affinity=ONDEMAND_NODE_AFFINITY,
        get_logs=True,
        is_delete_operator_pod=True,
    )

    OWS_UPDATE_EXTENTS = SubDagOperator(
        task_id="run-ows-update-ranges",
        subdag=ows_update_extent_subdag(
            DAG_NAME, "run-ows-update-ranges", DEFAULT_ARGS
        ),
    )

    EXPLORER_SUMMARY = SubDagOperator(
        task_id="run-cubedash-gen-refresh-stat",
        subdag=explorer_refresh_stats_subdag(
            DAG_NAME, "run-cubedash-gen-refresh-stat", DEFAULT_ARGS
        ),
    )

    ARCHIVE_EXTRANEOUS_DS >> OWS_UPDATE_EXTENTS
    ARCHIVE_EXTRANEOUS_DS >> EXPLORER_SUMMARY
