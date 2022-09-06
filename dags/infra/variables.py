"""
# Environment shared variables read from airflow variable config, provided by infrastracture
# https://airflow.apache.org/docs/stable/concepts.html?highlight=variable#storing-variables-in-environment-variables
# Variables set using Environment Variables would not appear in the Airflow UI but you will be able to use it in your DAG file
Audit check:
    date: 21/04/2021
"""
from airflow.models import Variable

# DB Users / Roles
SECRET_EXPLORER_WRITER_NAME = Variable.get(
    "db_explorer_writer_secret", default_var="explorer-writer"
)  # qa
SECRET_OWS_WRITER_NAME = Variable.get(
    "db_ows_writer_secret", default_var="ows-writer"
)  # qa
SECRET_ODC_WRITER_NAME = Variable.get(
    "db_odc_writer_secret", default_var="odc-writer"
)  # qa
SECRET_ODC_READER_NAME = Variable.get(
    "db_odc_reader_secret", default_var="odc-reader"
)  # qa
SECRET_DBA_ADMIN_NAME = Variable.get(
    "db_dba_admin_secret", default_var="dba_admin"
)  # qa

SECRET_ODC_ADMIN_NAME = Variable.get("db_odc_admin_secret", default_var="odc-admin")

SECRET_EXPLORER_ADMIN_NAME = Variable.get(
    "db_explorer_admin_secret", default_var="explorer-admin"
)

SECRET_OWS_ADMIN_NAME = Variable.get("db_ows_admin_secret", default_var="ows-admin")

SECRET_EXPLORER_NCI_ADMIN_NAME = Variable.get(
    "db_explorer_nci_admin_secret", default_var="explorer-nci-admin"
)  # qa
SECRET_EXPLORER_NCI_WRITER_NAME = Variable.get(
    "db_explorer_nci_writer_secret", default_var="explorer-nci-writer"
)  # qa

# DB config
DB_DATABASE = Variable.get("db_database", default_var="odc")  # qa
DB_HOSTNAME = Variable.get("db_hostname", default_var="db-writer")  # qa
DB_READER_HOSTNAME = Variable.get("db_reader_hostname", default_var="db-reader")
DB_PORT = Variable.get("db_port", default_var="5432")  # qa

AWS_DEFAULT_REGION = Variable.get("region", default_var="ap-southeast-2")  # qa


# c3 alchemist deriveritves
ALCHEMIST_C3_USER_SECRET = Variable.get(
    "alchemist_c3_user_secret", default_var="alchemist-c3-user-creds"
)

ALCHEMIST_S2_C3_WO_NRT_USER_SECRET = Variable.get(
    "alchemist_s2_c3_wo_nrt_user_secret",
    default_var="alchemist-s2-c3-nrt-wo-user-creds",
)

LANDSAT_C3_AWS_USER_SECRET = Variable.get(
    "landsat_c3_aws_user_secret", default_var="processing-landsat-3-aws-creds"
)

SENTINEL_2_ARD_INDEXING_AWS_USER_SECRET = Variable.get(
    "sentinel_2_ard_indexing_aws_user_secret",
    default_var="sentinel-2-ard-indexing-creds",
)

S2_NRT_AWS_CREDS = "wagl-nrt-aws-creds"
ARD_NRT_LS_CREDS = "ard-nrt-ls-aws-creds"


# stats
PROCESSING_STATS_USER_SECRET = Variable.get(
    "processing_stats_user_secret", default_var="processing-aws-creds-stats"
)

C3_BA_ALCHEMIST_SECRET = Variable.get(
    "s2_c3_ba_indexing_secret", "s2-c3-ba-derivative-user-creds"
)

# STATSD
STATSD_HOST = Variable.get("statsd_host", default_var="localhost")
STATSD_PORT = Variable.get("statsd_port", default_var="8125")
