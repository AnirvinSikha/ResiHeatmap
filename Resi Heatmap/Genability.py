'''
The entire Genability interface. Performs API calls in 3 steps
1. Get the utilities for a given zip
2. Get the rates for a given utility
3. Get the list of import/export values for 8760 hrs for set rate

'''

from __future__ import print_function
import requests, json
import Parser
import csv
import pandas as pd
import os

external_loadengine_app_id = "81a4b573-2007-4df9-bfcc-811d94d34c72"
external_loadengine_app_key = "658f2f17-04f0-4ed0-855f-e1de3baa3449"


class TariffEngine():
    def __init__(self, Shortname, providerAccountId, zip, start_time, end_time, master_tarrifId=None):
        self.Shortname = str(Shortname)
        self.providerAccountId = str(providerAccountId)
        self.masterTariffId = master_tarrifId
        self.loads = []
        self.verbose = False
        self.zip = zip
        self.start_time = str(start_time)
        self.end_time = str(end_time)

    def __str__(self):
        return "Site name:", self.Shortname, "providerAccountId:", self.providerAccountId

    def insert_masterTarifID(self, id):
        id = str(id)
        self.masterTariffId = id

    def create_account(self):  # creates a customer based on zipcode
        account_json = {
            'accountName': self.Shortname,
            'providerAccountId': self.providerAccountId,
            "address": {
                "zip": self.zip,
                "country": "US",
            },
            "properties": {
                "customerClass": {
                    "keyName": "customerClass",  # what type of customer: 1-residential, 2-commercial, 4 -special
                    "dataValue": "1"
                }
            }
        }
        Url_put = 'https://api.genability.com/rest/v1/accounts'
        p = requests.put(Url_put, auth=(external_loadengine_app_id, external_loadengine_app_key), json=account_json)
        # GET
        Url_get = "https://api.genability.com/rest/v1/accounts/pid/" + self.providerAccountId
        g = requests.get(Url_get, auth=(external_loadengine_app_id, external_loadengine_app_key), json=account_json)
        return g.json()

    def get_utility(self):  # based on customer and zipcode, selects utility
        url = 'https://api.genability.com/rest/public/lses?postCode=' + str(self.zip) + \
              '&country=US&residentialServiceTypes=ELECTRICITY&sortOn=totalCustomers&sortOrder=DESC'
        g = requests.get(url, auth=(external_loadengine_app_id, external_loadengine_app_key))
        g = g.json()
        results = {}
        for i in g["results"]:
            results[i["name"]] = i['lseId']
        return results

    def set_utility(self, id):  # based on available utilities, pick and set the best one
        url = 'https://api.genability.com/rest/v1/accounts/pid/' + self.providerAccountId + '/properties'
        account_json = {
            "keyName": "lseId",
            "dataValue": str(id),  # 1228 is SCE ID
        }
        p = requests.put(url, auth=(external_loadengine_app_id, external_loadengine_app_key), json=account_json)
        return p.json()

    def get_tarrif(self):  # retrieves a list of tariffs from the set utility
        url_get = 'https://api.genability.com/rest/v1/accounts/pid/' + self.providerAccountId + '/tariffs?serviceTypes=ELECTRICITY'
        g = requests.get(url_get, auth=(external_loadengine_app_id, external_loadengine_app_key))
        g = g.json()  # 3250148 is TOU-A
        results = {}
        for i in g["results"]:
            results[i["tariffCode"]] = i['masterTariffId']
        return results

    def set_tarrif(self, inp):  # set one tarrif as the rate to use for the set utility
        self.masterTariffId = inp
        properties = {
            "keyName": "masterTariffId",
            "dataValue": self.masterTariffId,
        }
        url_put = 'https://api.genability.com/rest/v1/accounts/pid/' + self.providerAccountId + '/properties'
        p = requests.put(url_put, auth=(external_loadengine_app_id, external_loadengine_app_key), json=properties)
        return p.json()

    def import_rates(self):  # retrieves import rates for a given tariff
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
        r = r.json()
        import_rates = []
        output = r["results"][0]["items"]
        prev_time = ""
        for i in range(len(output)):
            curr_time = output[i]["fromDateTime"]
            if output[i]["chargeType"] == "CONSUMPTION_BASED" and curr_time != prev_time:
                import_rates += [output[i]["rateAmount"]]
                prev_time = curr_time

        return import_rates

    def export_rates(self):  # retrieves export rates for a given tarrif
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
        r = r.json()
        export_rates = []
        output = r["results"][0]["items"]
        prev_time = ""
        for i in range(len(output)):
            curr_time = output[i]["fromDateTime"]
            if output[i]["chargeType"] == "CONSUMPTION_BASED" and curr_time != prev_time:
                export_rates += [output[i]["rateAmount"]]
        return export_rates


def find_key(dict, value):  # used to find utility/tariff given a list of utilities and tariffs
    for key, val in dict.items():
        if str(val) == value:
            return key


def update_rates():
    all_rates = pd.read_csv("Rates/all_rates.csv")
    count = 1
    for filename in os.listdir("LoadProfiles"):
        try:
            file = Parser.fileParse("LoadProfiles/" + filename)
            city = file.getCity()
            z = file.getZipcode()
            print(z)

            location = city in all_rates["City"].values
            #if utility and tariff id have already been found in a previous run
            if location:
                row = all_rates.loc[all_rates['Zip'] == z]
                tariff_id = int(row["Tariff Id"])
                tariff = TariffEngine(str(city), str(count), str(z), "2018-01-01T00:00:00", "2019-01-01T00:00:00",
                                      tariff_id)
                utility_id = int(row["Utility Id"])
            else:
                # set up a tariff engine and get a list of utilities
                tariff = TariffEngine(str(city), str(count), str(z), "2018-01-01T00:00:00", "2019-01-01T00:00:00")
                tariff.create_account()
                utilities = tariff.get_utility()
                print(utilities)

                # input the \id for one of the utilities, setting that as the given utility for rates
                utility_id = raw_input("What Utility ID do you want to use?")
                while int(utility_id) not in utilities.values():
                    print()
                    print(utilities)
                    utility_id = raw_input("Not valid! What utility ID do you want to use?")
                print()
                print("Setting Utility...")
                print(tariff.set_utility(utility_id))
                utility_name = find_key(utilities, utility_id)

                # get a list of tariffs under set utility
                print()
                print("List of available tariffs:")
                tariff_list = tariff.get_tarrif()
                print(tariff_list)

                # input the masterTariffId for the preferred utility
                tariff_id = raw_input("What masterTariff ID do you want to use?")
                while int(tariff_id) not in tariff_list.values():
                    print()
                    print(tariff_list)
                    tariff_id = raw_input('Invalid! What masterTariff ID do you want to use?')
                print()
                print("Setting Tariff...")
                print(tariff.set_tarrif(tariff_id))
                tariff_name = find_key(tariff_list, tariff_id)

            # retrieve rates, and write rates file.
            import_rates = tariff.import_rates()
            export_rates = tariff.export_rates()
            print(import_rates)
            print(export_rates)

            directory = "Rates/" + city + ":" + utility_name + ":" + tariff_name + ".csv"
            if location == True: #if there is already a file of this name when updating rates
                os.remove(directory)

            with open(directory, 'w') as output_file:
                headers = ["Import Rates", "Export Rates"]
                writer = csv.DictWriter(output_file, headers)
                writer.writeheader()
                for i in range(len(import_rates)):
                    writer.writerow({"Import Rates": import_rates[i],
                                     "Export Rates": export_rates[i]})

            with open("Rates/all_rates.csv", 'w') as all_rates_file:
                headers = ["City", "Zip", "Utility", "Utility Id", "Tariff", "Tariff Id"]
                writer = csv.DictWriter(all_rates_file, headers)
                writer.writeheader()
                writer.writerow({"City": city, "Zip": z, "Utility": utility_name,
                                 "Utility Id": utility_id, "Tariff": tariff_name,
                                 "Tariff Id": tariff_id})



            print(str(count) + ".finished " + city + "!")
            count += 1
        except(KeyError, NameError, RuntimeError, IndexError, ValueError):
            print("exception")
            pass


update_rates()
