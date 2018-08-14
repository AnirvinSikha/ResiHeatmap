'''
All heatmap visualization code.
First you need to run get_dataframe which will parse through the
values to get the ess/solar values that you want to plot.

Then run get_all_values which does the zip --> fips conversion needed to plot the info

Then run plot and hawaii_plot which will plot the data in plotly
'''

import plotly
import plotly.plotly as py
import plotly.figure_factory as ff
import pandas as pd
import json
import time
import numpy as np
import colorlover as cl
from IPython.display import HTML

start_time = time.time()
total_utilities, total_cities, total_zips, total_tariffs, total_ESS_savings, total_solar_savings = [], [], [], [], [], []
bill_before_solar, bill_solar, bill_solar_storage = [],[],[]
ESS = False

#fileters through final calc vals and gets maximum savings to plot
def get_dataframe():
    global total_utilities, total_cities, total_zips, total_tariffs, total_ESS_savings, total_solar_savings
    global bill_before_solar, bill_solar, bill_solar_storage
    global ESS
    df = pd.read_csv("Outputs/finalCalculation.csv")
    utils = df['Utility'].tolist()
    utils = list(set(utils))
    inp = raw_input("Do you want to display Solar or ESS? (solar/ess)")
    while True:
        if inp.lower() == "solar":
            ESS = False
            break
        elif inp.lower() == "ess":
            ESS = True
            break
        else:
            inp = raw_input("Invalid input! Do you want to display Solar or ESS? (solar/ess)")

    for i in utils:
        filtered = df.loc[df["Utility"] == i]
        filtered["ESS + Solar Savings"] = filtered["ESS Savings"] + filtered['Solar Savings']
        if ESS:
            maximum = filtered.loc[filtered['ESS + Solar Savings'].idxmax()]
        else:
            maximum = filtered.loc[filtered['Solar Savings'].idxmax()]
        maximum = maximum.tolist()
        total_utilities += [maximum[1]]
        total_cities += [maximum[2]]
        total_zips += [maximum[3]]
        total_tariffs  += [maximum[4]]
        bill_before_solar   += [maximum[5]]
        bill_solar  += [maximum[6]]
        bill_solar_storage  += [maximum[7]]
        total_solar_savings  += [maximum[8]]
        total_ESS_savings  += [maximum[9]]
    d = pd.DataFrame({"Utility": total_utilities, "City": total_cities, "Zip": total_zips,
                      "Tariff": total_tariffs, "Bill Before Solar": bill_before_solar,
                      "Bill Solar Only": bill_solar, "Bill PV+ESS": bill_solar_storage,
                      "Solar Savings": total_solar_savings, "ESS Savings": total_ESS_savings},
        columns= ['Utility', "City", 'Zip', 'Tariff', "Bill Before Solar", "Bill Solar Only",
                  "Bill PV+ESS", 'Solar Savings', 'ESS Savings'])
    d.to_csv("Outputs/Solar ESS.csv")
    return d

def zip2fips(z): #zip to fip conversion
    if len(str(z)) <= 4:
            z = "0" + str(z)
    data = open("zip2fips/zip2fips.json")
    data = json.load(data)
    return data[str(z)]

def util_to_zip(util, solar, ESS): #utility to zip conversion
    util2zip = pd.read_csv("iouzipcodes2011.csv")
    utils = util2zip["utility_name"].tolist()
    zips = util2zip['zip'].tolist()
    fips = []
    solar_vals = []
    storage_vals = []
    u = []
    for i in range(len(utils)):
        if utils[i] in util:
            try:
                fips += [zip2fips(zips[i])]
            except(KeyError):
                pass
    fips = list(set(fips))
    for i in fips:
        u += [util]
        solar_vals += [solar]
        storage_vals += [ESS]
    return [u, fips, solar_vals, storage_vals]

def get_all_values(): #does the util to zip and zip to fip conversion.
    global total_solar_savings, total_ESS_savings
    df = pd.read_csv("Outputs/Solar ESS.csv")
    final_utils = []
    final_fips = []
    final_solar = []
    final_ESS = []
    utils = df['Utility'].tolist()
    utils = list(set(utils))
    print(len(utils))
    for i in range((len(utils))):
        output = util_to_zip(utils[i], total_solar_savings[i], total_ESS_savings[i])
        final_utils += output[0]
        final_fips += output[1]
        final_solar += output[2]
        final_ESS += output[3]
        print("--- %s seconds ---" % (time.time() - start_time))
        print ('finished ' + str(utils[i]))

    d = pd.DataFrame({'Utility': final_utils, 'FIPS': final_fips, 'Solar': final_solar, 'ESS': final_ESS},
                     columns= ['Utility', 'FIPS', 'Solar', 'ESS'])
    d.to_csv("Outputs/Heatmap.csv")

def plot(): #plots all values on the heatmap
    global total_utilities, total_cities, total_zips, total_tariffs, total_ESS_savings, total_solar_savings
    global bill_before_solar, bill_solar, bill_solar_storage
    global ESS
    ESS = True

    username = "ASikha"
    api_key = "t4qWFWDpSSYx2yBrgnKT"
    plotly.tools.set_credentials_file(username=username, api_key=api_key)
    d = pd.read_csv("Outputs/Heatmap.csv")

    utils = d["Utility"]
    fips = d["FIPS"]
    solar = [round(x) for x in d["Solar"]]
    ESS_vals = d["ESS"]

    ryg = cl.scales['11']['div']['RdYlGn']
    ryg.reverse()


    if ESS == False:
        endpts = list(np.linspace(min(solar), max(solar), len(ryg) - 1))
        fig = ff.create_choropleth(fips = fips, values = solar, binning_endpoints=endpts,
                           colorscale = ryg, legend_title='Solar Savings', title='Solar Savings',
                           state_outline={'color': 'rgb(15, 15, 55)', 'width': 0.5}, round_legend_values=True)
    else:
        endpts = list(np.linspace(min(ESS_vals), max(ESS_vals), len(ryg) - 1))
        fig = ff.create_choropleth(fips = fips, values = ESS_vals, binning_endpoints=endpts,
                           colorscale = ryg, legend_title='ESS', title='ESS',
                           state_outline={'color': 'rgb(15, 15, 55)', 'width': 0.5}, round_legend_values=True)

    py.plot(fig, filename='Heatmap')

def hawaii_plot(): #only used for hawaii plot
    global ESS

    username = "ASikha"
    api_key = "t4qWFWDpSSYx2yBrgnKT"
    plotly.tools.set_credentials_file(username=username, api_key=api_key)
    d = pd.read_csv("Outputs/Heatmap.csv")

    FIPS = d["FIPS"].tolist()
    for i in FIPS:
        if i == 15003 or i == 15009:
            filtered = d.loc[d["FIPS"] == i]
            utils = filtered["Utility"]
            fips = filtered["FIPS"]
            solar = [round(x) for x in filtered["Solar"]]
            ESS_vals = filtered["ESS"]
    fips = fips.tolist()
    solar = solar
    ESS_vals = ESS_vals.tolist()
    fips += [15001]
    solar += [1200]
    ESS_vals += [532.3645541]

    ryg = cl.scales['11']['div']['RdYlGn']

    if ESS == False:
        fig = ff.create_choropleth(fips = fips, values = solar,
                           colorscale = ryg, legend_title='Solar Savings', title='Solar Savings',
                           state_outline={'color': 'rgb(15, 15, 55)', 'width': 0.5}, round_legend_values=True,
                                   scope = ['Hawaii'], show_state_data=True,)
    else:
        fig = ff.create_choropleth(fips = fips, values = ESS_vals,
                           colorscale = ryg, legend_title='ESS', title='ESS',
                           state_outline={'color': 'rgb(15, 15, 55)', 'width': 0.5}, round_legend_values=True,
                                   scope = ['Hawaii'], show_state_data=True,)

    py.plot(fig, filename='Heatmap')
df = get_dataframe()
get_all_values()
plot()
hawaii_plot()


