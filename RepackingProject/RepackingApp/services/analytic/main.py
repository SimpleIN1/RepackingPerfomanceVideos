import json

from RepackingApp.services.analytic.converter_v2_7 import AnalyticConverterV27
from RepackingApp.services.analytic.converter_v3_0 import AnalyticConverterV30, check_analytic_converter_v30


class AnalyticConverterFactory:
    def get_converter(self, data):
        if check_analytic_converter_v30(data):
            return AnalyticConverterV30
        else:
            return AnalyticConverterV27


if __name__ == '__main__':
    path = "../../../files/analytic_data-df718723832839b9c6ed3cfec63048f32ede462d-1776567672234.json"
    path_save = "analytic_test.csv"
    with open(path) as f:
        json_data = json.load(f)

    data = json_data["data"]
    converter = AnalyticConverterFactory().get_converter(data)
    c = converter(data)
    c.execute()
    c.save_analytic_data(path_save)
