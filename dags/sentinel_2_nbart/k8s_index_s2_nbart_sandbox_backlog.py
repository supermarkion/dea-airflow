"""
# Sentinel-2 indexing automation

DAG index all Sentinel-2 NBART data from S3 into the sandbox database.

This DAG uses k8s executors and in cluster with relevant tooling
and configuration installed.

"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.kubernetes.secret import Secret
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from infra.variables import DB_HOSTNAME
from infra.images import INDEXER_IMAGE
from infra.variables import (
    DB_SANDBOX_DATABASE,
    DB_HOSTNAME,
    DB_SANDBOX_USER_SECRET,
)

DEFAULT_ARGS = {
    "owner": "Kieran Ricardo",
    "depends_on_past": False,
    "start_date": datetime(2020, 6, 14),
    "email": ["kieran.ricardo@ga.gov.au"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "products": "s2a_ard_granule s2b_ard_granule",
    "env_vars": {
        "DB_DATABASE": DB_SANDBOX_DATABASE,
        "DB_HOSTNAME": DB_HOSTNAME,
    },
    # Lift secrets into environment variables
    "secrets": [
        Secret(
            "env",
            "DB_USERNAME",
            DB_SANDBOX_USER_SECRET,
            "postgres-username",
        ),
        Secret(
            "env",
            "DB_PASSWORD",
            DB_SANDBOX_USER_SECRET,
            "postgres-password",
        ),
    ],
}


dag = DAG(
    "k8s_index_s2_nbart_sandbox_backlog",
    default_args=DEFAULT_ARGS,
    doc_md=__doc__,
    schedule_interval="@weekly",
    catchup=False,
    tags=["k8s", "s2_nbart"],
)

with dag:
    for year in range(2015, 2022):
        for i, quarter in enumerate(["0[123]", "0[456]", "0[789]", "1[012]"]):

            INDEXING = KubernetesPodOperator(
                namespace="processing",
                image=INDEXER_IMAGE,
                image_pull_policy="Always",
                arguments=[
                    "s3-to-dc",
                    "--skip-lineage",
                    "--allow-unsafe",
                    "--skip-check",
                    "--update-if-exists",
                    "--no-sign-request",
                    "{% raw %}s3://dea-public-data/baseline/s2[ab]_ard_granule/{% endraw %}"
                    + f"{year}-{quarter}"
                    + "{% raw %}-*/*/eo3-ARD-METADATA.odc-metadata.yaml{% endraw %}",
                    dag.default_args["products"],
                ],
                labels={"step": "s3-dc-indexing"},
                name="datacube-index",
                task_id=f"indexing-task-{year}-Q{i+1}",
                get_logs=True,
                is_delete_operator_pod=True,
            )
