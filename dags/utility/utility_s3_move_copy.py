"""
# DB Backup Utility Tool (Self Serve)
## s3 copy objects from bucket to another bucket
This DAG copies files from s3 to another s3 using `s5cmd` commands

## Note
All list of utility dags here: https://github.com/GeoscienceAustralia/dea-airflow/tree/develop/dags/utility, see Readme

### Restrictions
This dag allows s3 file move between the following buckets

- `"s3://dea-public-data-dev"`
- `"s3://dea-public-data"`
- `"s3://dea-non-public-data"`

## Customisation

### Flags

- `mv` config acts like a flag, if it is passed, the `cp` command will be replaced with `mv` command
- `dry_run` is enabled by default, if its passed it will be disabled

scenario 1: for dry-run copy from src to destination

    {
        "src_bucket_folder": "s3://dea-public-data-dev/s2be/*",
        "dest_bucket_folder": "s3://dea-public-data/derivative/s2_barest_earth/"
    }

scenario 2: for standard copy from src to destination

    {
        "src_bucket_folder": "s3://dea-public-data-dev/s2be/*",
        "dest_bucket_folder": "s3://dea-public-data/derivative/s2_barest_earth/",
        "dry_run": "False"
    }

scenario 3: for standard copy from src to destination

    {
        "src_bucket_folder": "s3://dea-public-data-dev/s2be/*",
        "dest_bucket_folder": "s3://dea-public-data/derivative/s2_barest_earth/",
        "mv": "True",
        "dry_run": "False"
    }
"""
from datetime import datetime, timedelta

from airflow import DAG

from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from infra.images import S5CMD_IMAGE
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

S3_COPY_COMMAND = [
    "-c",
    "{% if dag_run.conf.get('src_bucket_folder') and dag_run.conf.get('dest_bucket_folder') %}./s5cmd {% if not dag_run.conf.get('dry_run') %}--dry-run{% endif %} {% if dag_run.conf.get('mv') %}mv{% else %}cp{% endif %} --acl bucket-owner-full-control '{{ dag_run.conf.src_bucket_folder }}' {{ dag_run.conf.dest_bucket_folder }}{% endif %}",
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
        image=S5CMD_IMAGE,
        cmds=["/bin/sh"],
        arguments=S3_COPY_COMMAND,
        annotations={"iam.amazonaws.com/role": UTILITY_S3_COPY_MOVE_ROLE},
        labels={"step": "utility-s5cmd-copy"},
        name="s5cmd-copy",
        task_id="s5cmd-copy",
        get_logs=True,
        affinity=ONDEMAND_NODE_AFFINITY,
        is_delete_operator_pod=True,
    )