"""
### DEA ODC prod database - Run Explorer Schema Migration

This is a Utility DAG, to be run manually to execute a Datacube Explorer Schema Migration.

It should be run whenever a new release of Datacube Explorer requires a database schema update.

*Note:* There was one of these DAGs for each Explorer instance, but I think we should move to a more
general purpose DAG. This may require switching to a parameterised `pod_template_file` instead of the
current Secrets configuration.

"""

import pendulum
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)
from airflow.kubernetes.secret import Secret
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
from infra.images import EXPLORER_UNSTABLE_IMAGE

local_tz = pendulum.timezone("Australia/Canberra")

# Templated DAG arguments
DB_HOSTNAME = "db-writer"

DEFAULT_ARGS = {
    "owner": "Damien Ayers",
    "depends_on_past": False,
    "start_date": datetime(2020, 10, 3, tzinfo=local_tz),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "env_vars": {
        "AWS_DEFAULT_REGION": "ap-southeast-2",
        "DB_HOSTNAME": DB_HOSTNAME,
        "DB_PORT": "5432",
    },
    # Use K8S secrets to send DB Creds
    # Lift secrets into environment variables for datacube database connectivity
    # Use this db-users to run cubedash update-summary
    "secrets": [
        Secret("env", "DB_DATABASE", "explorer-admin", "database-name"),
        Secret("env", "DB_USERNAME", "explorer-admin", "postgres-username"),
        Secret("env", "DB_PASSWORD", "explorer-admin", "postgres-password"),
    ],
}

dag = DAG(
    "k8s_odc_db_migrate_schema",
    doc_md=__doc__,
    default_args=DEFAULT_ARGS,
    catchup=False,
    concurrency=1,
    max_active_runs=1,
    tags=["k8s", "utility"],
    schedule_interval=None,  # Fully manual migrations
)

affinity = {
    "nodeAffinity": {
        "requiredDuringSchedulingIgnoredDuringExecution": {
            "nodeSelectorTerms": [
                {
                    "matchExpressions": [
                        {
                            "key": "nodetype",
                            "operator": "In",
                            "values": [
                                "ondemand",
                            ],
                        }
                    ]
                }
            ]
        }
    }
}

with dag:
    START = DummyOperator(task_id="odc-db-update-schema")

    # Run update summary
    UPDATE_SCHEMA = KubernetesPodOperator(
        namespace="processing",
        image=EXPLORER_UNSTABLE_IMAGE,
        cmds=["cubedash-gen"],
        arguments=["--init", "-v"],
        labels={"step": "update-schema"},
        name="update-schema",
        task_id="update-schema",
        get_logs=True,
        is_delete_operator_pod=True,
        affinity=affinity,
        # execution_timeout=timedelta(days=1),
    )

    # Task complete
    COMPLETE = DummyOperator(task_id="done")

    START >> UPDATE_SCHEMA
    UPDATE_SCHEMA >> COMPLETE
