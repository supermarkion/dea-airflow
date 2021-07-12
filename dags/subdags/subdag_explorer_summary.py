"""
# Explorer cubedash-gen refresh-stats subdag
This subdag can be called by other dags
"""

from airflow import DAG

from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from airflow.kubernetes.secret import Secret
from webapp_update.update_list import EXPLORER_UPDATE_LIST
from infra.podconfig import ONDEMAND_NODE_AFFINITY
from infra.images import EXPLORER_IMAGE
from infra.variables import SECRET_EXPLORER_WRITER_NAME
from infra.pools import DEA_NEWDATA_PROCESSING_POOL

EXPLORER_SECRETS = [
    Secret("env", "DB_USERNAME", SECRET_EXPLORER_WRITER_NAME, "postgres-username"),
    Secret("env", "DB_PASSWORD", SECRET_EXPLORER_WRITER_NAME, "postgres-password"),
]


def explorer_refresh_operator(xcom_task_id=None):
    """
    Expects to be run within the context of a DAG
    """

    if xcom_task_id:
        products = f"{{{{ task_instance.xcom_pull(task_ids='{xcom_task_id}') }}}}"
    else:
        products = " ".join(EXPLORER_UPDATE_LIST)

    EXPLORER_BASH_COMMAND = [
        "bash",
        "-c",
        f"cubedash-gen -v --no-init-database --refresh-stats {products}",
    ]
    return KubernetesPodOperator(
        namespace="processing",
        image=EXPLORER_IMAGE,
        arguments=EXPLORER_BASH_COMMAND,
        secrets=EXPLORER_SECRETS,
        labels={"step": "explorer-refresh-stats"},
        name="explorer-summary",
        task_id="explorer-summary-task",
        get_logs=True,
        is_delete_operator_pod=True,
        affinity=ONDEMAND_NODE_AFFINITY,
        pool=DEA_NEWDATA_PROCESSING_POOL,
    )
