"""
# Produce Landsat C3 ARD on the NCI

The DAG starts ard_scene_select which filters the landsat l1 scenes to send to ARD to process.
It also starts the ARD processing.  ARD processing indexes the ARD output scenes.

The logs are written to NCI.
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.contrib.operators.ssh_operator import SSHOperator
from airflow.operators.dummy_operator import DummyOperator

from sensors.pbs_job_complete_sensor import PBSJobSensor

params = {
    "project": "v10",
    "queue": "copyq",
    "module_ass": "ard-scene-select-py3-dea/20210216",
    "index_arg": "--index-datacube-env "
    "/g/data/v10/projects/c3_ard/dea-ard-scene-select/scripts/prod/ard_env/index-datacube.env",
    "wagl_env": "/g/data/v10/projects/c3_ard/dea-ard-scene-select/scripts/prod/ard_env/prod-wagl.env",
    "config_arg": "",
    "scene_limit": "--scene-limit 400",
    "interim_days_wait": "",
    "products_arg": "",
    "pkgdir_arg": "/g/data/xu18/ga",
    "base_dir": "/g/data/v10/work/c3_ard/",
    "days_to_exclude_arg": "",
    "run_ard_arg": "--run-ard",
}

ssh_conn_id = "lpgs_gadi"
schedule_interval = "0 10 * * *"

# Having the info above as variables and some empty values
# means I can easily test by adding some test code here
# without modifying the code below.


default_args = {
    "owner": "Duncan Gray",
    "depends_on_past": False,  # Very important, will cause a single failure to propagate forever
    "start_date": datetime(2020, 8, 31),
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
    "ssh_conn_id": ssh_conn_id,
    "params": params,
}

dag = DAG(
    "nci_ard",
    doc_md=__doc__,
    default_args=default_args,
    catchup=False,
    schedule_interval=schedule_interval,
    default_view="tree",
    tags=["nci", "landsat_c3"],
)

with dag:
    start = DummyOperator(task_id="start")
    completed = DummyOperator(task_id="completed")

    COMMON = """
        #  ts_nodash timestamp no dashes.
        {% set log_ext = ts_nodash + '/logdir' %}
        {% set work_ext = ts_nodash + '/workdir' %}
        """

    submit_task_id = f"submit_ard"
    submit_ard = SSHOperator(
        task_id=submit_task_id,
        command=COMMON
        + """
        mkdir -p {{ params.base_dir }}{{ work_ext }}
        mkdir -p {{ params.base_dir }}{{ log_ext }}
        qsub -N ard_scene_select \
              -q  {{ params.queue }}  \
              -W umask=33 \
              -l wd,walltime=3:00:00,mem=15GB,ncpus=1 -m abe \
              -l storage=gdata/v10+scratch/v10+gdata/if87+gdata/fj7+scratch/fj7 \
              -P  {{ params.project }} -o {{ params.base_dir }}{{ log_ext }} -e {{ params.base_dir }}{{ log_ext }}  \
              -- /bin/bash -l -c \
                  "module use /g/data/v10/public/modules/modulefiles/; \
                  module use /g/data/v10/private/modules/modulefiles/; \
                  module load {{ params.module_ass }}; \
                  ard-scene-select \
                {{ params.products_arg }} \
                {{ params.config_arg }} \
                  --workdir {{ params.base_dir }}{{ work_ext }} \
                  --pkgdir {{ params.pkgdir_arg }} \
                  --logdir {{ params.base_dir }}{{ log_ext }} \
                  --env {{ params.wagl_env }}  \
                  --project {{ params.project }} \
                  --walltime 10:00:00 \
                  {{ params.index_arg }} \
                  {{ params.scene_limit }} \
                  {{ params.interim_days_wait }} \
                  {{ params.days_to_exclude_arg }} \
                  {{ params.run_ard_arg }} "
        """,
        timeout=60 * 20,
        do_xcom_push=True,
    )

    wait_for_completion = PBSJobSensor(
        task_id=f"wait_for_completion",
        pbs_job_id="{{ ti.xcom_pull(task_ids='%s') }}" % submit_task_id,
        timeout=60 * 60 * 24 * 7,
    )

    start >> submit_ard >> wait_for_completion >> completed
