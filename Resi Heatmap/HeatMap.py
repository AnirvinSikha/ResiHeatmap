import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from netCDF4 import date2index
from PIL import Image
from netCDF4 import Dataset

lat = [34, 32, 37]
lon = [-118, -117, -121]
values = [1431, 1500, 1000]
#area = [1431, 1500, 1000]

# data = pd.read_csv("table.csv")
# lat = data["lat"].values
# lon = data["lon"].values
# values = data['values'].values
# area = data['area'].values

fig = plt.figure(figsize=(8, 8))
m = Basemap(projection='lcc', resolution='h',
            lat_0=37.5, lon_0=-119,
            width=1E6, height=1.2E6)
m.drawcoastlines(color='black')
m.drawstates(color='black')
m.drawrivers(color='blue')
m.drawcounties(color='black')
plt.title('Hello Cali')

x, y = m(lon, lat)

m.scatter(x, y, marker='o', c=values, s=values, cmap="Reds")

plt.colorbar(label=r'Annual Savings')
plt.clim(500, 1500)

# for a in [1000, 1500, 2000]:
#     plt.scatter([], [], c='k', alpha=0.5, s=a,
#                 label=str(a) + 'Annual Savings')
# plt.legend(scatterpoints=1, frameon=False,
#            labelspacing=3, loc='lower left');
plt.show()
m.drawcounties()
