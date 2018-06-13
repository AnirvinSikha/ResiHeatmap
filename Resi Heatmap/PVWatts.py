import requests
import json, sys, datetime

#git addition

key = "iKiCqfldxiivLAGQHjQ2y4pXdM5HKk2UNDxnyxiM"

url = "https://developer.nrel.gov/api/alt-fuel-stations/v1.json?fuel_type=E85,ELEC&state=CA&limit=2&api_key=iKiCqfldxiivLAGQHjQ2y4pXdM5HKk2UNDxnyxiM&format=JSON"

url2  = "https://developer.nrel.gov/api/pvwatts/v6.json?api_key=iKiCqfldxiivLAGQHjQ2y4pXdM5HKk2UNDxnyxiM&lat=40&lon=-105&system_capacity=4&azimuth=180&tilt=40&array_type=1&module_type=1&losses=10"
#json output

url3 = "https://developer.nrel.gov/api/pvwatts/v6.format?parameters"

url4 = "https://developer.nrel.gov/api/pvwatts/v6.json?api_key=iKiCqfldxiivLAGQHjQ2y4pXdM5HKk2UNDxnyxiM"

url_prime = "https://developer.nrel.gov/api/pvwatts/v6.json?"

parameters = {
        "format": "JSON",
        "api_key": "iKiCqfldxiivLAGQHjQ2y4pXdM5HKk2UNDxnyxiM",
        "system_capacity": '6', #anirvin ask about this one
        "module_type": '0', #Legend: 0 Standard, 1 Premium, 2 Thin Film
        "losses": '10', #Legend : -5 to 99
        "array_type": '0', # anirvin ask about this one. Legend: 0	Fixed - Open Rack, 1 Fixed - Roof Mounted, 2	1-Axis, 3 1-Axis Backtracking, 4 2-Axis
        "tilt": '10',
        "azimuth": '180',
    }


response = requests.get(url_prime, parameters)
print response.json()

