import json

from src import database_layer

def _get_metric_name_from_event(event):
    return event['pathParameters']['metric-name']


def get_all_metric_names(event, context):
    names = database_layer.get_all_metric_names()
    return {
        'statusCode': 200,
        'body': json.dumps(names)
    }


def get_metric_data(event, context):
    metric_name = _get_metric_name_from_event(event)
    timeseries = database_layer.get_metric_timeseries_data(metric_name)
    return {
        'statusCode': 200,
        'body': json.dumps(timeseries)
    }

def get_metric_rank(event, context):
    metric_name = _get_metric_name_from_event(event)
    rank = database_layer.get_metric_rank(metric_name)
    return {
        'statusCode': 200,
        'body': json.dumps(rank)
    }
