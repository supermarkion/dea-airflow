"""
Task for s2 completeness calculations
"""
import logging

from automated_reporting.utilities import helpers
from automated_reporting.utilities import copernicus_api
from automated_reporting.databases import odc_db, reporting_db

log = logging.getLogger("airflow.task")


def filter_products_to_region(products, region_id):
    """Filter odc products to the relavent region"""
    return list(filter(lambda x: x["region_id"] == region_id, products))


def get_expected_ids_missing_in_actual(r_expected_products, r_actual_products):
    """return list of granule_ids in expected, that are missing in actual, for region"""
    return list(
        set([x["granule_id"] for x in r_expected_products])
        - set([y["parent_id"] for y in r_actual_products])
    )


def get_products_in_expected_and_actual(r_expected_products, r_actual_products):
    """return a list of products that are in both expected and actual lists, for region"""
    actual_ids = list(
        set([x["granule_id"] for x in r_expected_products])
        & set([y["parent_id"] for y in r_actual_products])
    )
    return list(filter(lambda x: x["parent_id"] in actual_ids, r_actual_products))


def calculate_metric_for_region(r_expected_products, r_actual_products):
    """calculate completeness and latency for a single region"""

    # make a list of granule_ids in the expected list, not in not in actual list, for this region
    missing_ids = get_expected_ids_missing_in_actual(
        r_expected_products, r_actual_products
    )

    # filter the actual products list for region to those in expected products for region
    actual_products = get_products_in_expected_and_actual(
        r_expected_products, r_actual_products
    )

    # get latest sat_acq_time and latest_processing_time from odc list for this tile
    latest_sat_acq_time = None
    latest_processing_time = None

    if actual_products:
        latest_sat_acq_time = max(actual_products, key=lambda x: x["center_dt"])[
            "center_dt"
        ]
        latest_processing_time = max(actual_products, key=lambda x: x["processing_dt"])[
            "processing_dt"
        ]

    # calculate expected, actual, missing and completeness
    expected = len(r_expected_products)
    missing = len(missing_ids)
    actual = expected - missing
    # if there are no tiles expected show completeness as None/null
    if expected > 0:
        completeness = (float(actual) / float(expected)) * 100
    else:
        completeness = None

    # add a dictionary representing this tile to the main output list
    r_output = {
        "completeness": completeness,
        "expected": expected,
        "missing": missing,
        "actual": actual,
        "latest_sat_acq_ts": latest_sat_acq_time,
        "latest_processing_ts": latest_processing_time,
        "missing_ids": missing_ids,
    }
    return r_output


def filter_expected_to_sensor(expected_products, sensor):
    """filter expected products on 'sensor' key"""
    return [p for p in expected_products if p["sensor"] == sensor]


def calculate_metrics_for_all_regions(aoi_list, expected_products, actual_products):
    """calculate completeness and latency for every region in AOI"""

    output = list()

    # loop through each tile and compute completeness and latency
    for region in aoi_list:

        # create lists of products for expected and actual, filtered to this tile
        r_expected_products = filter_products_to_region(expected_products, region)
        r_actual_products = filter_products_to_region(actual_products, region)

        # calculate completness and latency for this region
        t_output = calculate_metric_for_region(r_expected_products, r_actual_products)

        # add the metrics result to output_list
        t_output["region_id"] = region
        output.append(t_output)

    return output


def calculate_summary_stats_for_aoi(output):
    """calculate summary stats for whole of AOI based on output from each region"""

    summary = dict()
    # get completeness for whole of aoi
    summary["expected"] = sum([x["expected"] for x in output])
    summary["missing"] = sum([x["missing"] for x in output])
    summary["actual"] = sum([x["actual"] for x in output])
    if summary["expected"] > 0:
        summary["completeness"] = completeness = (
            float(summary["actual"]) / float(summary["expected"])
        ) * 100
    else:
        summary["completeness"] = None

    # get latency for whole of AOI
    summary["latest_sat_acq_ts"] = None
    sat_acq_time_list = list(filter(lambda x: x["latest_sat_acq_ts"] != None, output))
    if sat_acq_time_list:
        summary["latest_sat_acq_ts"] = max(
            sat_acq_time_list,
            key=lambda x: x["latest_sat_acq_ts"],
        )["latest_sat_acq_ts"]

    # get latency for whole of AOI
    summary["latest_processing_ts"] = None
    processing_time_list = list(
        filter(lambda x: x["latest_processing_ts"] != None, output)
    )
    if processing_time_list:
        summary["latest_processing_ts"] = max(
            processing_time_list,
            key=lambda x: x["latest_processing_ts"],
        )["latest_processing_ts"]

    return summary


def log_results(sensor, summary, output):
    """log a results list to Airflow logs"""

    # log summary completeness and latency
    log.info("{} Completeness complete".format(sensor))
    log.info("{} Total expected: {}".format(sensor, summary["expected"]))
    log.info("{} Total missing: {}".format(sensor, summary["missing"]))
    log.info("{} Total actual: {}".format(sensor, summary["actual"]))
    log.info("{} Total completeness: {}".format(sensor, summary["completeness"]))
    log.info("{} Latest Sat Acq Time: {}".format(sensor, summary["latest_sat_acq_ts"]))
    log.info(
        "{} Latest Processing Time: {}".format(sensor, summary["latest_processing_ts"])
    )
    # log region level completeness and latency
    for record in output:
        log.debug(
            "{} - {} - {}:{}:{}".format(
                sensor,
                record["region_id"],
                record["expected"],
                record["actual"],
                record["missing"],
            )
        )
        # log missing granule ids for each tile
        for scene_id in record["missing_ids"]:
            log.debug("    Missing:{}".format(scene_id))


def generate_db_writes(product_id, summary, output, execution_date):
    """Generate a list of db writes from a results list"""

    execution_date = helpers.python_dt(execution_date)

    db_completeness_writes = []
    # append summary stats to output list
    db_completeness_writes.append(
        [
            "all_s2",
            summary["completeness"],
            summary["expected"],
            summary["actual"],
            product_id,
            summary["latest_sat_acq_ts"],
            summary["latest_processing_ts"],
            execution_date,
            [],
        ]
    )
    # append detailed stats for eacgh region to list
    for record in output:
        completeness_record = [
            record["region_id"],
            record["completeness"],
            record["expected"],
            record["actual"],
            product_id,
            record["latest_sat_acq_ts"],
            record["latest_processing_ts"],
            execution_date,
            [],
        ]
        # add a list of missing scene ids to each region_code
        for scene_id in record["missing_ids"]:
            completeness_record[-1].append([scene_id, execution_date])
        db_completeness_writes.append(completeness_record)
    return db_completeness_writes


def streamline_with_copericus_format(product_list):
    """
    Modify the data returned from odc to match that returned from Copernicus to make
    calculations reuseable for different levels.
    """
    copernicus_format = list()
    for product in product_list:
        row = {
            "uuid": product["uuid"],
            "granule_id": product["granule_id"],
            "region_id": product["region_id"],
            "sensor": product["granule_id"][:3].lower(),
        }
        copernicus_format.append(row)
    return copernicus_format


def swap_in_parent(product_list):
    """
    Swap parent_id into granule_id to allow reusing completeness calculation.
    """
    for product in product_list:
        product["granule_id"] = product["parent_id"]
    return product_list


# Task callable for derivatives
def task_derivative(
    upstream, target, execution_date, days, rep_conn, odc_conn, aux_data_path, **kwargs
):
    """
    Task to compute Sentinel2 derivative completeness
    """
    expected_products_odc = list()
    for product_code in upstream:
        # query ODC for for all upstream products for last X days
        expected_products_odc += odc_db.query(
            odc_conn, product_code, execution_date, days
        )

    # streamline the ODC results back to match the Copernicus query
    expected_products = streamline_with_copericus_format(expected_products_odc)

    # get a optimised tile list of AOI
    aoi_list = helpers.get_aoi_list(aux_data_path, "sentinel2_aoi_list.txt")
    log.info("Loaded AOI tile list: {} tiles found".format(len(aoi_list)))

    # a list of tuples to store values before writing to database
    db_completeness_writes = []

    log.info("Computing completeness for: {}".format(target))

    # query ODC for all S2 L1 products for last X days
    actual_products = odc_db.query(odc_conn, target, execution_date, days)

    # swap granule_id and parent_id
    # actual_products = swap_in_parent(actual_products)

    # compute completeness and latency for every tile in AOI
    output = calculate_metrics_for_all_regions(
        aoi_list, expected_products, actual_products
    )

    # calculate summary stats for whole of AOI
    summary = calculate_summary_stats_for_aoi(output)
    summary_out = {target: summary}

    # write results to Airflow logs
    log_results(target, summary, output)

    # generate the list of database writes for sensor/platform
    db_completeness_writes += generate_db_writes(
        target, summary, output, execution_date
    )

    # write records to reporting database
    reporting_db.insert_completeness(rep_conn, db_completeness_writes)
    log.info(
        "Inserting completeness output to reporting DB: {} records".format(
            len(db_completeness_writes)
        )
    )

    return summary_out


# Task callable for ard
def task_ard(
    s2a,
    s2b,
    execution_date,
    days,
    rep_conn,
    odc_conn,
    aux_data_path,
    copernicus_api_credentials,
    **kwargs
):
    """
    Task to compute Sentinel2 ARD completeness
    """

    # query Copernicus API for for all S2 L1 products for last X days
    expected_products = copernicus_api.query(
        execution_date, days, copernicus_api_credentials
    )

    # get a optimised tile list of AOI
    aoi_list = helpers.get_aoi_list(aux_data_path, "sentinel2_aoi_list.txt")
    log.info("Loaded AOI tile list: {} tiles found".format(len(aoi_list)))

    # a list of tuples to store values before writing to database
    db_completeness_writes = []

    summary_out = dict()

    # calculate metrics for each s2 sensor/platform and add to output list
    for sensor in [s2a, s2b]:

        log.info("Computing completeness for: {}".format(sensor["odc_code"]))

        # query ODC for all S2 L1 products for last X days
        actual_products = odc_db.query(
            odc_conn, sensor["odc_code"], execution_date, days
        )

        # filter expected products on sensor (just for completeness between lo and l1)
        filtered_expected_products = filter_expected_to_sensor(
            expected_products, sensor["id"]
        )

        # compute completeness and latency for every tile in AOI
        output = calculate_metrics_for_all_regions(
            aoi_list, filtered_expected_products, actual_products
        )

        # calculate summary stats for whole of AOI
        summary = calculate_summary_stats_for_aoi(output)
        summary_out[sensor["id"]] = summary

        # write results to Airflow logs
        log_results(sensor["odc_code"], summary, output)

        # generate the list of database writes for sensor/platform
        db_completeness_writes += generate_db_writes(
            sensor["rep_code"], summary, output, execution_date
        )

    # write records to reporting database
    reporting_db.insert_completeness(rep_conn, db_completeness_writes)
    log.info(
        "Inserting completeness output to reporting DB: {} records".format(
            len(db_completeness_writes)
        )
    )

    return summary_out
