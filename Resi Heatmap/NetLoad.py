'''
Where all the calculations/consolidations occur. Results in a table that has,
Load/Consumption, Bill befor solar, import/export rates, solar production, basic
storage, Bill Solar/Storage, and ESS savings
'''
import PVWatts
import LoadProfile
import Parser
import csv
import Dispatch
import os
import pandas as pd
import numpy as np
import time


start_time = time.time()
def ESS_calc(file, lat, lon, n, rates):  # inputs: a load profile, lat/lon coordinates, name of location
    I = 1  # Incrementation. 1 = hour .25= quarter hourly
     # create 5 lists to keep track of data.
    # 1) the date, aka 8760 values "YYYY-MM-DD hour:min:sec"
    # 2) consumption vals, aka the load profile. How much electricity used per hour
    # 3) bill before solar (electricity only) per hour
    # 4) solar - Output of PVWatts.py. Solar generation for 8760
    # 5) net load = load - solar
    output = LoadProfile.run(file, rates)
    consumption = output[1]
    before_solar = output[2]
    import_rates = output[3]
    export_rates = output[4]
    solar = PVWatts.run(lat, lon)

    net_load = []
    for i in range(len(consumption)):
        net_load += [consumption[i] - solar[i]]

    after_solar = []
    for i in range(len(net_load)):
        if net_load[i] >= 0:
            after_solar += [net_load[i] * import_rates[i] * I]
        else:
            after_solar += [net_load[i] * export_rates[i] * I]

    # writes all calculations to a csv file
    name = "Outputs/" + n + ".csv"
    with open(name, 'w') as output_file:
        headers = ["Date/Time", "Load", "Bill Before Solar", "Solar", "Net Load Solar Only",
                   "Bill Solar Only", "Import Rate", "Export Rate"]
        writer = csv.DictWriter(output_file, headers)

        writer.writeheader()
        for i in range(len(consumption)):
            writer.writerow({"Date/Time": i, "Load": consumption[i], "Bill Before Solar": before_solar[i],
                             "Solar": solar[i], "Net Load Solar Only": net_load[i], "Bill Solar Only": after_solar[i],
                             "Import Rate": import_rates[i], "Export Rate": export_rates[i]})

    # perform dispatch analysis through Dispatch.py. Gets basic storage and soc.
    # calculate bill of solar and storage
    # calculates the difference between bill pre-solar and bill solar/storage to get ESS savings
    d = pd.read_csv(name)
    d = Dispatch.full_basic_dispatch(d, I)
    d['Net Load (Solar and Storage)'] = d["Load"] - d["basic storage"] - d["Solar"]
    d["Bill PV + ESS"] = np.where(d["Net Load (Solar and Storage)"] >= 0,
                                  d['Net Load (Solar and Storage)'] * d['Import Rate'] * I,
                                  d['Net Load (Solar and Storage)'] * d['Export Rate'] * I)
    d["ESS Savings"] = d["Bill Solar Only"] - d["Bill PV + ESS"]
    d["yearly ESS savings"] = d["ESS Savings"].sum()
    val = d.at[0, "yearly ESS savings"]
    d = d.to_csv(name)
    return val

# determines, for all the rates in a utility, the rate that gives the max ESS savings
def max_ESS_val(file, lat, lon, n, rates, util):
    city = file.getCity()
    ESS_savings = {}
    for i in rates:
        directory = "Rates/" + util + "/" + i
        rate_file = pd.read_csv(directory)
        val = ESS_calc(file, lat, lon, n, rate_file)
        ESS_savings[i] = val
        print("finished ESS savings for " + i)
        print("--- %s seconds ---" % (time.time() - start_time))
    print ESS_savings
    maximum = max(ESS_savings, key=ESS_savings.get)
    print (maximum, ESS_savings[maximum])

def utility_city(city):
    util_city = pd.read_csv("Util:City/Util:City Database.csv")
    utility = np.where(util_city["City"] == city)
    return utility[0]

for filename in os.listdir("LoadProfiles"):
    file = Parser.fileParse("LoadProfiles/" + filename)
    city = file.getCity()
    util = utility_city(city)
    rates = os.listdir("Rates/" + util)
    max_ESS_val(file, 34, -118, "LA", rates, util)


