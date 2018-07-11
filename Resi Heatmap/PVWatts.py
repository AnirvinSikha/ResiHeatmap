import requests
from uszipcode import ZipcodeSearchEngine

key = "iKiCqfldxiivLAGQHjQ2y4pXdM5HKk2UNDxnyxiM"

url = "https://developer.nrel.gov/api/alt-fuel-stations/v1.json?fuel_type=E85,ELEC&state=CA&limit=2&api_key=iKiCqfldxiivLAGQHjQ2y4pXdM5HKk2UNDxnyxiM&format=JSON"

url2 = "https://developer.nrel.gov/api/pvwatts/v6.json?api_key=iKiCqfldxiivLAGQHjQ2y4pXdM5HKk2UNDxnyxiM&lat=40&lon=-105&system_capacity=4&azimuth=180&tilt=40&array_type=1&module_type=1&losses=10"
# json output

url3 = "https://developer.nrel.gov/api/pvwatts/v6.format?parameters"

url4 = "https://developer.nrel.gov/api/pvwatts/v6.json?api_key=iKiCqfldxiivLAGQHjQ2y4pXdM5HKk2UNDxnyxiM"

url_prime = "https://developer.nrel.gov/api/pvwatts/v6.json?"

def run(zipcode = None):
    if zipcode == None:
        zipcode = raw_input("What zipcode would you like to check?")
    conversion = ZipcodeSearchEngine().by_zipcode(zipcode)
    lat = conversion["Latitude"]
    lon = conversion["Longitude"]

    parameters = {
        "format": "JSON",
        "api_key": "iKiCqfldxiivLAGQHjQ2y4pXdM5HKk2UNDxnyxiM",
        "system_capacity": '6',
        "module_type": '0',  # Legend: 0 Standard, 1 Premium, 2 Thin Film
        "losses": '2',  # Legend : -5 to 99
        "array_type": '1', # Legend: 0	Fixed - Open Rack, 1 Fixed - Roof Mounted, 2	1-Axis, 3 1-Axis Backtracking, 4 2-Axis
        "tilt": '10',
        "azimuth": '180',
        "dataset": "tmy3", #subject to change
        "lat": str(lat),
        "lon": str(lon),
        "timeframe": "hourly"
    }
    response = requests.get(url_prime, parameters)
    #print response.json()
    #j = json.loads(response.json())
    outputs = response.json()["outputs"]
    for i in range(len(outputs["ac"])):
        outputs["ac"][i] = outputs["ac"][i]/1000
    return outputs["ac"]
    #visualize(outputs)


