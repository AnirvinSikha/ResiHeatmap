import os

import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

import Parser
import Zipcode
from Outputs import NetLoad
import time

lat = []
lon = []
cities = []
values = []
count = 1
start_time = time.time()

for filename in os.listdir("LoadProfiles"):
    file = Parser.fileParse("LoadProfiles/" + filename)
    name = file.getCity()
    if filename.endswith(".csv"):

        z = file.getZipcode()
        cities += [name]
        latitude, longitude = Zipcode.find_lat(z), Zipcode.find_lon(z)
        lat += [latitude]
        lon += [longitude]
        output = NetLoad.run(file, latitude, longitude, file.getCity())
        values += [output]
    print str(count) + ".finished " + name + "!"
    count += 1
    print("--- %s seconds ---" % (time.time() - start_time))

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

    x, y = m(lon, lat)

    m.scatter(x, y, marker='o', c=values, s=values, cmap="YlOrRd")

    plt.colorbar(label=r'Annual Savings')
    plt.clim(min(values) - 200, max(values) + 50)


    plt.show()

def main():
    print cities
    print lat
    print lon
    print values
    heatmap_generation(lat, lon, values)


main()

