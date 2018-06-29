import requests
from uszipcode import ZipcodeSearchEngine

key = "PyOaUYw1qozUQaNgWxuAEGBTSqffW0k48gCoZGsb"

def run(zipcode = None):
    if zipcode == None:
        zipcode = raw_input("What zipcode would you like to check?")
    conversion = ZipcodeSearchEngine().by_zipcode(zipcode)
    lat = conversion["Latitude"]
    lon = conversion["Longitude"]
    parameters = {
            "format": "json",
            "api_key": "PyOaUYw1qozUQaNgWxuAEGBTSqffW0k48gCoZGsb",
            "version": 5,
            "lat": str(lat),
            "lon": str(lon),
            #"ratesforutility": "Southern California Edison",
            "sector": "Residential"
        }

    url = "https://api.openei.org/utility_rates?parameters"

    response = requests.get(url, parameters)
    print response.json()

run()


