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

    def __init__(self, Shortname, providerAccountId, zip, start_time, end_time):
        self.Shortname = str(Shortname)
        self.providerAccountId = str(providerAccountId)
        self.masterTariffId = ''
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

    def electricity_profile(self):  # create a load profile for the customer from start time to end time.
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

    def pvWatts(self): # does PV watts calc for given zipcode. Equivalent to PVWatts.py
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

    def calc_no_solar_or_storage(self): #returns a cost value for start-end time given no solar/storage. based on the load profile given above
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

    def retrieve_rates(self): #given the cost and load profile, returns a net hourly profile of rates.
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

    def run_calculation(self): #not used, test code, crashes server
        url = "https://api.genability.com/rest/v1/ondemand/calculate"
        account_json = {
        "fromDateTime": self.start_time,
        "toDateTime": self.end_time,
        "masterTariffId": self.masterTariffId,
        "groupBy": "HOUR",
        "detailLevel": "CHARGE_TYPE",
        "minimums": "true",

        "propertyInputs": [
        {
            "keyName": "consumption",
            "dataValue": "1",
            #below is the load profile
            #"dataSeries": [1.58, 1.58, 1.58, 1.58, 1.59, 1.60, 1.61, 1.62, 1.63, 1.63, 1.64, 1.64, 1.66, 1.68, 1.70, 1.73, 1.75, 1.76, 1.78, 1.80, 1.80, 1.81, 1.81, 1.81, 1.84, 1.88, 1.91, 1.95, 1.97, 1.98, 2.00, 2.01, 2.02, 2.03, 2.04, 2.05, 2.06, 2.07, 2.08, 2.09, 2.09, 2.11, 2.12, 2.13, 2.13, 2.11, 2.09, 2.08, 2.07, 2.05, 2.03, 2.02, 2.01, 2.01, 2.01, 2.01, 2.02, 2.02, 2.03, 2.04, 2.02, 1.99, 1.96, 1.92, 1.90, 1.89, 1.88, 1.86, 1.85, 1.83, 1.82, 1.79, 1.77, 1.74, 1.71, 1.67, 1.65, 1.63, 1.61, 1.60, 1.58, 1.55, 1.53, 1.51, 1.51, 1.51, 1.52, 1.52, 1.54, 1.56, 1.58, 1.60, 1.60, 1.59, 1.58, 1.58, 1.58, 1.59, 1.59, 1.60, 1.61, 1.63, 1.65, 1.67, 1.67, 1.67, 1.67, 1.67, 1.69, 1.72, 1.74, 1.77, 1.78, 1.79, 1.79, 1.80, 1.80, 1.79, 1.79, 1.78, 1.81, 1.85, 1.89, 1.94, 1.96, 1.97, 1.98, 2.00, 2.01, 2.02, 2.04, 2.05, 2.06, 2.06, 2.07, 2.07, 2.08, 2.09, 2.11, 2.12, 2.12, 2.12, 2.12, 2.12, 2.12, 2.11, 2.09, 2.08, 2.08, 2.08, 2.08, 2.08, 2.07, 2.07, 2.06, 2.05, 2.03, 2.00, 1.97, 1.94, 1.91, 1.90, 1.88, 1.86, 1.84, 1.83, 1.82, 1.81, 1.78, 1.74, 1.70, 1.66, 1.65, 1.64, 1.64, 1.63, 1.61, 1.57, 1.54, 1.51, 1.51, 1.51, 1.52, 1.52, 1.54, 1.56, 1.58, 1.60, 1.60, 1.59, 1.58, 1.57, 1.54, 1.54, 1.54, 1.54, 1.55, 1.56, 1.56, 1.57, 1.58, 1.57, 1.57, 1.57, 1.58, 1.61, 1.63, 1.65, 1.68, 1.71, 1.73, 1.76, 1.78, 1.79, 1.80, 1.81, 1.83, 1.85, 1.88, 1.90, 1.91, 1.92, 1.92, 1.93, 1.93, 1.93, 1.92, 1.91, 1.92, 1.93, 1.93, 1.94, 1.95, 1.97, 1.99, 2.01, 2.01, 2.00, 1.99, 1.98, 1.97, 1.97, 1.96, 1.96, 1.96, 1.95, 1.95, 1.94, 1.95, 1.96, 1.97, 1.98, 1.97, 1.96, 1.94, 1.92, 1.90, 1.89, 1.87, 1.86, 1.84, 1.81, 1.79, 1.76, 1.74, 1.72, 1.71, 1.69, 1.66, 1.64, 1.61, 1.58, 1.56, 1.54, 1.52, 1.49, 1.48, 1.49, 1.49, 1.50, 1.52, 1.53, 1.55, 1.57, 1.57, 1.56, 1.55, 1.53, 1.51, 1.51, 1.52, 1.52, 1.53, 1.53, 1.54, 1.55, 1.55, 1.55, 1.55, 1.55, 1.56, 1.58, 1.61, 1.62, 1.65, 1.67, 1.70, 1.73, 1.74, 1.74, 1.75, 1.76, 1.77, 1.80, 1.82, 1.85, 1.86, 1.86, 1.86, 1.86, 1.86, 1.86, 1.85, 1.85, 1.85, 1.86, 1.86, 1.87, 1.88, 1.90, 1.91, 1.93, 1.93, 1.92, 1.91, 1.90, 1.90, 1.89, 1.89, 1.88, 1.88, 1.88, 1.88, 1.87, 1.88, 1.90, 1.91, 1.93, 1.92, 1.90, 1.88, 1.86, 1.85, 1.84, 1.83, 1.82, 1.80, 1.78, 1.76, 1.73, 1.71, 1.69, 1.68, 1.66, 1.64, 1.61, 1.58, 1.55, 1.52, 1.50, 1.48, 1.46, 1.46, 1.46, 1.47, 1.47, 1.49, 1.51, 1.53, 1.55, 1.54, 1.53, 1.52, 1.50, 1.48, 1.48, 1.49, 1.50, 1.51, 1.51, 1.52, 1.52, 1.52, 1.52, 1.52, 1.52, 1.54, 1.56, 1.58, 1.60, 1.62, 1.64, 1.66, 1.69, 1.70, 1.70, 1.70, 1.70, 1.72, 1.74, 1.77, 1.79, 1.80, 1.80, 1.80, 1.80, 1.80, 1.79, 1.79, 1.78, 1.78, 1.79, 1.79, 1.80, 1.81, 1.82, 1.83, 1.85, 1.85, 1.84, 1.83, 1.83, 1.82, 1.82, 1.81, 1.80, 1.80, 1.80, 1.80, 1.80, 1.82, 1.83, 1.85, 1.87, 1.86, 1.85, 1.83, 1.81, 1.80, 1.79, 1.79, 1.78, 1.76, 1.74, 1.73, 1.71, 1.69, 1.67, 1.65, 1.63, 1.61, 1.57, 1.54, 1.51, 1.49, 1.47, 1.45, 1.43, 1.43, 1.44, 1.44, 1.45, 1.46, 1.48, 1.50, 1.52, 1.52, 1.51, 1.49, 1.49, 1.52, 1.53, 1.53, 1.54, 1.55, 1.55, 1.56, 1.56, 1.57, 1.57, 1.57, 1.57, 1.58, 1.60, 1.62, 1.64, 1.66, 1.68, 1.70, 1.73, 1.73, 1.73, 1.74, 1.74, 1.76, 1.78, 1.80, 1.83, 1.84, 1.84, 1.84, 1.85, 1.84, 1.84, 1.83, 1.83, 1.83, 1.83, 1.84, 1.85, 1.86, 1.86, 1.88, 1.89, 1.89, 1.88, 1.87, 1.86, 1.86, 1.85, 1.85, 1.84, 1.84, 1.84, 1.84, 1.84, 1.85, 1.87, 1.88, 1.90, 1.89, 1.88, 1.86, 1.84, 1.83, 1.82, 1.82, 1.81, 1.79, 1.77, 1.75, 1.73, 1.71, 1.69, 1.68, 1.66, 1.63, 1.60, 1.57, 1.55, 1.52, 1.50, 1.48, 1.46, 1.46, 1.47, 1.48, 1.48, 1.50, 1.52, 1.54, 1.55, 1.56, 1.54, 1.53, 1.54, 1.57, 1.57, 1.58, 1.58, 1.59, 1.59, 1.60, 1.60, 1.61, 1.61, 1.61, 1.61, 1.62, 1.64, 1.66, 1.68, 1.70, 1.72, 1.74, 1.76, 1.76, 1.77, 1.77, 1.78, 1.79, 1.82, 1.84, 1.86, 1.88, 1.88, 1.88, 1.89, 1.89, 1.88, 1.88, 1.88, 1.88, 1.88, 1.88, 1.89, 1.90, 1.91, 1.92, 1.93, 1.93, 1.91, 1.91, 1.90, 1.89, 1.89, 1.89, 1.88, 1.88, 1.88, 1.88, 1.88, 1.89, 1.90, 1.92, 1.93, 1.92, 1.91, 1.89, 1.87, 1.86, 1.85, 1.85, 1.84, 1.82, 1.80, 1.78, 1.76, 1.74, 1.72, 1.70, 1.68, 1.66, 1.63, 1.61, 1.58, 1.56, 1.54, 1.52, 1.49, 1.49, 1.50, 1.51, 1.52, 1.53, 1.55, 1.57, 1.59, 1.59, 1.58, 1.58, 1.57, 1.58, 1.58, 1.58, 1.58, 1.59, 1.60, 1.62, 1.63, 1.64, 1.64, 1.63, 1.63, 1.64, 1.67, 1.70, 1.73, 1.74, 1.76, 1.77, 1.78, 1.79, 1.79, 1.78, 1.78, 1.80, 1.83, 1.86, 1.90, 1.91, 1.92, 1.92, 1.93, 1.93, 1.94, 1.94, 1.95, 1.96, 1.97, 1.98, 1.99, 1.99, 2.01, 2.01, 2.02, 2.02, 2.01, 2.01, 2.00, 2.00],
            "dataSeries": [1],
            "unit":"kWh"
          }]
        }
        r = requests.post(url, auth=(external_loadengine_app_id, external_loadengine_app_key),
                          json=account_json)
        return r.json()


store = ""

def main():
    test = TariffEngine("LA", "1717", "90001")
    test.calc_no_solar_or_storage()
    store = test.retrieve_rates()
    print(store)
    rates = []
    output = store["results"][0]["items"]
    for i in range(len(output)):
        if output[i]["chargeType"] == "CONSUMPTION_BASED":
            rates += [output[i]["rateAmount"]]
    print(rates)
    print(len(rates))

def main2():
    test = TariffEngine("LA", "1717", "90001","2015-01-01T9:00:00", "2015-01-01T10:00:00")
    print(test.run_calculation())

def main3():
    test = TariffEngine("LosAngeles", "206683", "90001", "2018-01-01T00:00:00", "2018-02-01T00:00:00")
    test.create_account()
    print(test.get_utility())
    print(test.set_utility())
    print(test.get_tarrif())
    print(test.set_tarrif())
    print(test.electricity_profile())
    print(test.pvWatts())
    print(test.calc_no_solar_or_storage())
    store = test.retrieve_rates()
    print(store)


    rates = []
    output = store["results"][0]["items"]
    prev_time = ""
    for i in range(len(output)):
        curr_time = output[i]["fromDateTime"]
        if output[i]["chargeType"] == "CONSUMPTION_BASED" and curr_time != prev_time:
            rates += [output[i]["rateAmount"]]
            prev_time = curr_time
    print(rates)
    #print(len(rates))

main3()
