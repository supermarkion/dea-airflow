"""
Utilities for reporting db queries and inserts
"""

import logging
import re

from psycopg2.errors import UniqueViolation
from airflow.providers.postgres.hooks.postgres import PostgresHook
from automated_reporting.databases import sql
from datetime import datetime as dt, timezone, timedelta

log = logging.getLogger("airflow.task")


def insert_completeness(connection_id, db_completeness_writes):
    """Insert completeness results into reporting DB"""

    rep_pg_hook = PostgresHook(postgres_conn_id=connection_id)
    rep_conn = None
    try:
        # open the connection to the Reporting DB and get a cursor
        with rep_pg_hook.get_conn() as rep_conn:
            with rep_conn.cursor() as rep_cursor:
                for record in db_completeness_writes:
                    missing_scenes = record.pop()
                    rep_cursor.execute(sql.INSERT_COMPLETENESS, tuple(record))
                    log.debug(
                        "Reporting Executed SQL: {}".format(rep_cursor.query.decode())
                    )
                    last_id = rep_cursor.fetchone()[0]
                    for missing_scene in missing_scenes:
                        missing_scene.insert(0, last_id)
                        rep_cursor.execute(
                            sql.INSERT_COMPLETENESS_MISSING, tuple(missing_scene)
                        )
                        log.debug(
                            "Reporting Executed SQL: {}".format(
                                rep_cursor.query.decode()
                            )
                        )
    except UniqueViolation as e:
        log.error("Duplicate item in database")
    except Exception as e:
        raise e
    finally:
        if rep_conn is not None:
            rep_conn.close()


def insert_latency(
    connection_id, product_name, latest_sat_acq_ts, latest_processing_ts, execution_date
):
    """Insert latency result into reporting DB"""

    rep_pg_hook = PostgresHook(postgres_conn_id=connection_id)
    rep_conn = None
    try:
        # open the connection to the Reporting DB and get a cursor
        with rep_pg_hook.get_conn() as rep_conn:
            with rep_conn.cursor() as rep_cursor:
                rep_cursor.execute(
                    sql.INSERT_LATENCY,
                    (
                        product_name,
                        latest_sat_acq_ts.astimezone(tz=timezone.utc).replace(
                            tzinfo=None
                        ),
                        latest_processing_ts.astimezone(tz=timezone.utc).replace(
                            tzinfo=None
                        ),
                        execution_date.astimezone(
                            tz=timezone(timedelta(hours=10), name="AEST")
                        ).replace(tzinfo=None),
                    ),
                )
                log.info("REP Executed SQL: {}".format(rep_cursor.query.decode()))
                log.info("REP returned: {}".format(rep_cursor.statusmessage))
    except UniqueViolation as e:
        log.error("Duplicate item in database")
    except Exception as e:
        raise e
    finally:
        if rep_conn is not None:
            rep_conn.close()


def expire_completeness(connection_id, product_id):
    """Expire completeness results in reporting DB"""

    rep_pg_hook = PostgresHook(postgres_conn_id=connection_id)
    rep_conn = None
    count = None
    try:
        # open the connection to the Reporting DB and get a cursor
        with rep_pg_hook.get_conn() as rep_conn:
            with rep_conn.cursor() as rep_cursor:
                rep_cursor.execute(sql.EXPIRE_COMPLETENESS, {"product_id": product_id})
                count = rep_cursor.rowcount
    except Exception as e:
        raise e
    finally:
        if rep_conn is not None:
            rep_conn.close()
    return count


def insert_latency_list(connection_id, latency_results, execution_date):
    """Insert latency result into reporting DB"""

    rep_pg_hook = PostgresHook(postgres_conn_id=connection_id)
    rep_conn = None
    try:
        # open the connection to the Reporting DB and get a cursor
        with rep_pg_hook.get_conn() as rep_conn:
            with rep_conn.cursor() as rep_cursor:
                for latency in latency_results:
                    sat_acq_ts = dt.utcfromtimestamp(latency["latest_sat_acq_ts"])
                    proc_ts = None
                    if latency["latest_processing_ts"]:
                        proc_ts = dt.utcfromtimestamp(latency["latest_processing_ts"])
                    rep_cursor.execute(
                        sql.INSERT_LATENCY,
                        (
                            latency["product_name"],
                            sat_acq_ts,
                            proc_ts,
                            execution_date.astimezone(
                                tz=timezone(timedelta(hours=10), name="AEST")
                            ).replace(tzinfo=None),
                        ),
                    )
                    log.info("REP Executed SQL: {}".format(rep_cursor.query.decode()))
                    log.info("REP returned: {}".format(rep_cursor.statusmessage))
    except Exception as e:
        raise e
    finally:
        if rep_conn is not None:
            rep_conn.close()
