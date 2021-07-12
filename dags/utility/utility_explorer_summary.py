"""
## Utility Tool
### explore refresh stats
This is utility is to provide administrators the easy accessiblity to run ad-hoc --refresh-stats

## Note
All list of utility dags here: https://github.com/GeoscienceAustralia/dea-airflow/tree/develop/dags/utility, see Readme

#### default run
    `cubedash-gen --no-init-database --refresh-stats --force-refresh s2a_nrt_granule`
    `cubedash-gen --no-init-database --refresh-stats --force-refresh s2b_nrt_granule`

#### Utility customisation
The DAG can be parameterized with run time configuration `products`

To run with all, set `dag_run.conf.products` to `--all`
otherwise provide products to be refreshed seperated by space, i.e. `s2a_nrt_granule s2b_nrt_granule`
dag_run.conf format:

#### example conf in json format

    {
        "products": "--all"
    }

    or

    {
        "products": "s2a_nrt_granule s2b_nrt_granule"
    }

"""

from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python_operator import PythonOperator

from airflow.kubernetes.secret import Secret
from airflow.operators.subdag_operator import SubDagOperator
from subdags.subdag_explorer_summary import explorer_refresh_operator
from infra.variables import (
    DB_DATABASE,
    DB_HOSTNAME,
    AWS_DEFAULT_REGION,
)
from webapp_update.update_list import (
    EXPLORER_UPDATE_LIST,
)

DAG_NAME = "utility_explorer-refresh-stats"

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
}


# THE DAG
dag = DAG(
    dag_id=DAG_NAME,
    doc_md=__doc__,
    default_args=DEFAULT_ARGS,
    schedule_interval=None,
    catchup=False,
    tags=["k8s", "explorer", "self-service"],
    access_control={"utilityuser": {"can_dag_read", "can_dag_edit"}},
)


def parse_dagrun_conf(products, **kwargs):
    """get dag run product"""
    if products:
        return products
    else:
        return " ".join(EXPLORER_UPDATE_LIST)


SET_REFRESH_PRODUCT_TASK_NAME = "parse_dagrun_conf"

with dag:

    SET_PRODUCTS = PythonOperator(
        task_id=SET_REFRESH_PRODUCT_TASK_NAME,
        python_callable=parse_dagrun_conf,
        op_args=["{{ dag_run.conf.products }}"],
        # provide_context=True,
    )

    EXPLORER_SUMMARY = explorer_refresh_operator(
        xcom_task_id=SET_REFRESH_PRODUCT_TASK_NAME,
    )

    SET_PRODUCTS >> EXPLORER_SUMMARY
