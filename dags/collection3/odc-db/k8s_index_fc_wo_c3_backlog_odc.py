"""
# Landsat Collection-3 indexing automation for odc db

DAG to periodically index/archive Landsat Collection-3 data.

This DAG uses k8s executors and in cluster with relevant tooling
and configuration installed.

"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from airflow.kubernetes.secret import Secret
from airflow.operators.subdag import SubDagOperator
from infra.variables import (
    DB_DATABASE,
    DB_HOSTNAME,
    SECRET_ODC_WRITER_NAME,
    STATSD_HOST,
    STATSD_PORT,
)
from infra.images import INDEXER_IMAGE
from infra.podconfig import ONDEMAND_NODE_AFFINITY


DEFAULT_ARGS = {
    "owner": "Pin Jin",
    "depends_on_past": False,
    "start_date": datetime(2020, 6, 14),
    "email": ["pin.jin@ga.gov.au"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "env_vars": {
        "DB_HOSTNAME": DB_HOSTNAME,
        "DB_DATABASE": DB_DATABASE,
    },
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
    ],
}
TASK_ARGS = {
    "secrets": DEFAULT_ARGS["secrets"],
    "start_date": DEFAULT_ARGS["start_date"],
}


def load_subdag(parent_dag_name, child_dag_name, product, rows, args):
    """
    Make us a subdag to hide all the sub tasks
    """
    subdag = DAG(
        dag_id=f"{parent_dag_name}.{child_dag_name}", default_args=args, catchup=False
    )

    with subdag:
        for row in rows:
            # for path in paths:
            INDEXING = KubernetesPodOperator(
                namespace="processing",
                image=INDEXER_IMAGE,
                image_pull_policy="Always",
                arguments=[
                    "s3-to-dc",
                    "--stac",
                    "--statsd-setting",
                    f"{STATSD_HOST}:{STATSD_PORT}",
                    "--no-sign-request",
                    f"s3://dea-public-data/derivative/{product}/{row}/**/*.json",
                    " ".join(products),
                ],
                labels={"backlog": "s3-to-dc"},
                name="datacube-index-fc-wo-c3-backlog",
                task_id=f"{product}--Backlog-indexing-row--{row}",
                get_logs=True,
                is_delete_operator_pod=True,
                affinity=ONDEMAND_NODE_AFFINITY,
                dag=subdag,
            )
    return subdag


DAG_NAME = "k8s_index_wo_fc_c3_backlog_odc"

dag = DAG(
    dag_id=DAG_NAME,
    default_args=DEFAULT_ARGS,
    schedule_interval="@once",
    tags=["k8s", "landsat_c3", "backlog"],
    catchup=False,
)

with dag:
    # Rows should be from 88 to 116, and paths from 67 to 91
    # paths = range(88, 117)
    rows = range(67, 92)
    products = ["ga_ls_fc_3", "ga_ls_wo_3"]

    for product in products:
        TASK_NAME = f"{product}--backlog"
        index_backlog = SubDagOperator(
            task_id=TASK_NAME,
            subdag=load_subdag(DAG_NAME, TASK_NAME, product, rows, TASK_ARGS),
            default_args=TASK_ARGS,
            dag=dag,
        )
