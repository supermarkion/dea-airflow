"""
# IMAGES USED FOR DAGs
"""
## STABLE IMAGES
INDEXER_IMAGE = "538673716275.dkr.ecr.ap-southeast-2.amazonaws.com/opendatacube/datacube-index:latest"

OWS_IMAGE = "538673716275.dkr.ecr.ap-southeast-2.amazonaws.com/opendatacube/ows:1.8.13"
OWS_CONFIG_IMAGE = "geoscienceaustralia/dea-datakube-config:latest"  # do not pull from ECR, to avoid delay in ecr sync

EXPLORER_IMAGE = (
    "538673716275.dkr.ecr.ap-southeast-2.amazonaws.com/opendatacube/explorer:2.5.1"
)

S3_TO_RDS_IMAGE = "538673716275.dkr.ecr.ap-southeast-2.amazonaws.com/geoscienceaustralia/s3-to-rds:0.1.4"

WAGL_IMAGE = (
    "538673716275.dkr.ecr.ap-southeast-2.amazonaws.com/dev/wagl:release-20210526a"
)

STAT_IMAGE = "538673716275.dkr.ecr.ap-southeast-2.amazonaws.com/opendatacube/datacube-statistician:0.3.31"

WAGL_IMAGE_POC = "geoscienceaustralia/dea-wagl-docker:latest"

# UNSTABLE IMAGES
EXPLORER_UNSTABLE_IMAGE = "opendatacube/explorer:2.5.0-3-gd9f5a67"

WATERBODIES_UNSTABLE_IMAGE = "geoscienceaustralia/dea-waterbodies:1.1.5-2-g381258f"
