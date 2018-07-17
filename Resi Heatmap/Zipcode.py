import urllib
import string
import pandas as pd

df = pd.read_csv("ZipcodeDatabase.csv")


def find_zipcode(city, state):
    locations = {}
    index = 0
    for i in df["City"]:
        if i in city.upper() and df.at[index, "State"] == state.upper():
            locations[i] = df.at[index, "Zipcode"]
        index += 1
    maximum = max(locations.keys())
    return locations.get(maximum)


def find_lat(zip):
    row = df.loc[df["Zipcode"] == zip]
    return row["Lat"].item()


def find_lon(zip):
    row = df.loc[df["Zipcode"] == zip]
    return row["Long"].item()


def main():
    z = find_zipcode("Los Angeles")
    print find_lon(z)
    print find_lat(z)
