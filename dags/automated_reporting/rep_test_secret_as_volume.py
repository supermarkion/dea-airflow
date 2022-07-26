"""
Dev Dag
"""

import datetime
from airflow import DAG
from airflow.kubernetes.secret import Secret
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)

secret_volume = Secret(
    deploy_type="volume",
    # Path where we mount the secret as volume
    deploy_target="/var/secrets/lpgs",
    # Name of Kubernetes Secret
    secret="lpgs-port-forwarder",
    # Key in the form of service account file name
    key="PORT_FORWARDER_KEY",
)

YESTERDAY = datetime.datetime.now() - datetime.timedelta(days=1)

default_args = {
    "owner": "Ramkumar Ramagopalan",
    "depends_on_past": True,
    "start_date": YESTERDAY,
    "email": ["ramkumar.ramagopalan@ga.gov.au"],
    "email_on_failure": True,
    "email_on_retry": False,
}

secret_env_db_host = Secret(
    deploy_type="env",
    deploy_target="DB_HOST",
    secret="reporting-nci-odc-db",
    key="DB_HOST",
)

secret_env_db_name = Secret(
    deploy_type="env",
    deploy_target="DB_NAME",
    secret="reporting-nci-odc-db",
    key="DB_NAME",
)

secret_env_db_port = Secret(
    deploy_type="env",
    deploy_target="DB_PORT",
    secret="reporting-nci-odc-db",
    key="DB_PORT",
)

secret_env_db_user = Secret(
    deploy_type="env",
    deploy_target="DB_USER",
    secret="reporting-nci-odc-db",
    key="DB_USER",
)

secret_env_db_password = Secret(
    deploy_type="env",
    deploy_target="DB_PASSWORD",
    secret="reporting-nci-odc-db",
    key="DB_PASSWORD",
)

dag = DAG(
    "rep_test_secret_as_volume",
    description="composer_sample_kubernetes_pod ",
    tags=["reporting_dev"],
    default_args=default_args,
    schedule_interval=None,
)

with dag:
    JOBS_SSH_CONN = [
        "echo try ssh tunnel $(date)",
        "apt update -y",
        "apt install -y openssh-server",
        "apt install -y ca-certificates",
        "apt-get install -y postgresql-client",
        "mkdir -p ~/.ssh",
        "cat /var/secrets/lpgs/PORT_FORWARDER_KEY > ~/.ssh/identity_file.pem",
        "chmod 0400 ~/.ssh/identity_file.pem",
        "ssh -o StrictHostKeyChecking=no -f -N -i ~/.ssh/identity_file.pem\
             -L 54320:$DB_HOST:$DB_PORT $NCI_TUNNEL_USER@$NCI_TUNNEL_HOST",
        "echo tunnel established",
        "PGPASSWORD=$DB_PASSWORD psql -h localhost -p 54320 -U $DB_USER \
            $DB_NAME -c 'select count(*) from agdc.dataset_type'",
    ]
    kubernetes_secret_vars_ex = KubernetesPodOperator(
        namespace="processing",
        image="python:3.8-slim-buster",
        arguments=["bash", "-c", " &&\n".join(JOBS_SSH_CONN)],
        name="checksecret",
        do_xcom_push=False,
        is_delete_operator_pod=True,
        in_cluster=True,
        task_id="check_secret",
        get_logs=True,
        secrets=[
            secret_volume,
            secret_env_db_host,
            secret_env_db_name,
            secret_env_db_port,
            secret_env_db_user,
            secret_env_db_password,
        ],
    )
    kubernetes_secret_vars_ex
