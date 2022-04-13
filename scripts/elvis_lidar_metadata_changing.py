# This script aims to
# 1. get a S3 prefix URI which under s3://elvis-stac, return relative S3 objects URIs
# 2. use these S3 object URIs to load relative STAC metadata files (JSON format)
# 3. run transform script to these metadata files
# 4. dump the new metadata files to s3://dea-public-data-dev/projects/elvis-lidar (keep original hierarchy)
# Note: the dea-public-data-dev writer credentials will be passed by K8s secret


import json
import boto3
from urllib.parse import urlparse
import logging
import os

# these collection items will map to S3 URI
# s3://elvis-stac/{product_name}/{collection_name}/collection.json
PRODUCT_LIST = ["dem_1m", "dem_2m", "dem_5m"]

COLLECTION_LIST = ["Bellata201106", "Paika201303", "Para201410",
                   "BaanBaa201401", "Boomi201501", "Geera201705"]

ORIGINAL_BUKCET_NAME = "elvis-stac"
NWE_BUCKET_NAME = "dea-public-data-dev"
NEW_PREFIX = "projects/elvis-lidar/"


def modify_json_content(old_metadata_content: dict) -> dict:
    # assume all JSON files follow the same schema to save development time
    collection = old_metadata_content['collection']
    old_metadata_content['properties']['odc:collection'] = collection
    return old_metadata_content


def get_metadata_path(product_name, collection_name):
    collection_key = f"{product_name}/{collection_name}/collection.json"
    logging.warning(f"Try to access s3://{ORIGINAL_BUKCET_NAME}/{collection_key}")
    # the read access will come from K8s service account
    s3_conn = boto3.client('s3')
    try:
        collection_content = s3_conn.get_object(Bucket=ORIGINAL_BUKCET_NAME, Key=collection_key)
        return [e['href'] for e in json.loads(collection_content["Body"].read())['links'] if e['rel'] == 'item']
    except:
        return []


def main():

    # the following values would be passed by Airflow, but consider it is a temp solution, let us
    # leave the hard-code values here to pass the test
    for product_name in PRODUCT_LIST:

        for collection_name in COLLECTION_LIST:

            original_file_list = get_metadata_path(product_name, collection_name)

            for original_file in original_file_list:

                original_file_key = urlparse(original_file).path[1:]

                # connect to s3 by elvis-stac creds
                # the read access will come from K8s service account
                s3_conn = boto3.client('s3')

                content_object = s3_conn.get_object(Bucket=ORIGINAL_BUKCET_NAME, Key=original_file_key)
                old_metadata_content = json.loads(content_object["Body"].read())
                try:
                    new_json_content = modify_json_content(old_metadata_content)

                    # turn on the sign-in cause we will upload to a private bucket
                    s3_conn = boto3.client('s3', aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID_WRITE'], aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY_WRITE'])
                    s3_conn.put_object(
                        Body=json.dumps(new_json_content),
                        Bucket=NWE_BUCKET_NAME,
                        Key=NEW_PREFIX + original_file_key
                    )

                except KeyError:
                    logging.warning(f"{original_file_key} cannot parse its product name")
                except:
                    logging.warning(f"{original_file_key} cannot modify its content and dump to temp S3 bucket")


if __name__ == "__main__":
    main()