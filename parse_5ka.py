import requests
import json
from pathlib import Path
import time
import os

class Parse_error(Exception):
    def __init__(self, txt):
        self.text = txt


class Parse_5ka:
    _params = {
        'records_per_page': 100,
        'page': 1,
    }

    _headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3'
    }

    def __init__(self, start_url, result_path):
        self.start_url = start_url
        self.result_path = result_path

    @staticmethod
    def __get_response(url, *args, **kwargs) -> requests.Response:
        while True:
            try:
                response = requests.get(url, *args, **kwargs)
                if response.status_code > 399:
                    raise Parse_error('response.status_code')
                time.sleep(0.1)
                return response
            except (requests.exceptions.RequestException, Parse_error):
                time.sleep(1)
                continue

    def run(self):
        for product in self.parse(self.start_url):
            path = self.result_path.joinpath(f'{product["id"]}.json')
            self._save_to_json(product, path)

    def parse(self, url):
        params = self._params
        while url:
            response = self.__get_response(url, params=params, headers=self._headers)
            if params:
                params = {}
            data = json.loads(response.text)
            url = data.get('next')
            for product in data.get('results'):
                yield product

    @staticmethod
    def _save_to_json(data, path: Path):
        with path.open('w', encoding='UTF-8') as file:
            json.dump(data, file, ensure_ascii=False)


class Parse_5ka_types(Parse_5ka):

    def __init__(self, start_url, type_url, result_path):
        super().__init__(start_url, result_path)
        self.type_url = type_url

    def __get_types(self, url):
        response = requests.get(url, headers=self._headers)
        print(response)
        return response.json()

    def run(self):
        for type in self.__get_types(self.type_url):

            path = self.result_path.joinpath(f'{type["parent_group_code"]}.json')
            data = {
                "name": type["parent_group_name"],
                "code": type["parent_group_code"],
                "products": [],
            }
            self._params["categories"] = type["parent_group_code"]
            self._save_to_json(data, path)

            for products in self.parse(self.start_url):
                self._add_to_json(products, 'products', path)

    @staticmethod
    def _add_to_json(new_data, dict_key, path: Path):
        with path.open('r', encoding='UTF-8') as file:
            data = json.load(file)
            print(type(data))
            data[dict_key] += [(new_data)]
        with path.open('w', encoding='UTF-8') as output:
            json.dump(data, output, ensure_ascii=False)


if __name__ == '__main__':
    json_dir = 'data'
    url = 'https://5ka.ru/api/v2/special_offers/'
    url_types = 'https://5ka.ru/api/v2/categories/'

    Path(json_dir).mkdir(parents=True, exist_ok=True)
    result_path = Path(__file__).parent.joinpath(json_dir)

    parser = Parse_5ka_types(url, url_types, result_path)
    parser.run()

    print(f'Completed\nPlease check {result_path} directory')
