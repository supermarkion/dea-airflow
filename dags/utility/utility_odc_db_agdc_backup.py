"""
# DB Backup Utility Tool (Self Serve)
## odc database in RDS backup and store to s3
This DAG backup ODC database data weekly and stores in S3 bucket.

## Note
All list of utility dags here: https://github.com/GeoscienceAustralia/dea-airflow/tree/develop/dags/utility, see Readme

## Customisation
This dag does not take `dag_run.conf.` values.
"""
from datetime import date, datetime, timedelta

from airflow import DAG
from airflow.kubernetes.secret import Secret

from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from textwrap import dedent
from infra.images import INDEXER_IMAGE
from infra.variables import (
    SECRET_DBA_ADMIN_NAME,
    AWS_DEFAULT_REGION,
    DB_DATABASE,
    DB_HOSTNAME,
)
from infra.s3_buckets import DB_DUMP_S3_BUCKET
from infra.iam_roles import DB_DUMP_S3_ROLE
from infra.podconfig import ONDEMAND_NODE_AFFINITY

DAG_NAME = "utility_odc_db_dump_agdc_schema_onlyto_s3"


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
        # TODO: Pass these via templated params in DAG Run
        "DB_HOSTNAME": DB_HOSTNAME,
        "DB_DATABASE": DB_DATABASE,
        "AWS_DEFAULT_REGION": AWS_DEFAULT_REGION,
    },
    # Lift secrets into environment variables
    "secrets": [
        Secret("env", "DB_USERNAME", SECRET_DBA_ADMIN_NAME, "postgres-username"),
        Secret("env", "PGPASSWORD", SECRET_DBA_ADMIN_NAME, "postgres-password"),
    ],
}


DUMP_TO_S3_COMMAND = [
    "bash",
    "-c",
    dedent(
        """
            pg_dump -Fc -h $(DB_HOSTNAME) -U $(DB_USERNAME) -d $(DB_DATABASE) -n agdc -n public > {0}
            ls -la | grep {0}
            aws s3 cp --acl bucket-owner-full-control {0} s3://{1}/dea-dev/{0}
        """
    ).format(
        f"odc_agdc_only_{date.today().strftime('%Y_%m_%d')}.pgdump", DB_DUMP_S3_BUCKET
    ),
]

# THE DAG
dag = DAG(
    dag_id=DAG_NAME,
    doc_md=__doc__,
    default_args=DEFAULT_ARGS,
    schedule_interval="@weekly",  # weekly
    catchup=False,
    tags=["k8s", "developer_support", "rds", "s3", "db", "self-service"],
)

with dag:
    DB_DUMP = KubernetesPodOperator(
        namespace="processing",
        image=INDEXER_IMAGE,
        arguments=DUMP_TO_S3_COMMAND,
        annotations={"iam.amazonaws.com/role": DB_DUMP_S3_ROLE},
        labels={"step": "utiliy-dump-odc-db"},
        name="dump-odc-db",
        task_id="dump-odc-db",
        get_logs=True,
        affinity=ONDEMAND_NODE_AFFINITY,
        is_delete_operator_pod=True,
    )