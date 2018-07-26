'''
The entire Genability interface. Performs API calls in 3 steps
1. Get the utilities for a given zip
2. Get the rates for a given utility
3. Get the list of import/export values for 8760 hrs for set rate

'''

from __future__ import print_function
import requests, json
import Parser
import numpy as np
from datetime import timedelta, datetime
import pandas as pd
import os

external_loadengine_app_id = "81a4b573-2007-4df9-bfcc-811d94d34c72"
external_loadengine_app_key = "658f2f17-04f0-4ed0-855f-e1de3baa3449"


class TariffEngine():

    def __init__(self, Shortname, providerAccountId, zip, start_time, end_time, master_tarrifID = None):
        self.Shortname = str(Shortname)
        self.providerAccountId = str(providerAccountId)
        self.masterTariffId = master_tarrifID
        self.tarrifID = ''
        self.loads = []
        self.verbose = False
        self.zip = zip
        self.start_time = str(start_time)
        self.end_time = str(end_time)


    def __str__(self):
        return "Site name:", self.Shortname, "providerAccountId:", self.providerAccountId

    def create_account(self): #creates a customer based on zipcode
        account_json = {
            'accountName': self.Shortname,
            'providerAccountId': self.providerAccountId,
            "address":{
                "zip": self.zip,
                "country": "US",
                },
            "properties": {
                "customerClass": {
                    "keyName": "customerClass", #what type of customer: 1-residential, 2-commercial, 4 -special
                    "dataValue": "1"
                }
            }
        }
        Url_put = 'https://api.genability.com/rest/v1/accounts'
        p = requests.put(Url_put, auth=(external_loadengine_app_id, external_loadengine_app_key), json=account_json)
        # GET
        Url_get = "https://api.genability.com/rest/v1/accounts/pid/" + self.providerAccountId
        g = requests.get(Url_get,  auth=(external_loadengine_app_id, external_loadengine_app_key), json=account_json)
        return g.json()


    def get_utility(self): #based on customer and zipcode, selects utility
            url = 'https://api.genability.com/rest/public/lses?postCode=' + str(self.zip) + \
                  '&country=US&residentialServiceTypes=ELECTRICITY&sortOn=totalCustomers&sortOrder=DESC'
            g = requests.get(url, auth=(external_loadengine_app_id, external_loadengine_app_key))
            return g.json()
    def set_utility(self): #based on available utilities, pick and set the best one
        url = 'https://api.genability.com/rest/v1/accounts/pid/' + self.providerAccountId + '/properties'
        account_json = {
            "keyName": "lseId",
            "dataValue": "1228", #1228 is SCE ID
        }
        p = requests.put(url, auth=(external_loadengine_app_id, external_loadengine_app_key), json=account_json)
        return p.json()

    def get_tarrif(self):  # retrieves a list of tariffs from the set utility
        url_get = 'https://api.genability.com/rest/v1/accounts/pid/'+ self.providerAccountId + '/tariffs?serviceTypes=ELECTRICITY'
        g = requests.get(url_get, auth=(external_loadengine_app_id, external_loadengine_app_key))
        return g.json()  # 3250148 is TOU-A

    def set_tarrif(self):  # set one tarrif as the rate to use for the set utility
        self.masterTariffId = str(3250149)
        properties = {
            "keyName": "masterTariffId",
            "dataValue": self.masterTariffId,
        }
        url_put = 'https://api.genability.com/rest/v1/accounts/pid/' + self.providerAccountId + '/properties'
        p = requests.put(url_put, auth=(external_loadengine_app_id, external_loadengine_app_key), json=properties)
        return p.json()

    def electricity_profile(self):  # bad code. create a load profile for the customer from start time to end time.
        account_json = {
          "providerAccountId": self.providerAccountId,
          "providerProfileId": "LA bills 2",
          "profileName": "Electricity Bills 2",
          "description": "Electricity consumption",
          "isDefault": True,
          "serviceTypes": "ELECTRICITY",
          "sourceId": "ReadingEntry",
          "readingData": [
              {"fromDateTime": self.start_time,
               "toDateTime": self.end_time,
               "quantityUnit": "kWh",
               "quantityValue": "-1"
               },
            ]
        }
        url = 'https://api.genability.com/rest/v1/profiles'
        p = requests.put(url, auth=(external_loadengine_app_id, external_loadengine_app_key), json=account_json)
        return p.json()

    def pvWatts(self): # bad code. does PV watts calc for given zipcode. Equivalent to PVWatts.py
        account_json = {
          "providerAccountId" : self.providerAccountId,
          "providerProfileId" : "LA bills",
          "groupBy" : "YEAR",
          "serviceTypes" : "SOLAR_PV",
          "source": {
            "sourceId":"PVWatts",
            "sourceVersion":"5"
          },
          "properties" : {
            "systemSize" : {
              "keyName" : "systemSize",
              "dataValue" : "6"
            },
            "azimuth" : {
              "keyName" : "azimuth",
              "dataValue" : "180"
            },
            "losses" : {
              "keyName" : "losses",
              "dataValue" : "2"
            },
            "inverterEfficiency" : {
              "keyName" : "inverterEfficiency",
              "dataValue" : "96"
            },
            "tilt" : {
              "keyName": "tilt",
              "dataValue": "10"
            }
          }
        }
        url = 'https://api.genability.com/rest/v1/profiles'
        p = requests.put(url, auth=(external_loadengine_app_id, external_loadengine_app_key), json=account_json)
        return p.json()

    def calc_no_solar_or_storage(self): #bad code. returns a cost value for start-end time given no solar/storage. based on the load profile given above
        account_json = {
            "fromDateTime": self.start_time,
            "toDateTime": self.end_time,
            "useIntelligentBaselining": "true",
            "includeDefaultProfile": "true",
            "autoBaseline": "true",
            "minimums": "false",
            "detailLevel": "CHARGE_TYPE",
            "groupBy": "HOUR",
            "fields": "EXT"
            }
        url = 'https://api.genability.com/rest/v1/accounts/pid/' + self.providerAccountId + '/calculate/'
        p = requests.post(url, auth=(external_loadengine_app_id, external_loadengine_app_key), json=account_json)
        return p.json()

    def retrieve_rates(self): #bad code. given the cost and load profile, returns a net hourly profile of rates.
        account_json = {
            "fromDateTime": self.start_time,
            "toDateTime": self.end_time,
            "useIntelligentBaselining": "true",
            "includeDefaultProfile": "true",
            "autoBaseline": "true",
            "minimums": "false",
            "detailLevel": "CHARGE_TYPE_AND_TOU",
            "groupBy": "HOUR",
            "fields": "EXT",
            "sortOn": "fromDateTime",
            "tariffInputs": [{
                "keyName": "profileId",
                "dataValue": "5b522155fca3ef2db58cb4ea", #LA solar profile - 5b522155fca3ef2db58cb4ea
                "operator": "-"
            }]
        }
        url = "https://api.genability.com/rest/v1/accounts/pid/"+ self.providerAccountId + "/calculate/"
        p = requests.post(url, auth=(external_loadengine_app_id, external_loadengine_app_key), json=account_json)
        return p.json()

    def import_rates(self): #retrieves import rates for a given tariff
        url = "https://api.genability.com/rest/v1/ondemand/calculate"
        account_json = {
          "fromDateTime": self.start_time,
          "toDateTime": self.end_time,
          "masterTariffId": self.masterTariffId,
          "groupBy": "HOUR",
          "detailLevel": "CHARGE_TYPE",
          "minimums": "false",
          "sortOn": "fromDateTime",
          "propertyInputs": [
          {
            "keyName": "consumption",
            "dataValue": "10000000"
          }]
        }
        r = requests.post(url, auth=(external_loadengine_app_id, external_loadengine_app_key),
                          json=account_json)
        return r.json()

    def export_rates(self): # retrieves export rates for a given tarrif
        url = "https://api.genability.com/rest/v1/ondemand/calculate"
        account_json = {
          "fromDateTime": self.start_time,
          "toDateTime": self.end_time,
          "masterTariffId": self.masterTariffId,
          "groupBy": "HOUR",
          "detailLevel": "CHARGE_TYPE",
          "minimums": "false",
          "sortOn": "fromDateTime",
          "propertyInputs": [
          {
            "keyName": "consumption",
            "dataValue": "-1000000"
          }]
        }
        r = requests.post(url, auth=(external_loadengine_app_id, external_loadengine_app_key),
                          json=account_json)
        return r.json()


def get_rates():
    '''
    create a
    :return:
    '''
    test = TariffEngine("LA", "1717", "90001", "2018-01-01T00:00:00", "2019-01-01T00:00:00", 3250148)

    import_rates = []
    store = test.import_rates()

    output = store["results"][0]["items"]
    prev_time = ""
    for i in range(len(output)):
        curr_time = output[i]["fromDateTime"]
        if output[i]["chargeType"] == "CONSUMPTION_BASED" and curr_time != prev_time:
            import_rates += [output[i]["rateAmount"]]
            prev_time = curr_time
    print("import rates:")
    print(import_rates)
    print("length:")
    print(len(import_rates))

    export_rates = []
    store = test.export_rates()

    output = store["results"][0]["items"]
    prev_time = ""
    for i in range(len(output)):
        curr_time = output[i]["fromDateTime"]
        if output[i]["chargeType"] == "CONSUMPTION_BASED" and curr_time != prev_time:
            export_rates += [output[i]["rateAmount"]]
            prev_time = curr_time
    print("export rates:")
    print(export_rates)
    print("length:")
    print(len(export_rates))


get_rates()
