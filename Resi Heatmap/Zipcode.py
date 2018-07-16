import urllib
import string
import pandas as pd

df = pd.read_csv("ZipcodeDatabase.csv")

def find_zipcode(city):
    locations = {}
    index = 0
    for i in df["City"]:
        if i in city.upper():
            locations[i] = df.at[index, "Zipcode"]
        index += 1
    maximum = max(locations.keys())
    return locations.get(maximum)

def find_lat(zip):
    row = df.loc[df["Zipcode"] == zip]
    return row["Lat"]

def find_lon(zip):
    row = df.loc[df["Zipcode"] == zip]
    return row["Long"]

def main():
    print find_zipcode("Los Angeles")


