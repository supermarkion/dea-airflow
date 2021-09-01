"""
# DB Backup Utility Tool (Self Serve)
## odc database in RDS backup and store to s3
This DAG backup ODC database data weekly and stores in S3 bucket.

## Note
All list of utility dags here: https://github.com/GeoscienceAustralia/dea-airflow/tree/develop/dags/utility, see Readme

### Restrictions
This dag allows s3 file move between the following buckets

- `"dea-public-data-dev"`
- `"dea-public-data"`
- `"dea-non-public-data"`

## Customisation

    {
        "src_bucket_folder": "s3://dea-public-data-dev/s2be/",
        "dest_bucket_folder": "s3://dea-public-data/derived/s2_barest_earth/"
    }
"""
from datetime import datetime, timedelta

from airflow import DAG

from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from textwrap import dedent
from infra.images import INDEXER_IMAGE
from infra.iam_roles import UTILITY_S3_COPY_MOVE_ROLE
from infra.podconfig import ONDEMAND_NODE_AFFINITY
from infra.variables import AWS_DEFAULT_REGION

DAG_NAME = "utility_s3_move_copy"


# DAG CONFIGURATION
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
        "AWS_DEFAULT_REGION": AWS_DEFAULT_REGION,
    },
}

S3_MOVE_COMMAND = [
    "bash",
    "-c",
    dedent(
        """
            {% if dag_run.conf.get('src_bucket_folder') and dag_run.conf.get('dest_bucket_folder') %}
            aws s3 cp --acl bucket-owner-full-control {{ dag_run.conf.src_bucket_folder }} {{ dag_run.conf.dest_bucket_folder }} --recursive
            {% endif %}
        """
    ),
]

# THE DAG
dag = DAG(
    dag_id=DAG_NAME,
    doc_md=__doc__,
    default_args=DEFAULT_ARGS,
    schedule_interval=None,  # Manual trigger
    catchup=False,
    tags=["k8s", "s3", "self-service"],
)

with dag:
    S3_COPY = KubernetesPodOperator(
        namespace="processing",
        image=INDEXER_IMAGE,
        arguments=S3_MOVE_COMMAND,
        annotations={"iam.amazonaws.com/role": UTILITY_S3_COPY_MOVE_ROLE},
        labels={"step": "utility-s3-move"},
        name="s3-move",
        task_id="s3-move",
        get_logs=True,
        affinity=ONDEMAND_NODE_AFFINITY,
        is_delete_operator_pod=True,
    )