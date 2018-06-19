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

    def showHeaders(self):
        print(self.headers)





def main():
    filename = "USA_CA_Los.Angeles.Intl.AP.722950_TMY3_HIGH.csv"
    f = open(filename)
    run = Parser(f, filename)
    print run.showHeaders()
    print run.country
    print run.state
    print run.city



if __name__ == "__main__":
    main()
