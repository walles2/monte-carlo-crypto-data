from typing import List, NamedTuple, Callable
import io
import time
from datetime import datetime

import boto3
import pandas

from src.common import PriceRecord

athena_client = boto3.client('athena')
s3_client = boto3.client('s3')

# S3 Constants
S3_BUCKET = "scott-waller-bucket"
S3_PRICE_DATA_FOLDER = "price_data"

# Athena Constants
DATABASE = "scott_waller_database"
TABLE = "price_data"
WORKGROUP = "primary"

# Athena Query States
SUCCEEDED = "SUCCEEDED"
FAILED = "FAILED"
CANCELLED = "CANCELLED"
FINISHED_STATES = frozenset([SUCCEEDED, FAILED, CANCELLED])
UNSUCCESSFUL_STATES = frozenset([FAILED, CANCELLED])

# SQL queries
WITHIN_LAST_DAY_EXPRESSION = """timestamp > (current_timestamp - interval '24' hour)"""

GET_METRIC_NAMES_QUERY = f"""
SELECT DISTINCT(METRIC) FROM {TABLE}
"""

GET_METRIC_TIMESERIES_DATA_QUERY = f"""
SELECT timestamp,value,metric FROM {TABLE} 
WHERE metric = '{{metric_name}}' and {WITHIN_LAST_DAY_EXPRESSION}
"""

GET_METRIC_RANK_QUERY = f"""
SELECT STDDEV(value)/(
    SELECT MAX(value_stddev) AS max_stddev FROM (
        SELECT STDDEV(value) AS value_stddev, metric FROM {TABLE} 
        WHERE {WITHIN_LAST_DAY_EXPRESSION}
        GROUP BY metric
    ) 
) AS metric_rank FROM {TABLE} 
 WHERE metric = '{{metric_name}}' and {WITHIN_LAST_DAY_EXPRESSION}
"""

# Execution Constants
SQL_TIMEOUT = 30
SLEEP_TIME = 0.1
RESULT_PATH = "s3://scott-waller-bucket/athena_query_results/"


ATHENA_TYPE_TO_PYTHON_TYPE = {
    "varchar": lambda x: x,
    "double": lambda x: float(x),
    "timestamp": lambda x: datetime.fromisoformat(x)
}


class Column(NamedTuple):
    name: str
    type: str
    formatter: Callable

class AthenaQueryUnsuccessful(Exception):
    pass

class AthenaQueryTimeout(Exception):
    pass

def _check_athena_query(query_id, timeout=SQL_TIMEOUT):
    state = "UNDEFINED"
    start_time = time.time()
    while state not in FINISHED_STATES:
        if (time.time() - start_time) > timeout:
            raise AthenaQueryTimeout()

        check_response = athena_client.get_query_execution(
            QueryExecutionId=query_id
        )
        state = check_response["QueryExecution"]["Status"]["State"]
        time.sleep(SLEEP_TIME)

    if state in UNSUCCESSFUL_STATES:
        raise AthenaQueryUnsuccessful()


def _run_athena_query(sql):
    # start the query
    start_response = athena_client.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={
            'Database': DATABASE
        },
        ResultConfiguration={
            'OutputLocation': RESULT_PATH
        },
        WorkGroup=WORKGROUP
    )
    query_id = start_response['QueryExecutionId']

    _check_athena_query(query_id)

    # return results
    result_response = athena_client.get_query_results(
        QueryExecutionId=query_id
    )
    result_set = result_response['ResultSet']
    columns = [Column(column['Name'], column['Type'], ATHENA_TYPE_TO_PYTHON_TYPE[column['Type']]) 
               for column in result_set['ResultSetMetadata']['ColumnInfo']]
    import ipdb; ipdb.set_trace()
    data = result_set["Rows"][1:] # The first row is a "header" row
    rows = [{column.name: column.formatter(value_dict['VarCharValue']) for column, value_dict in zip(columns, row['Data'])} for row in data]
    return rows


def insert_price_records(records: List[PriceRecord], timestamp):
    df = pandas.DataFrame(records)
    s3_filename = f"s3://{S3_BUCKET}/{S3_PRICE_DATA_FOLDER}/{str(timestamp)}.pq"
    df.to_parquet(s3_filename, compression='gzip')


def get_all_metric_names():
    return _run_athena_query(GET_METRIC_NAMES_QUERY)


def get_metric_timeseries_data(metric_name):
    query = GET_METRIC_TIMESERIES_DATA_QUERY.format(metric_name=metric_name)
    return _run_athena_query(query)


def get_metric_rank(metric_name):
    query = GET_METRIC_RANK_QUERY.format(metric_name=metric_name)
    return _run_athena_query(query)
