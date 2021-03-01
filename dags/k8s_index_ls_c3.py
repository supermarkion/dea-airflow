"""
# Landsat Collection-3 indexing automation

DAG to periodically index/archive Landsat Collection-3 data.

This DAG uses k8s executors and in cluster with relevant tooling
and configuration installed.

This DAG takes following input parameters from `k8s_index_ls_c3_config` variable:

 * `index_sqs_queue`: Name of the SQS queue for indexing
 * `archive_sqs_queue`: Name of the SQS queue for archiving
 * `db_hostname`: Name of the DB host
 * `db_database`: Name of the DB

"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.kubernetes.secret import Secret
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.dummy_operator import DummyOperator

DEFAULT_ARGS = {
    "owner": "Damien Ayers",
    "depends_on_past": False,
    "start_date": datetime(2020, 6, 1),
    "email": ["damien.ayers@ga.gov.au"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "index_sqs_queue": "{{ var.json.k8s_index_ls_c3_config.index_sqs_queue }}",
    "archive_sqs_queue": "{{ var.json.k8s_index_ls_c3_config.archive_sqs_queue }}",
    "products": "ga_ls5t_ard_3 ga_ls7e_ard_3 ga_ls8c_ard_3",
    "env_vars": {
        "DB_HOSTNAME": "{{ var.json.k8s_index_ls_c3_config.db_hostname }}",
        "DB_DATABASE": "{{ var.json.k8s_index_ls_c3_config.db_database }}",
    },
    # Lift secrets into environment variables
    "secrets": [
        Secret(
            "env",
            "DB_USERNAME",
            "ows-db",
            "postgres-username",
        ),
        Secret(
            "env",
            "DB_PASSWORD",
            "ows-db",
            "postgres-password",
        ),
        Secret(
            "env",
            "AWS_DEFAULT_REGION",
            "processing-aws-creds-sandbox",
            "AWS_DEFAULT_REGION",
        ),
        Secret(
            "env",
            "AWS_ACCESS_KEY_ID",
            "processing-aws-creds-sandbox",
            "AWS_ACCESS_KEY_ID",
        ),
        Secret(
            "env",
            "AWS_SECRET_ACCESS_KEY",
            "processing-aws-creds-sandbox",
            "AWS_SECRET_ACCESS_KEY",
        ),
    ],
}

from infra.images import INDEXER_IMAGE

dag = DAG(
    "k8s_index_ls_c3",
    doc_md=__doc__,
    default_args=DEFAULT_ARGS,
    schedule_interval="0 */1 * * *",
    catchup=False,
    tags=["k8s", "landsat_c3"],
)

with dag:
    START = DummyOperator(task_id="start-tasks")

    INDEXING = KubernetesPodOperator(
        namespace="processing",
        image=INDEXER_IMAGE,
        image_pull_policy="Always",
        arguments=[
            "sqs-to-dc",
            "--stac",
            "--skip-lineage",
            dag.default_args["index_sqs_queue"],
            dag.default_args["products"],
        ],
        labels={"step": "sqs-dc-indexing"},
        name="datacube-index",
        task_id="indexing-task",
        get_logs=True,
        is_delete_operator_pod=True,
    )

    ARCHIVING = KubernetesPodOperator(
        namespace="processing",
        image=INDEXER_IMAGE,
        image_pull_policy="Always",
        arguments=[
            "sqs-to-dc",
            "--archive",
            dag.default_args["archive_sqs_queue"],
            dag.default_args["products"],
        ],
        labels={"step": "sqs-dc-archiving"},
        name="datacube-archive",
        task_id="archiving-task",
        get_logs=True,
        is_delete_operator_pod=True,
    )

    COMPLETE = DummyOperator(task_id="tasks-complete")

    START >> INDEXING >> COMPLETE
    START >> ARCHIVING >> COMPLETE
