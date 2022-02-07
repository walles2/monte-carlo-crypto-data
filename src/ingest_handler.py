from typing import NamedTuple
from datetime import datetime

import requests

from src import database_layer
from src.common import PriceRecord

PRICES_ENDPOINT = "https://api.cryptowat.ch/markets/prices"
RESULT_KEY = "result"
SPLIT_TOKEN = ":"

###
# Example Response from the prices endpoint
#
# {'result': {'index:kraken-futures:cf-in-bchusd': 330.46,
#   'index:kraken-futures:cf-in-ltcusd': 127.21,
#   'index:kraken-futures:cf-in-xrpusd': 0.7482,
#   'index:kraken-futures:cme-cf-brti': 42794,
#   'index:kraken-futures:cme-cf-ethusd-rti': 3095.52,
#   ...}
#   'cursor': {'last': 'Jh6w3I06BYtr42oNCbOiTP_FWisrb4TBjaFwbMGLeR80kOlzJxJilltfF3BpqA',
#   'hasMore': False},
#  'allowance': {'cost': 0.015,
#   'remaining': 9.97,
#   'upgrade': 'For unlimited API access, create an account at https://cryptowat.ch'}
#  }
###

class FailedRequestException(Exception):
	pass


def parse_record(key: str, value: float, now: datetime):
	market_type, market_name, metric = key.split(SPLIT_TOKEN)
	return PriceRecord(
		market_type=market_type,
		market_name=market_name,
		metric=metric,
		value=value,
		timestamp=now
	)


def gather_crypto_data():
	now = datetime.utcnow()
	response = requests.get(PRICES_ENDPOINT)
	if response.status_code != 200:
		raise FailedRequestException()
	price_data = response.json()
	prices = [parse_record(key, value, now) for key, value in price_data[RESULT_KEY].items()]
	import ipdb; ipdb.set_trace()
	database_layer.insert_price_records(prices)
