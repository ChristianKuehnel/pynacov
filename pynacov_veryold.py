import requests
from datetime import date, timedelta
from typing import List, Dict

_URL_PREFIX = 'https://api.covid19tracking.narrativa.com/api'
_LIST_COUNTRIES_URL = _URL_PREFIX + '/countries'
_LIST_REGIONS_URL = _LIST_COUNTRIES_URL + '/{country}/regions'
_REGION_DATA_URL = _URL_PREFIX + '/country/{country}/region/{region}?date_from={date_from}&date_to={date_to}'


class _Geography:

    def __init__(self, *, geo_id: str = None, json_config: dict = None):
        if geo_id is None and json_config is None:
            raise ValueError('Either geo_id or json_config must not be None!')
        self._json_config = json_config
        self._id = geo_id
        print(json_config)

    @property
    def id(self) -> str:
        if self._json_config is not None:
            return self._json_config['id']
        return self._id

    @property
    def name(self) -> str:
        return self._json_config['name']

    def __str__(self) -> str:
        return '{} ({})'.format(self.name, self.id)


class Region(_Geography):

    def __init__(self, country_id, *, geo_id: str = None, json_config: dict = None):
        self.country_id = country_id
        super().__init__(geo_id=geo_id, json_config=json_config)

    @property
    def seven_day_incidence(self):
        to_date = date.today()
        from_date = to_date - timedelta(days=7)
        url = _REGION_DATA_URL.format(
            country=self.country_id,
            region=self.id,
            date_from=from_date.isoformat(),
            date_to=to_date.isoformat())
        response = requests.get(url).json()
        print(response)


class Country(_Geography):

    def __init__(self, *, json_config: dict = None, country_id: str = None):
        super().__init__(json_config=json_config, geo_id=country_id)
        self._regions = {}  # type: Dict[str, Region]

    def __getitem__(self, region_id: str) -> Region:
        if len(self._regions) == 0:
            return Region(country_id=self.id, geo_id=region_id)
        return self._countries[region_id]

    @property
    def regions(self) -> List[Region]:
        if len(self._regions) == 0:
            response = requests.get(_LIST_REGIONS_URL.format(country=self.id)).json()
            for country_dict in response['countries']:
                if self.id in country_dict:
                    for region_dict in country_dict[self.id] :
                        print(region_dict)
                        r = Region(country_id=self.id, json_config=region_dict)
                        self._regions[r.id] = r
        return list(self._regions.values())


class PyNaCov:

    def __init__(self):
        self._countries = {}  # type: Dict[str, Country]

    @property
    def countries(self) -> List[Country]:
        if len(self._countries) == 0:
            response = requests.get(_LIST_COUNTRIES_URL).json()
            for country_dict in response['countries']:
                c = Country(json_config=country_dict)
                self._countries[c.id] = c
        return list(self._countries.values())

    def __getitem__(self, country_id: str) -> Country:
        if len(self._countries) == 0:
            return Country(country_id=country_id)
        return self._countries[country_id]


if __name__ == '__main__':
    source = PyNaCov()
    #print(source.countries)
    spain = source['spain']
    #print(spain.regions)
    canarias = spain['canarias']
    canarias.seven_day_incidence