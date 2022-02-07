from typing import List
import io

import boto3
import pandas

from src.common import PriceRecord

athena_client = boto3.client('athena')
s3_client = boto3.client('s3')


S3_BUCKET = "scott-waller-bucket"
S3_PRICE_DATA_FOLDER = "price_data"

DATABASE = "scott_waller_database"
TABLE = "Price_Data"

GET_METRIC_NAMES_QUERY = f"""
SELECT DISTINCT(METRIC) FROM {TABLE}
"""

WITHIN_LAST_DAY_EXPRESSION = """timestamp > (current_date - interval '1' day)"""

GET_METRIC_TIMESERIES_DATA_QUERY = f"""
SELECT timestamp,value,metric FROM {TABLE} WHERE metric = {{metric_name}} and {WITHIN_LAST_DAY_EXPRESSION}
"""

GET_METRIC_RANK_QUERY = f"""
SELECT STDDEV(value where metric = {{metric_name}} and {WITHIN_LAST_DAY_EXPRESSION})/MAX() as rank, metric from {TABLE}
"""


def _run_athena_query(sql):
	# some stuff

def insert_price_records(records: List[PriceRecord], timestamp):
	df = pandas.DataFrame(records)
	s3_filename = f"s3://{S3_BUCKET}/{S3_PRICE_DATA_FOLDER}/{str(timestamp)}.pq"
	df.to_parquet(s3_filename, compression='gzip')


def get_all_metric_names():
	return _run_athena_query(GET_METRIC_NAMES_QUERY)


def get_metric_timeseries_data(metric_name):
	query = GET_METRIC_TIMESERIES_DATA_QUERY.format(metric_name)
	return _run_athena_query(query)

def get_metric_rank(metric_name):
	query = GET_METRIC_RANK_QUERY.format(metric_name)
	return _run_athena_query(query)
