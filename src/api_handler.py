from src import database_layer

def _get_metric_name_from_event(event):
	return event['metric_name']


def get_all_metric_names(event, context):
	return database_layer.get_all_metric_names()


def get_metric_data(event, context):
	metric_name = _get_metric_name_from_event(event)
	return database_layer.get_metric_timeseries_data(metric_name)

def get_metric_rank(event, context):
	metric_name = _get_metric_name_from_event(event)
	return database_layer.get_metric_rank(metric_name)
