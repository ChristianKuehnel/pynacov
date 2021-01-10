import requests
from datetime import date, timedelta
from typing import List, Dict, Optional
import json
import re

_URL_PREFIX = 'https://api.covid19tracking.narrativa.com/api'
_DATE_URL_SUFFIX = '?date_from={from_date}&date_to={to_date}'


class Data:

    _ATTRIBUTE_REGEX = re.compile('source|today.*|yesterday.*')

    def __init__(self, data_dict: dict):
        self.date = date.fromisoformat(data_dict['date'])
        self._attributes = {}
        for key, value in data_dict.items():
            if Data._ATTRIBUTE_REGEX.match(key):
                try:
                    self._attributes[key] = int(value)
                except (ValueError, TypeError):
                    try:
                        self._attributes[key] = float(value)
                    except (ValueError, TypeError):
                        self._attributes[key] = value

    @property
    def attributes(self) -> List[str]:
        return list(self._attributes.keys())

    def __getattr__(self, key):
        return self._attributes[key]


class SubRegion:

    _DATA_URL = _URL_PREFIX + '/country/{country}/region/{region}/sub_region/{subregion}' + _DATE_URL_SUFFIX

    def __init__(self, pynacov: 'PyNaCov', country: 'Country', region: 'Region', subregion_id: str):
        self.id = subregion_id
        self.name = None  # type: Optional[str]
        self._pynacov = pynacov
        self._country = country
        self._region = region
        self._data = {}  # type: Dict[date, Data]

    def get_data(self, from_date: date):
        url = SubRegion._DATA_URL.format(
            country=self._country.id,
            region=self._region.id,
            subregion=self.id,
            from_date=from_date.isoformat(),
            to_date=from_date.isoformat(),
        )
        response = requests.get(url).json()
        self._pynacov.update_from_data(response)
        return self._data

    def update_from_geo(self, response: dict):
        self.name = response['name']

    def update_from_data(self, subregion_data: dict):
        d = Data(subregion_data)
        self._data[d.date] = d
        if self.name is None:
            self.name = subregion_data['name']


class Region:

    _DATA_URL = _URL_PREFIX + '/country/{country}/region/{region}' + _DATE_URL_SUFFIX
    _LIST_SUBREGIONS_URL = _URL_PREFIX + '/countries/{country}/regions/{region}/sub_regions'

    def __init__(self, pynacov: 'PyNaCov', country: 'Country', region_id: str):
        self.id = region_id
        self.name = None  # type: Optional[str]
        self._pynacov = pynacov
        self._country = country
        self._subregions = {}  # type: Dict[str, SubRegion]
        self._data = {}  # type: Dict[date, Data]

    @property
    def subregions(self) -> List[str]:
        url = Region._LIST_SUBREGIONS_URL.format(
            country=self._country.id,
            region=self.id,
        )
        response = requests.get(url).json()
        self._pynacov.update_from_geo(response)
        return list(self._subregions.keys())

    def __getitem__(self, subregion_id) -> SubRegion:
        self._subregions.setdefault(subregion_id, SubRegion(self._pynacov, self._country, self, subregion_id))
        return self._subregions[subregion_id]

    def update_from_geo(self, response: dict):
        for subregsion_dict in response:
            self[subregsion_dict['id']].update_from_geo(subregsion_dict)

    def update_from_data(self, region_data: dict):
        d = Data(region_data)
        self._data[d.date] = d
        if self.name is None:
            self.name = region_data['name']
        for subregion_data in region_data['sub_regions']:
            subregion_id = subregion_data['id']
            self[subregion_id].update_from_data(subregion_data)


class Country:

    _DATA_URL = _URL_PREFIX + '/country/{country}' + _DATE_URL_SUFFIX
    _LIST_REGIONS_URL = _URL_PREFIX + '/countries/{country}/regions'

    def __init__(self, pynacov: 'PyNaCov', country_id: str):
        self.id = country_id
        self.name = None  # type: Optional[str]
        self._pynacov = pynacov
        self._regions = {}  # type: Dict[str, Region]
        self._data = {}  # type: Dict[date, Data]

    @property
    def regions(self):
        return None

    def __getitem__(self, region_id) -> Region:
        self._regions.setdefault(region_id, Region(self._pynacov, self, region_id))
        return self._regions[region_id]

    def update_from_geo(self, response: dict):
        for region_id, region_data in response.items():
            self[region_id].update_from_geo(region_data)

    def update_from_data(self, response_date: date, country_data: dict):
        d = Data(country_data)
        self._data[d.date] = d
        if self.name is None:
            self.name = country_data['name']
        for region in country_data['regions']:
            region_id = region['id']
            self[region_id].update_from_data(region)


class PyNaCov:

    _LIST_COUNTRIES_URL = _URL_PREFIX + '/countries'

    def __init__(self):
        self._geo_update = False
        self._countries = {}

    @property
    def countries(self):
        return None

    def update_from_data(self, response: dict):
        for date_str, data in response['dates'].items():
            for key, country_data in data['countries'].items():
                if key != 'info':
                    country_id = country_data['id']
                    self[country_id].update_from_data(date.fromisoformat(date_str), country_data)

    def update_from_geo(self, response: dict):
        for country_dict in response['countries']:
            country_id, country_data = list(country_dict.items())[0]
            self[country_id].update_from_geo(country_data)

    def __getitem__(self, country_id) -> Country:
        self._countries.setdefault(country_id, Country(self, country_id))
        return self._countries[country_id]


if __name__ == '__main__':
    source = PyNaCov()
    source['spain']['canarias'].subregions
    lanzarote = source['spain']['canarias']['lanzarote']
    for date, data in lanzarote.get_data(date.today()).items():
        new = data.today_confirmed - data.yesterday_confirmed
        print(new)
