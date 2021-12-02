import datetime as dt
import os
from datetime import timedelta

import pendulum


# Thanks https://github.com/apache/airflow/issues/17720


def days_ago(n, hour=0, minute=0, second=0, microsecond=0):
    """Choose a number of days ago based on midnight local time, instead of midnight UTC"""
    tz = pendulum.tz.timezone(
        os.environ.get("AIRFLOW__AIRFLOW__CORE__DEFAULT_TIMEZONE")
    )
    today = dt.datetime.now(tz=tz).replace(
        hour=hour, minute=minute, second=second, microsecond=microsecond
    )
    return today - timedelta(days=n)
