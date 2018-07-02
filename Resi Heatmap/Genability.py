from __future__ import print_function
import requests, json
import numpy as np
from datetime import timedelta, datetime
import pandas as pd
import os

external_loadengine_app_id = "81a4b573-2007-4df9-bfcc-811d94d34c72"
external_loadengine_app_key = "658f2f17-04f0-4ed0-855f-e1de3baa3449"

class TariffEngine():

    def __init__(self, Shortname, providerAccountId):
        self.Shortname = str(Shortname)
        self.providerAccountId = str(providerAccountId)
        self.masterTariffId = ''
        self.loads = []
        self.verbose = False


    def __str__(self):
        return "Site name:", self.Shortname, "providerAccountId:", self.providerAccountId


    def create_account(self, address):
        account_json = {
            'providerAccountId': self.providerAccountId,
            "accountName": self.Shortname,
            "address": address,
            "properties": {
                "customerClass": {
                    "keyName": "customerClass",
                    "dataValue": "2"
                }
            }
        }
        Url = 'https://api.genability.com/rest/v1/accounts'
        r = requests.post(Url, auth=(external_loadengine_app_id, external_loadengine_app_key),
                          headers={'Content-Type': 'application/json; charset=utf-8'}, json=account_json)
        # GET https://api.genability.com/rest/v1/accounts/pid/83725
        if self.verbose:
            print(r)




    def set_tariff(self, masterTariffId):
        self.masterTariffId = masterTariffId
        tariff_json = {"keyName": "masterTariffId",
                       "dataValue": masterTariffId}

        Url = 'https://api.genability.com/rest/v1/accounts/pid/' + self.providerAccountId + '/properties'
        r = requests.put(Url, auth=(external_loadengine_app_id, external_loadengine_app_key),
                         headers={'Content-Type': 'application/json; charset=utf-8'}, json=tariff_json)

        if self.verbose:
            print(r)

    def get_tariffs(self):
        Url = 'https://api.genability.com/rest/v1/accounts/pid/' + self.providerAccountId + '/tariffs'
        r = requests.get(Url, auth=(external_loadengine_app_id, external_loadengine_app_key),
                         headers={'Content-Type': 'application/json; charset=utf-8'})

        if self.verbose:
            print(r)

        d = json.loads(r.content)


        df = pd.DataFrame(columns=['tariffId', 'masterTariffId', 'tariffCode', 'tariffName'])
        for t in d['results']:
            df = df.append(t, ignore_index=True)



        return df


    def add_load(self, series, profileTag):
        readingData = []


        series = series.dropna()
        for i in range(0, len(series)):
            r = {"fromDateTime": get_iso_date(series.index[i]),
                 "quantityUnit": "kWh",
                 "quantityValue": str(series[i]),
                 "toDateTime": get_iso_date(series.index[i] + timedelta(minutes=15))
                 }
            readingData.append(r)

        load_dict = {
            "providerAccountId": self.providerAccountId,
            "providerProfileId": self.providerAccountId + profileTag,
            "profileName": "Load Baseline",
            "description": "Pre-solar electricity usage data",
            "isDefault": "true",
            "serviceTypes": "ELECTRICITY",
            "sourceId": "ReadingEntry",
            "readingData": readingData
        }

        Url = 'https://api.genability.com/rest/v1/profiles'
        r = requests.post(Url, auth=(external_loadengine_app_id, external_loadengine_app_key),
                          headers={'Content-Type': 'application/json; charset=utf-8'}, json=load_dict)

        #  https://api.genability.com/rest/v1/profiles/pid/83725load02
        #  https://api.genability.com/rest/v1/profiles/pid/83725load02?populateIntervals=true&groupBy=MONTH

        self.loads.append(profileTag)

        if self.verbose:
            print(r)
            print(r.content)


    def delete_load(self, profileTag):
        Url = 'https://api.genability.com/rest/v1/profiles/pid/' + self.providerAccountId + profileTag
        r = requests.delete(Url, auth=(external_loadengine_app_id, external_loadengine_app_key),
                            headers={'Content-Type': 'application/json; charset=utf-8'})

        #  https://api.genability.com/rest/v1/profiles/pid/83725load02
        #  https://api.genability.com/rest/v1/profiles/pid/83725load02?populateIntervals=true&groupBy=MONTH

        if profileTag in self.loads:
            self.loads.remove(profileTag)

        if self.verbose:
            print(r)
            print(r.content)


    def simple_calculate(self, profileTag, start, end):
        profileId = self.get_profile_id(profileTag)

        calc_dict = {
            "fromDateTime": start.strftime("%Y-%m-%d"),
            "toDateTime": end.strftime("%Y-%m-%d"),
            "billingPeriod": False,
            "minimums": True,
            "detailLevel": "RATE",
            "groupBy": "MONTH",
            "profileId": profileId,


        }

        Url = 'https://api.genability.com/rest/v1/accounts/pid/' + self.providerAccountId + '/calculate/'
        r = requests.post(Url, auth=(external_loadengine_app_id, external_loadengine_app_key),
                          headers={'Content-Type': 'application/json; charset=utf-8'}, json=calc_dict)

        if self.verbose:
            print(r)
            print(r.content)

        df = self.parse_calculate(r.content)

        return df


    def get_profile_id(self, profileTag):
        Url = 'https://api.genability.com/rest/v1/profiles/pid/' + self.providerAccountId + profileTag
        r = requests.get(Url, auth=(external_loadengine_app_id, external_loadengine_app_key),
                         headers={'Content-Type': 'application/json; charset=utf-8'})

        d = json.loads(r.content)

        if self.verbose:
            print(r)
            print(r.content)

        profileId = d["results"][0]['profileId']

        return profileId


    def parse_calculate(self, json_data):

        d = json.loads(json_data)

        item_list = d['results'][0]['items']

        df = pd.DataFrame()
        df['DEMAND_BASED'] = 0
        df['CONSUMPTION_BASED'] = 0
        df['FIXED_PRICE'] = 0
        df['TOTAL'] = 0

        for i in item_list:
            df.loc[i['fromDateTime'], i['rateName']] = float(i['cost'])

            chargeType = i['chargeType']
            if chargeType in ['MINIMUM', 'QUANTITY']:
                chargeType = "FIXED_PRICE"

            if np.isnan(df.loc[i['fromDateTime'], chargeType]):
                df.loc[i['fromDateTime'], chargeType] = 0
            if np.isnan(df.loc[i['fromDateTime'], "TOTAL"]):
                df.loc[i['fromDateTime'], "TOTAL"] = 0

            #print i
            df.loc[i['fromDateTime'], chargeType] += float(i['cost'])
            df.loc[i['fromDateTime'], "TOTAL"] += float(i['cost'])

        return df


    def get_demand_savings(self, load, net_load):
        self.delete_load('profile1')
        self.delete_load('profile2')

        self.add_load(load, 'profile1')
        self.add_load(net_load, 'profile2')

        bills1 = self.simple_calculate('profile1')
        bills2 = self.simple_calculate('profile2')

        annual_demand_savings = bills1['DEMAND_BASED'].sum() - bills2['DEMAND_BASED'].sum()

        return annual_demand_savings, bills1, bills2


    def get_bills(self, net_load, profile_tag=None):

        if profile_tag == None:
            profile_tag = os.getusername()




        self.delete_load(profile_tag)
        self.add_load(net_load, profile_tag)
        bills = self.simple_calculate(profile_tag)
        return bills

def main():
    run = TariffEngine("test_customer", )
