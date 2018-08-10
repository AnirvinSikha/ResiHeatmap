'''
Where all the calculations/consolidations occur. Results in a table that has,
Load/Consumption, Bill befor solar, import/export rates, solar production, basic
storage, Bill Solar/Storage, and ESS savings
'''
import PVWatts
import LoadProfile
import Parser
import Zipcode
import csv
import Dispatch
import os
import pandas as pd
import numpy as np
import time

#these lists store all the values for all tariffs to be run, put into a dataframe/csv at the end.
start_time = time.time()
total_utilities, total_cities, total_zips, total_tariffs, total_savings = [], [], [], [], []
bill_before_solar, bill_solar, bill_solar_storage = [],[],[]



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
    d = Dispatch.full_savings_dispatch(d, I)
    d['Net Load (Solar and Storage)'] = d["Load"] - d["basic storage"] - d["Solar"]
    d["Bill PV + ESS"] = np.where(d["Net Load (Solar and Storage)"] >= 0,
                                  d['Net Load (Solar and Storage)'] * d['Import Rate'] * I,
                                  d['Net Load (Solar and Storage)'] * d['Export Rate'] * I)
    d["ESS Savings"] = d["Bill Solar Only"] - d["Bill PV + ESS"]
    d["yearly ESS savings"] = d["ESS Savings"].sum()
    val = d.at[0, "yearly ESS savings"]
    bill_pre_solar = d["Bill Before Solar"].sum()
    bill_solar_only = d["Bill Solar Only"].sum()
    bill_solar_storage = d["Bill PV + ESS"].sum()
    d = d.to_csv(name)
    return (val, bill_pre_solar, bill_solar_only, bill_solar_storage)


# determines, for all the rates in a utility, the rate that gives the max ESS savings
def max_ESS_val(file, lat, lon, n, rates, util):
    global total_utilities,total_cities, total_savings, total_tariffs, total_zips,\
        bill_before_solar, bill_solar, bill_solar_storage

    city = file.getCity()
    z = file.getZipcode()
    ESS_savings = {}
    for i in rates: #for each rate for a given utility, performs ESS savings analysis and adds values to lists.
        directory = "Rates/" + util + "/" + i
        tariff_name = Parser.getTariffName(i)
        rate_file = pd.read_csv(directory)
        output = ESS_calc(file, lat, lon, n, rate_file)
        ESS_savings[i] = output[0]
        print("finished ESS savings for " + util + ": " + i)
        print("--- %s seconds ---" % (time.time() - start_time))

        total_utilities += [util]
        total_cities += [city]
        total_zips += [z]
        total_tariffs += [tariff_name]
        total_savings += [ESS_savings[i]]
        bill_before_solar += [output[1]]
        bill_solar += [output[2]]
        bill_solar_storage += [output[3]]
    print ESS_savings
    maximum = max(ESS_savings, key=ESS_savings.get)
    print (maximum, ESS_savings[maximum])


def utility_city(city): #given a city, returns the utility that corresponds with it
    util_city = pd.read_csv("Util:City/Util:City Database.csv")
    utility = util_city.loc[util_city["City"] == city, "Utility"]
    return utility


def utility_parse(inp): #given the file name of the rate, returns only the name of the utility
    inp = inp.tolist()[0]
    ret = ""
    while True:
        if inp[0] == " " or inp[0].isdigit():
            inp = inp[1:]
        else:
            break
    for i in inp:
        if i == "\n":
            return ret
        else:
            ret += i
    return inp

# determines what loads are to be run, and if all loads are to be run.
# returns a list of filenames of loads to be run.
def load_select():
    loads = []
    count = 1
    for filename in os.listdir("LoadProfiles/"):
        loads += [filename]
        print(str(count) + " " + filename)
        count += 1
    print
    inp = raw_input("Do you want to run all loads? (y/n)")
    while True:
        if inp == 'y':
            return loads
        elif inp == 'n':
            break
        else:
            inp = raw_input("Invalid input! Do you want to run all loads? (y/n)")

    for i in range(len(loads)):
        count = i + 1
        print (str(count) + ". " + loads[i])
    print
    inp = raw_input("What loads do you want to run. (Input as so: 1, 2, 4, 18)")
    indexes = find_int(inp)
    loads = [loads[int(x) - 1] for x in indexes]
    return loads

def find_int(s):
    ret = []
    for i in s.split(", "):
        if i.isdigit():
            ret += [i]
    return ret

#determines if all rates for all utilities are to be run
def all_tariffs():
    inp = raw_input("Do you want to run all tariffs? (y/n)")
    while True:
        if inp == 'y':
            return True
        elif inp == 'n':
            return False
        else:
            inp = raw_input("Invalid input! Do you want to run all tariffs? (y/n)")

#returns list of tariffs to be run
def tariff_select(rates):
    count = 1
    for rate in rates:
        print(str(count) + ". " + rate)
        count += 1
    print
    inp = raw_input("What rates do you want to run. (Input as so: 1, 2, 17, 25)")
    indexes = find_int(inp)
    rates = [rates[int(x) - 1] for x in indexes]
    return rates

def main():
    loads = load_select()
    all_tar = all_tariffs()
    for filename in loads: #runs utility calc for all load profiles
        try:
            print(filename)
            file = Parser.fileParse("LoadProfiles/" + filename)
            city = file.getCity()
            z = file.getZipcode()
            lat = Zipcode.find_lat(z)
            lon = Zipcode.find_lon(z)
            util = utility_city(city)
            util = utility_parse(util)
            rates = os.listdir("Rates/" + util)
            if all_tar == False:
                rates = tariff_select(rates)
            max_ESS_val(file, lat, lon, city, rates, util)
        except(KeyError, NameError, RuntimeError, IndexError, ValueError, OSError, pd.errors.ParserError):
            #raise
            pass

    d = pd.DataFrame({"Utility": total_utilities, "City": total_cities, "Zip": total_zips,
                      "Tariff": total_tariffs, "Bill Before Solar": bill_before_solar,
                      "Bill Solar Only": bill_solar, "Bill PV+ESS": bill_solar_storage,
                        "ESS Savings": total_savings},
        columns= ['Utility', "City", 'Zip', 'Tariff', "Bill Before Solar", "Bill Solar Only",
                  "Bill PV+ESS", 'ESS Savings'])
    d["Solar Savings"] = d["Bill Before Solar"] - d["Bill Solar Only"]
    d.to_csv("Outputs/finalCalculation.csv")

main()

