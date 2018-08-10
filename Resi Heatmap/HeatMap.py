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

#fileters through final calc vals and gets maximum savings to plot
def get_dataframe():
    global total_utilities, total_cities, total_zips, total_tariffs, total_ESS_savings, total_solar_savings
    global bill_before_solar, bill_solar, bill_solar_storage

    df = pd.read_csv("Outputs/finalCalculation.csv")
    ret = pd.DataFrame()
    utils = df['Utility'].tolist()
    utils = list(set(utils))

    for i in utils:
        filtered = df.loc[df["Utility"] == i]
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
    return d

def zip2fips(z):
    if len(str(z)) <= 4:
            z = "0" + str(z)
    data = open("zip2fips/zip2fips.json")
    data = json.load(data)
    return data[str(z)]

def util_to_zip(util, solar, ESS):
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

def get_all_values():
    global total_solar_savings, total_ESS_savings

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

def plot():
    global total_utilities, total_cities, total_zips, total_tariffs, total_ESS_savings, total_solar_savings
    global bill_before_solar, bill_solar, bill_solar_storage

    username = "ASikha"
    api_key = "t4qWFWDpSSYx2yBrgnKT"
    plotly.tools.set_credentials_file(username=username, api_key=api_key)
    d = pd.read_csv("Outputs/Heatmap.csv")

    utils = d["Utility"]
    fips = d["FIPS"]
    solar = d["Solar"]
    ESS = d["ESS"]

    #text = "Utility:" + utils.tolist() + '<br>' + "Solar Savings: " + solar.tolist() + '<br>' + "ESS Savings: " + ESS.tolist()
    ryg = cl.scales['11']['div']['RdYlGn']
    ryg.reverse()
    scl = [[0.0, 'rgb(242,240,247)'],[0.2, 'rgb(218,218,235)'],[0.4, 'rgb(188,189,220)'],\
            [0.6, 'rgb(158,154,200)'],[0.8, 'rgb(117,107,177)'],[1.0, 'rgb(84,39,143)']]
    endpts = list(np.linspace(min(solar), max(solar), len(ryg) - 1))


    fig = ff.create_choropleth(fips = fips, values = solar, binning_endpoints=endpts,
    colorscale = ryg, legend_title='Solar Savings',)

    py.plot(fig, filename='Heatmap')


#df = get_dataframe()
#get_all_values()
plot()


