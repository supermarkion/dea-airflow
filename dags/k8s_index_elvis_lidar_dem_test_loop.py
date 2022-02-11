"""
This DAG aims speed up the ELVIS Lidar (Digital Elevation Model) data indexing test loop.

It includes following main steps:

1. load metadata files from s3://elvis-stac bucket (belongs to NLI team, we better not modify files in that bucket)
2. modify the metadata content (will pass this change to NLI team once everyone happy with the DEM products)
3. dump the updated metadata to s3://dea-public-data-dev/projects/elvis-lidar
4. index DEM datasets from s3://dea-public-data-dev/projects/elvis-lidar

To run this Airflow DAG, we need value:

script_path
    Default "https://raw.githubusercontent.com/GeoscienceAustralia/dea-airflow/develop/scripts/elvis_lidar_metadata_changing.py"

We force the user to provide script path before DAG run. In case the Airlfow repo had been hacked and someone can pass any script to run in GA network.

"""

from datetime import datetime, timedelta
from textwrap import dedent

from airflow import DAG
from airflow.kubernetes.secret import Secret
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)

from infra.images import CONFLUX_UNSTABLE_IMAGE
from infra.podconfig import (
    ONDEMAND_NODE_AFFINITY,
)

from infra.variables import (
    WATERBODIES_DEV_USER_SECRET,
)

INDEXER_IMAGE = "538673716275.dkr.ecr.ap-southeast-2.amazonaws.com/opendatacube/datacube-index:0.0.21"

DEFAULT_PARAMS = dict(
    script_path="https://raw.githubusercontent.com/GeoscienceAustralia/dea-airflow/develop/scripts/elvis_lidar_metadata_changing.py",
)

# DAG CONFIGURATION
SECRETS = {
    # Lift secrets into environment variables
    "secrets": [
        Secret(
            "env",
            "AWS_ACCESS_KEY_ID",
            WATERBODIES_DEV_USER_SECRET,
            "AWS_ACCESS_KEY_ID",
        ),
        Secret(
            "env",
            "AWS_SECRET_ACCESS_KEY",
            WATERBODIES_DEV_USER_SECRET,
            "AWS_SECRET_ACCESS_KEY",
        ),
    ],
}
DEFAULT_ARGS = {
    "owner": "Sai Ma",
    "depends_on_past": False,
    "start_date": datetime(2022, 2, 2),
    "email": ["sai.ma@ga.gov.au"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "startup_timeout_seconds": 5 * 60,
    **SECRETS,
}

# THE DAG
dag = DAG(
    "k8s_elvis_lidar_indexing",
    doc_md=__doc__,
    default_args=DEFAULT_ARGS,
    schedule_interval=None,  # triggered only
    catchup=False,
    concurrency=128,
    tags=["k8s", "elvis", "lidar", "dem"],
)


def update_metadata(dag):
    cmd = [
        "bash",
        "-c",
        dedent(
            """
            # Download update script
            echo "Downloading {{{{ dag_run.conf.get("script_path", "{script_path}") }}}}
            wget {{{{ dag_run.conf.get("script_path", "{script_path}") }}}}

            # Push the IDs to the queue.
            python elvis_lidar_metadata_changing.py
            """.format(
                script_path=DEFAULT_PARAMS['script_path'],
            )
        ),
    ]
    return KubernetesPodOperator(
        image=CONFLUX_UNSTABLE_IMAGE,
        dag=dag,
        name="elvis-lidar-update-metadata",
        arguments=cmd,
        image_pull_policy="IfNotPresent",
        labels={"app": "elvis-lidar-indexing"},
        get_logs=True,
        affinity=ONDEMAND_NODE_AFFINITY,
        is_delete_operator_pod=True,
        resources={
            "request_cpu": "1000m",
            "request_memory": "512Mi",
        },
        namespace="processing",
        task_id="elvis-lidar-update-metadata",
    )


S3_TO_DC_CMD = [
    "bash",
    "-c",
    dedent(
        """
        s3-to-dc s3://dea-public-data-dev/projects/elvis-lidar/**/*.json" --absolute --stac --no-sign-request --skip-lineage dem_1m
        """
    ),
]


def index_dataset(dag):
    return KubernetesPodOperator(
        namespace="processing",
        image=INDEXER_IMAGE,
        image_pull_policy="IfNotPresent",
        labels={"step": "s3-to-dc"},
        arguments=S3_TO_DC_CMD,
        name="elvis-lidar-indexing-metadata",
        task_id="elvis-lidar-indexing-metadata",
        get_logs=True,
        affinity=ONDEMAND_NODE_AFFINITY,
        is_delete_operator_pod=True,
    )


with dag:

    update_metadata = update_metadata(dag)
    index_dataset = index_dataset(dag)
    update_metadata >> index_dataset