import requests
from typing import List

_URL_PREFIX = 'https://api.covid19tracking.narrativa.com/api'
_COUNTRIES_URL = _URL_PREFIX + '/countries'


class Country:
    def __init__(self, json_config):
        self._json_config = json_config
        print(json_config)

    @property
    def id(self) -> str:
        return self._json_config['id']

    @property
    def name(self) -> str:
        return self._json_config['name']

    def __str__(self) -> str:
        return self.id


def get_countries() -> List[Country]:
    response = requests.get(_COUNTRIES_URL).json()
    countries = [Country(c) for c in response['countries']]
    return countries


if __name__ == '__main__':
    for country in get_countries():
        print(country)