"""
# S3 to Datacube Indexing

DAG to periodically/one-shot update explorer and ows schemas in RDS
after a given Dataset has been indexed from S3.

- Run Explorer summaries
- Run ows update ranges for NRT products
- Run ows update ranges for NRT multi-products

This DAG uses k8s executors and pre-existing pods in cluster with relevant tooling
and configuration installed.

The DAG has to be parameterized with S3_Glob and Target product as below.

    "s3_glob": "s3://dea-public-data/cemp_insar/insar/displacement/alos//**/*.yaml",
    "product": "cemp_insar_alos_displacement"

"""
from datetime import datetime, timedelta

import kubernetes.client.models as k8s
from airflow import DAG
from airflow.kubernetes.secret import Secret
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

from infra.variables import DB_HOSTNAME

OWS_CFG_PATH = "/env/config/ows_cfg.py"

DEFAULT_ARGS = {
    "owner": "Pin Jin",
    "depends_on_past": False,
    "start_date": datetime(2020, 3, 4),
    "email": ["pin.jin@ga.gov.au"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "env_vars": {
        "AWS_DEFAULT_REGION": "ap-southeast-2",
        # TODO: Pass these via templated params in DAG Run
        "DB_HOSTNAME": DB_HOSTNAME,
        "DB_DATABASE": "ows-index",
        "WMS_CONFIG_PATH": OWS_CFG_PATH,
        "DATACUBE_OWS_CFG": "config.ows_cfg.ows_cfg",
    },
    # Use K8S secrets to send DB Creds
    # Lift secrets into environment variables for datacube
    "secrets": [
        Secret("env", "DB_USERNAME", "ows-db", "postgres-username"),
        Secret("env", "DB_PASSWORD", "ows-db", "postgres-password"),
    ],
}

INDEXER_IMAGE = "opendatacube/datacube-index:0.0.7"
OWS_IMAGE = "opendatacube/ows:1.8.1"
OWS_CONFIG_IMAGE = "geoscienceaustralia/dea-datakube-config:1.5.1"

OWS_CFG_IMAGEPATH = "/opt/dea-config/dev/services/wms/ows/ows_cfg.py"

# for main container mount
ows_cfg_mount = k8s.V1VolumeMount(
    name="ows-config-volume", mount_path="/env/config", sub_path=None, read_only=False
)

ows_cfg_volume = k8s.V1Volume(name="ows-config-volume")

# for init container mount
cfg_image_mount = k8s.V1VolumeMount(
    mount_path="/env/config", name="ows-config-volume", sub_path=None, read_only=False
)

config_container = k8s.V1Container(
    image=OWS_CONFIG_IMAGE,
    command=["cp"],
    args=[OWS_CFG_IMAGEPATH, OWS_CFG_PATH],
    volume_mounts=[cfg_image_mount],
    name="mount-ows-config",
    working_dir="/opt",
)
dag = DAG(
    "k8s_ows_pod_pin",
    doc_md=__doc__,
    default_args=DEFAULT_ARGS,
    schedule_interval=None,
    catchup=False,
    tags=["k8s"],
)


def print_context(ds):
    print(ds, type(ds))
    if ds:
        print("empty string is also a true?")
    else:
        print("else statement")
    return "Whatever you return gets printed in the logs"


with dag:
    START = DummyOperator(task_id="s3_index_publish")

    BOOTSTRAP = KubernetesPodOperator(
        namespace="processing",
        image=INDEXER_IMAGE,
        cmds=["datacube", "--help"],
        labels={"step": "bootstrap"},
        name="datacube-index",
        task_id="bootstrap-task",
        get_logs=True,
    )

    INDEXING = KubernetesPodOperator(
        namespace="processing",
        image=INDEXER_IMAGE,
        cmds=["s3-to-dc"],
        # Assume kube2iam role via annotations
        # TODO: Pass this via DAG parameters
        annotations={"iam.amazonaws.com/role": "dea-dev-eks-orchestration"},
        # TODO: Collect form JSON used to trigger DAG
        arguments=[
            # "s3://dea-public-data/cemp_insar/insar/displacement/alos//**/*.yaml",
            # "cemp_insar_alos_displacement",
            # Jinja templates for arguments
            "{{ dag_run.conf.s3_glob }}",
            "{{ dag_run.conf.product }}",
        ],
        labels={"step": "s3-to-rds"},
        name="datacube-index",
        task_id="indexing-task",
        get_logs=True,
    )

    UPDATE_RANGES = KubernetesPodOperator(
        namespace="processing",
        image=OWS_IMAGE,
        cmds=["head"],
        arguments=["-n", "50", OWS_CFG_PATH],
        labels={"step": "ows"},
        name="ows-update-ranges",
        task_id="update-ranges-task",
        get_logs=True,
        volumes=[ows_cfg_volume],
        volume_mounts=[ows_cfg_mount],
        init_containers=[config_container],
    )

    COMPLETE = DummyOperator(task_id="all_done")

    # START >> BOOTSTRAP
    # BOOTSTRAP >> INDEXING
    # INDEXING >> UPDATE_RANGES
    # INDEXING >> SUMMARY
    # UPDATE_RANGES >> COMPLETE
    # SUMMARY >> COMPLETE

    run_this = PythonOperator(
        task_id="conf_value_check",
        python_callable=print_context,
        op_args=["{{ dag_run.conf.test_value }}"],
    )

    START >> run_this
    run_this >> COMPLETE
