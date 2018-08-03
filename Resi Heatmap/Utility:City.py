'''
A one time use file, to create the CSV that states what City has what Utility.
If you want to add a utility, you need to add a load where that city is.
If you add a utility re-run this file.
'''
import Genability
import Parser
import os
import pandas as pd
import time

def find_key(dict, value):  # used to find utility/tariff given a list of utilities and tariffs
    for key, val in dict.items():
        if str(val) == value or val == value:
            return key


def run():
    util_list = []
    util_id_list = []
    zips = []
    city_list = []
    count = 1
    start_time = time.time()

    for filename in os.listdir("LoadProfiles"):
            try:
                file = Parser.fileParse("LoadProfiles/" + filename)
                city = file.getCity()
                z = file.getZipcode()
                print(z)
                print(city)

                # set up a tariff engine and get a list of utilities
                tariff = Genability.TariffEngine(str(city), str(count), str(z), "2018-01-01T00:00:00", "2019-01-01T00:00:00")
                tariff.create_account()
                utilities = tariff.get_utility()
                print(utilities)

                if len(utilities) == 1:  # if there's only one utility, pick it
                    utility_id = list(utilities.values())[0]
                else:
                    utility_id = raw_input("What Utility ID do you want to use?")
                    while int(utility_id) not in utilities.values():
                        print()
                        print(utilities)
                        utility_id = raw_input("Not valid! What utility ID do you want to use?")
                utility_name = find_key(utilities, utility_id)

                util_list += [utility_name]
                util_id_list += [utility_id]
                zips += [z]
                city_list += [city]

                count += 1
                print count
                print("--- %s seconds ---" % (time.time() - start_time))
                print
            except(KeyError, NameError, RuntimeError, IndexError, ValueError):
                count += 1
                pass
    return util_list, util_id_list, zips, city_list


def to_csv(util_list, util_id_list, zips, city_list):
    d = {"Utility": util_list, "Utility ID": util_id_list,
         "Zip Code": zips, "City": city_list}
    df = pd.DataFrame(d)
    name = "Util:City/" + "Util:City Database" + ".csv"
    df.to_csv(name)


output = run()
to_csv(output[0], output[1], output[2], output[3])
