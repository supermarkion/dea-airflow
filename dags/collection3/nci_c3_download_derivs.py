"""

Download derivatives from AWS to NCI and index them into the NCI database

"""

from datetime import datetime
from textwrap import dedent

import pendulum
from airflow import DAG
from airflow.providers.ssh.operators.ssh import SSHOperator

local_tz = pendulum.timezone("Australia/Canberra")

dag = DAG(
    "nci_c3_download_derivs",
    doc_md=__doc__,
    catchup=False,
    tags=["nci", "landsat_c3"],
    default_view="tree",
    start_date=datetime(2021, 1, 20, tzinfo=local_tz),
    default_args=dict(
        do_xcom_push=False,
        ssh_conn_id="lpgs_gadi",
        email=["damien.ayers@ga.gov.au"],
        email_on_failure=True,
        email_on_retry=False,
        owner="Damien Ayers",
        retries=3,
    ),
)

COMMON = dedent(
    """
    set -eux
"""
)

with dag:

    # Need to decide between two options:
    # 1. Use s5cmd, save output of transferred files, index them.
    #
    # 2. Save inventory from Athena/raw. Save NCI files from DB. Compare

    setup = SSHOperator(
        task_id="setup",
        command=dedent(
            COMMON
            + """
            mkdir -p /g/data/v10/work/c3_download_derivs/{{ ts_nodash }}
            """
        ),
    )

    # Sync WOfS directory using a Gadi Data Mover node
    sync_wofs = SSHOperator(
        task_id="sync_wofs",
        # Run on the Gadi Data Mover node, it's specifically spec'd for data transfers, and
        # we use s5cmd to transfer using lots of threads to max out the network pipe, and quickly
        # walk both the S3 tree and the Lustre FS tree.
        remote_host="gadi-dm.nci.org.au",
        # There have been random READ failures when performing this download. So retry a few times.
        # Append to the log file so that we don't lose track of any downloaded files.
        command=dedent(
            COMMON
            + """
            cd /g/data/jw04/ga/ga_ls_wo_3
            time ~/bin/s5cmd --stat cp --if-size-differ 's3://dea-public-data/derivative/ga_ls_wo_3/*' . >> /g/data/v10/work/c3_download_derivs/{{ts_nodash}}/ga_ls_wo_3.download.log
            """
        ),
    )

    # Sync WOfS summary
    sync_wofs_fq_apr_oct = SSHOperator(
        task_id="sync_wofs_fq_apr_oct",
        remote_host="gadi-dm.nci.org.au",
        command=dedent(
            COMMON
            + """
            cd /g/data/jw04/ga/ga_ls_wo_fq_apr_oct_3
            time ~/bin/s5cmd --stat cp --if-size-differ 's3://dea-public-data/derivative/ga_ls_wo_fq_apr_oct_3/*' . >> /g/data/v10/work/c3_download_derivs/{{ts_nodash}}/ga_ls_wo_fq_apr_oct_3.download.log
            """
        ),
    )

    sync_wofs_fq_nov_mar = SSHOperator(
        task_id="sync_wofs_fq_nov_mar",
        remote_host="gadi-dm.nci.org.au",
        command=dedent(
            COMMON
            + """
            cd /g/data/jw04/ga/ga_ls_wo_fq_nov_mar_3
            time ~/bin/s5cmd --stat cp --if-size-differ 's3://dea-public-data/derivative/ga_ls_wo_fq_nov_mar_3/*' . >> /g/data/v10/work/c3_download_derivs/{{ts_nodash}}/ga_ls_wo_fq_nov_mar_3.download.log
            """
        ),
    )

    sync_wofs_fq_cyear = SSHOperator(
        task_id="sync_wofs_fq_cyear",
        remote_host="gadi-dm.nci.org.au",
        command=dedent(
            COMMON
            + """
            cd /g/data/jw04/ga/ga_ls_wo_fq_cyear_3
            time ~/bin/s5cmd --stat cp --if-size-differ 's3://dea-public-data/derivative/ga_ls_wo_fq_cyear_3/*' . >> /g/data/v10/work/c3_download_derivs/{{ts_nodash}}/ga_ls_wo_fq_cyear_3.download.log
            """
        ),
    )

    sync_wofs_fq_myear = SSHOperator(
        task_id="sync_wofs_fq_myear",
        remote_host="gadi-dm.nci.org.au",
        command=dedent(
            COMMON
            + """
            cd /g/data/jw04/ga/ga_ls_wo_fq_myear_3
            time ~/bin/s5cmd --stat cp --if-size-differ 's3://dea-public-data/derivative/ga_ls_wo_fq_myear_3/*' . >> /g/data/v10/work/c3_download_derivs/{{ts_nodash}}/ga_ls_wo_fq_myear_3.download.log
            """
        ),
    )

    # Sync FC directory using a Gadi Data Mover node
    sync_fc = SSHOperator(
        task_id="sync_fc",
        remote_host="gadi-dm.nci.org.au",
        command=dedent(
            COMMON
            + """
            cd /g/data/jw04/ga/ga_ls_fc_3
            time ~/bin/s5cmd --stat cp --if-size-differ 's3://dea-public-data/derivative/ga_ls_fc_3/*' . >> /g/data/v10/work/c3_download_derivs/{{ts_nodash}}/ga_ls_fc_3.download.log
            """
        ),
    )

    # Sync Landsat Geomedian summary
    sync_ls5_gm_cyear = SSHOperator(
        task_id="sync_ls5_gm_cyear",
        remote_host="gadi-dm.nci.org.au",
        command=dedent(
            COMMON
            + """
            cd /g/data/jw04/ga/ga_ls5t_nbart_gm_cyear_3
            time ~/bin/s5cmd --stat cp --if-size-differ 's3://dea-public-data/derivative/ga_ls5t_nbart_gm_cyear_3/*' . >> /g/data/v10/work/c3_download_derivs/{{ts_nodash}}/ga_ls5t_nbart_gm_cyear_3.download.log
            """
        ),
    )

    sync_ls7_gm_cyear = SSHOperator(
        task_id="sync_ls5t_nbart_gm_cyear",
        remote_host="gadi-dm.nci.org.au",
        command=dedent(
            COMMON
            + """
            cd /g/data/jw04/ga/ga_ls7e_nbart_gm_cyear_3
            time ~/bin/s5cmd --stat cp --if-size-differ 's3://dea-public-data/derivative/ga_ls7e_nbart_gm_cyear_3/*' . >> /g/data/v10/work/c3_download_derivs/{{ts_nodash}}/ga_ls7e_nbart_gm_cyear_3.download.log
            """
        ),
    )

    sync_ls8_gm_cyear = SSHOperator(
        task_id="sync_ls8c_nbart_gm_cyear",
        remote_host="gadi-dm.nci.org.au",
        command=dedent(
            COMMON
            + """
            cd /g/data/jw04/ga/ga_ls8c_nbart_gm_cyear_3
            time ~/bin/s5cmd --stat cp --if-size-differ 's3://dea-public-data/derivative/ga_ls8c_nbart_gm_cyear_3/*' . >> /g/data/v10/work/c3_download_derivs/{{ts_nodash}}/ga_ls8c_nbart_gm_cyear_3.download.log
            """
        ),
    )

    index_wofs = SSHOperator(
        task_id="index_wofs",
        command=dedent(
            COMMON
            + """
            module load dea
            cd /g/data/v10/work/c3_download_derivs/{{ts_nodash}}

            awk '/odc-metadata.yaml/ {print "/g/data/jw04/ga/ga_ls_wo_3/" $3}' ga_ls_wo_3.download.log  | \
            xargs -P 4 datacube -v dataset add --no-verify-lineage --product ga_ls_wo_3
        """
        ),
        # Attempt to index downloaded datasets, even if there were some failures in the download
        # We want to avoid missing indexing anything, and any gaps will get filled in next time
        # the download runs.
        trigger_rule="all_done",
    )

    index_wofs_fq_apr_oct = SSHOperator(
        task_id="index_wofs_fq_apr_oct",
        command=dedent(
            COMMON
            + """
            module load dea
            cd /g/data/v10/work/c3_download_derivs/{{ts_nodash}}

            awk '/odc-metadata.yaml/ {print "/g/data/jw04/ga/ga_ls_wo_fq_apr_oct_3/" $3}' ga_ls_wo_fq_apr_oct_3.download.log  | \
            xargs -P 4 datacube -v dataset add --no-verify-lineage --product ga_ls_wo_fq_apr_oct_3
            """
        ),
        trigger_rule="all_done",
    )

    index_wofs_fq_nov_mar = SSHOperator(
        task_id="index_wofs_fq_nov_mar",
        command=dedent(
            COMMON
            + """
            module load dea
            cd /g/data/v10/work/c3_download_derivs/{{ts_nodash}}

            awk '/odc-metadata.yaml/ {print "/g/data/jw04/ga/ga_ls_wo_fq_nov_mar_3/" $3}' ga_ls_wo_fq_nov_mar_3.download.log  | \
            xargs -P 4 datacube -v dataset add --no-verify-lineage --product ga_ls_wo_fq_nov_mar_3
            """
        ),
        trigger_rule="all_done",
    )

    index_wofs_fq_cyear = SSHOperator(
        task_id="index_wofs_fq_cyear",
        command=dedent(
            COMMON
            + """
            module load dea
            cd /g/data/v10/work/c3_download_derivs/{{ts_nodash}}

            awk '/odc-metadata.yaml/ {print "/g/data/jw04/ga/ga_ls_wo_fq_cyear_3/" $3}' ga_ls_wo_fq_cyear_3.download.log  | \
            xargs -P 4 datacube -v dataset add --no-verify-lineage --product ga_ls_wo_fq_cyear_3
            """
        ),
        trigger_rule="all_done",
    )

    index_wofs_fq_myear = SSHOperator(
        task_id="index_wofs_fq_myear",
        command=dedent(
            COMMON
            + """
            module load dea
            cd /g/data/v10/work/c3_download_derivs/{{ts_nodash}}

            awk '/odc-metadata.yaml/ {print "/g/data/jw04/ga/ga_ls_wo_fq_myear_3/" $3}' ga_ls_wo_fq_myear_3.download.log  | \
            xargs -P 4 datacube -v dataset add --no-verify-lineage --product ga_ls_wo_fq_myear_3
            """
        ),
        trigger_rule="all_done",
    )

    index_ls5_gm_cyear = SSHOperator(
        task_id="index_ls5_gm_cyear",
        command=dedent(
            COMMON
            + """
            module load dea
            cd /g/data/v10/work/c3_download_derivs/{{ts_nodash}}

            awk '/odc-metadata.yaml/ {print "/g/data/jw04/ga/sync_ls5_gm_cyear/" $3}' sync_ls5_gm_cyear.download.log  | \
            xargs -P 4 datacube -v dataset add --no-verify-lineage --product sync_ls5_gm_cyear
            """
        ),
        trigger_rule="all_done",
    )

    index_ls7_gm_cyear = SSHOperator(
        task_id="index_ls7_gm_cyear",
        command=dedent(
            COMMON
            + """
            module load dea
            cd /g/data/v10/work/c3_download_derivs/{{ts_nodash}}

            awk '/odc-metadata.yaml/ {print "/g/data/jw04/ga/sync_ls7_gm_cyear/" $3}' sync_ls7_gm_cyear.download.log  | \
            xargs -P 4 datacube -v dataset add --no-verify-lineage --product sync_ls7_gm_cyear
            """
        ),
        trigger_rule="all_done",
    )

    index_ls8_gm_cyear = SSHOperator(
        task_id="index_ls8_gm_cyear",
        command=dedent(
            COMMON
            + """
            module load dea
            cd /g/data/v10/work/c3_download_derivs/{{ts_nodash}}

            awk '/odc-metadata.yaml/ {print "/g/data/jw04/ga/sync_ls8_gm_cyear/" $3}' sync_ls8_gm_cyear.download.log  | \
            xargs -P 4 datacube -v dataset add --no-verify-lineage --product sync_ls8_gm_cyear
            """
        ),
        trigger_rule="all_done",
    )

    index_fc = SSHOperator(
        task_id="index_fc",
        command=dedent(
            COMMON
            + """
            module load dea
            cd /g/data/v10/work/c3_download_derivs/{{ts_nodash}}

            awk '/odc-metadata.yaml/ {print "/g/data/jw04/ga/ga_ls_fc_3/" $3}' ga_ls_fc_3.download.log  | \
            xargs -P 4 datacube -v dataset add --no-verify-lineage --product ga_ls_fc_3
            """
        ),
        trigger_rule="all_done",
    )

    setup >> [sync_fc,
              sync_wofs, sync_wofs_fq_apr_oct, sync_wofs_fq_nov_mar, sync_wofs_fq_cyear, sync_wofs_fq_myear,
              sync_ls5_gm_cyear, sync_ls7_gm_cyear, sync_ls8_gm_cyear]

    sync_wofs >> index_wofs
    sync_wofs_fq_apr_oct >> index_wofs_fq_apr_oct
    sync_wofs_fq_nov_mar >> index_wofs_fq_nov_mar
    sync_wofs_fq_cyear >> index_wofs_fq_cyear
    sync_wofs_fq_myear >> index_wofs_fq_myear

    sync_fc >> index_fc

    sync_ls5_gm_cyear >> index_ls5_gm_cyear
    sync_ls7_gm_cyear >> index_ls5_gm_cyear
    sync_ls8_gm_cyear >> index_ls5_gm_cyear
