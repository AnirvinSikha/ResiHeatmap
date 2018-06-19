import csv
import sqlite3
import glob
import os

class Parser:

    def __init__(self, f, filename):
        self.f = f
        self.filename = filename
        self.reader = csv.reader(f)
        self.headers = self.reader.next()

        split = filename.split("_")
        self.country = split[0]
        self.state = split[1]
        self.city = split[2]

        self.columns = {}
        for h in self.headers:
            self.columns[h] = []
        for row in self.reader:
            for h, v in zip(self.headers, row):
                self.columns[h].append(v)

    def getElectricity(self):
        return self.columns["Electricity:Facility [kW](Hourly)"]

def fileParse(filename):
    f = open(filename)
    parsedCSV = Parser(f, filename)
    return parsedCSV

def main():
    filename = "USA_CA_Los.Angeles.Intl.AP.722950_TMY3_HIGH.csv"
    run = fileParse(filename)
    print run.getElectricity()
