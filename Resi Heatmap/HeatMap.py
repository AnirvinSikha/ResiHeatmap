import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import pandas as pd
import importlib
importlib.import_module(NetLoad.py)


for filename in os.listdir("LoadProfiles"):
    if filename.endswith(".csv"):
        NetLoad
lat = [34, 32, 37]
lon = [-118, -117, -121]
values = [1255.444345, 1245.702862, 1141.722539]
#area = [1431, 1500, 1000]

def heatmap_generation(lat, lon, values):
    fig = plt.figure(figsize=(8, 8))
    m = Basemap(projection='lcc', resolution='h',
                lat_0=37.5, lon_0=-119,
                width=1E6, height=1.2E6)
    m.drawcoastlines(color='black')
    m.drawstates(color='black')
    m.drawcounties(color='black')
    plt.title('Hello Cali')

    x, y = m(lon, lat)

    m.scatter(x, y, marker='o', c=values, s=values, cmap="YlOrRd")

    plt.colorbar(label=r'Annual Savings')
    plt.clim(900, 1300)


    plt.show()
    m.drawcounties()
