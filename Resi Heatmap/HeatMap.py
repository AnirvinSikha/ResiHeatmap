'''
Goes through all files in Load Profiles.
Runs NedLoad.py calc on all load profile files.
For all outputs, plots the value on a generated heat map
'''

import os
import time

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib import colors
import numpy as np
import NetLoad
import Parser
import Zipcode

lat = []
lon = []
cities = []
values = []
count = 1
start_time = time.time()

# lat = [33.91, 37.8, 32.86, 36.67, 38.29, 33.48, 40.85, 37.41, 34.78, 37.36, 33.29, 33.19, 38.45, 38.57, 38.92, 32.8, 39.3, 34.42, 34.01, 34.86, 32.8, 39.12, 34.2, 34.25, 36.37, 41.76, 41.43, 36.05, 34.92, 33.83, 33.89, 39.12, 33.94, 32.8, 36.82, 37.62, 33.16, 33.77, 35.25, 36.28, 40.13, 40.64, 37.87, 38.26, 34.64, 34.95, 33.98, 37.96, 33.94, 37.33, 33.71, 34.16, 37.77, 41.75, 37.65, 35.27, 34.63, 38.57, 37.82, 34.27, 34.2, 37.77, 36.57, 32.8, 34.01, 35.65, 34.57, 37.41]
# lon = [-118.36, -122.31, -115.65, -121.62, -122.28, -116.1, -124.05, -122.05, -114.59, -118.4, -117.3, -117.23, -122.59, -121.52, -119.96, -117.13, -120.31, -119.7, -118.19, -116.81, -117.13, -121.39, -118.47, -119.16, -119.18, -122.39, -120.53, -119.14, -117.94, -116.54, -117.93, -123.28, -117.39, -117.13, -119.76, -122.1, -117.34, -118.18, -119.0, -119.84, -122.43, -122.5, -122.04, -121.93, -118.21, -120.5, -117.65, -121.3, -117.39, -121.89, -117.9, -118.21, -121.75, -124.2, -120.99, -120.73, -120.46, -121.52, -122.16, -116.1, -118.98, -122.41, -121.83, -117.13, -118.46, -120.69, -118.11, -120.5]
# values = [608.91616970314442, 450.50585815504525, 285.67739299487351, 497.92996345769217, 424.24673517891728, 318.29099858432801, 389.43054880155381, 450.63921942696436, 318.76760591598315, 610.32793355373508, 612.00743811258133, 425.2979347183396, 562.94707465164277, 582.9065627355368, 640.65791834562401, 567.71951923285906, 509.6351443072121, 611.62796366605244, 449.50463051207828, 623.65472041422117, 469.3857115907017, 570.90210367575321, 509.28115806565904, 551.26721435112108, 542.16567277696402, 586.49772930240022, 545.41559515555593, 525.99039791548364, 335.95074129470783, 621.61504864753181, 419.81852963288753, 591.17815419190003, 633.36173360267185, 492.69117623674123, 450.09035409881733, 627.34778659197104, 606.69691988304112, 580.79443161933318, 519.95764414575342, 476.36709266410992, 466.74630006891044, 570.87487955985, 536.5081413419914, 468.52594838507696, 482.54155353720085, 585.94233811849847, 549.8744035651963, 314.72954964868597, 441.50816946498747, 646.04856733074894, 571.04952975676918, 441.25012011612893, 389.19672672731991, 570.52600894412717, 496.02138222029117, 485.91499470757617, 570.11096278799391, 576.113223333527, 417.75908179610764, 497.44968524193541, 450.89347193747125, 498.35476219162808, 643.84556227677035, 613.29490741290897, 495.57706328937485, 446.00262053265493, 563.61946301975706]


for filename in os.listdir("LoadProfiles"):
    try:
        file = Parser.fileParse("LoadProfiles/" + filename)
        name = file.getCity()
        if filename.endswith(".csv"):

            z = file.getZipcode()
            cities += [name]
            latitude, longitude = Zipcode.find_lat(z), Zipcode.find_lon(z)
            lat += [latitude]
            lon += [longitude]
            output = NetLoad.max_ESS_val(file, latitude, longitude, file.getCity())
            values += [output]
        print str(count) + ".finished " + name + "!"
        count += 1
        print("--- %s seconds ---" % (time.time() - start_time))
    except(KeyError, NameError, RuntimeError, IndexError, ValueError):
        pass

def heatmap_generation(lat, lon, values):
    fig = plt.figure(figsize=(8, 8))
    #US Code:
    # m = Basemap(projection='lcc', resolution='h',
    #             llcrnrlon=-119,llcrnrlat=22,urcrnrlon=-64,urcrnrlat=49,
    #             lat_1=33,lat_2=45,lon_0=-95)

    #CA Code:
    m = Basemap(projection='lcc', resolution='h',
                lat_0=37.5, lon_0=-119,
                width=1E6, height=1.2E6)

    m.drawcoastlines(color='black')
    m.drawstates(color='black')
    m.drawcounties(color='black')
    plt.title('Hello Cali')

    #m.scatter(lon, lat, latlon = True, marker='o', s=values, cmap="YlOrRd")
    #plt.colorbar(label=r'Annual Savings')
    #plt.clim(min(values), max(values))


    plt.show()

def main():
    #print cities
    print lat
    print lon
    print values
    heatmap_generation(lat, lon, values)

main()

