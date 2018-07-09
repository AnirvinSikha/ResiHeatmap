import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from datetime import datetime
from netCDF4 import date2index
from PIL import Image
from netCDF4 import Dataset


fig = plt.figure(figsize=(10, 8))
m = Basemap(projection='cass', resolution='h',
            lat_0=37.5, lon_0=-119,
            width=1E6, height=1.2E6)
m.drawcoastlines(color='black')
m.drawstates(color='black')
m.drawrivers(color='blue')
m.drawcounties(color='black')
plt.title('Hello Cali')
plt.show()
m.drawcounties()
