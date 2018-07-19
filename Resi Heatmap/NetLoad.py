import PVWatts
import LoadProfile
import Parser
import csv
import Dispatch
import Zipcode
import pandas as pd
import numpy as np

# userhome = os.path.expanduser('~')
# csvfile = r'/Desktop/USA_CA_San.Jose.Intl.AP.724945_TMY3_HIGH' + '.csv'
# os.makedirs(userhome)
# load_file = Parser.fileParse(open(csvfile, "r"))

ratesEWeek = "RateEweek.csv"

rates = Parser.fileParse(ratesEWeek)


def run(file, lat, lon, n):
    I = 1  # hour
    output = LoadProfile.run(file, rates)
    dates = output[0]
    consumption = output[1]
    before_solar = output[2]
    solar = PVWatts.run(lat, lon)
    net_load = []
    for i in range(len(consumption)):
        net_load += [consumption[i] - solar[i]]

    import_rates = output[3]
    export_rates = []
    for i in range(len(import_rates)):
        export_rates += [import_rates[i] - .03]

    after_solar = []
    for i in range(len(net_load)):
        if net_load[i] >= 0:
            after_solar += [net_load[i] * import_rates[i] * I]
        else:
            after_solar += [net_load[i] * export_rates[i] * I]

    name = "Outputs/" + n + ".csv"
    with open(name, 'w') as output_file:
        headers = ["Date/Time", "Load", "Bill Before Solar", "Solar", "Net Load Solar Only",
                   "Bill Solar Only", "Import Rate", "Export Rate"]
        writer = csv.DictWriter(output_file, headers)

        writer.writeheader()
        for i in range(len(dates)):
            writer.writerow({"Date/Time": dates[i], "Load": consumption[i], "Bill Before Solar": before_solar[i],
                             "Solar": solar[i], "Net Load Solar Only": net_load[i], "Bill Solar Only": after_solar[i],
                             "Import Rate": import_rates[i], "Export Rate": export_rates[i]})

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
