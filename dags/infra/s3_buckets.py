"""
#
# s3_buckets supplied by terraform or global
Audit check:
    date: 21/04/2021
"""
from airflow.models import Variable

# S3 buckets
DB_DUMP_S3_BUCKET = Variable.get("db_dump_s3_bucketname", "dea-dev-odc-db-dump") #qa
