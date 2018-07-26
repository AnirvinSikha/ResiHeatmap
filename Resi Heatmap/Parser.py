'''
Parses LoadProfile files and rate files
'''
import pandas
import Zipcode

class Parser:

    def __init__(self, f, filename):
        self.f = pandas.read_csv(f)
        self.filename = filename
        #self.reader = csv.reader(f)
        #self.headers = self.reader.next()

        self.columns = {}
        #for h in self.headers:
        #    self.columns[h] = []
        #for row in self.reader:
        #    for h, v in zip(self.headers, row):
        #        self.columns[h].append(v)

    def getCountry(self):
        split = self.filename.split("_")
        return split[0]

    def getState(self):
        split = self.filename.split("_")
        return split[1]

    def getCity(self):
        split = self.filename.split("_")
        split = split[2].split(".7")
        ret = ""
        for i in split[0]:
            if i == ".":
                ret += " "
            else:
                ret += i
        return ret

    def getZipcode(self):
        city = self.getCity()
        state = self.getState()
        return Zipcode.find_zipcode(city, state)

    def getLat(self):
        zip = self.getZipcode()
        return Zipcode.find_lat(zip)

    def getLon(self):
        zip = self.getZipcode()
        return Zipcode.find_lon(zip)

    def getElectricity(self):
        return self.f["Electricity:Facility [kW](Hourly)"]

    def getTotalHour(self):
        return self.f["Date/Time"]

    def convertHour(self, str): #takes in "01/01 01:00:00" and returns int of 1 (hour)
        store = str.split()[1]
        return int(store.split(":")[0])

    def convertDay(self, str):
        store = str.split()[0]
        return int(store.split("/")[1])

    def convertMonth(self, str): #takes in "01/01 01:00:00" and returns int of 01 (month)
        return int(str.split("/")[0])

    def getWeek(self):
        return self.f["week/weekend"]

    def getMonth(self):
        return self.f["month"]

    def getHour(self, h):
        h = int(h)
        return self.f[str(h)]

def fileParse(filename):
    f = open(filename)
    parsedCSV = Parser(f, filename)
    return parsedCSV

# def main():
#     filename = "LoadProfiles/USA_CA_Los.Angeles.Intl.AP.722950_TMY3_HIGH.csv"
#     run = fileParse(filename)
#     print "here"
#     print run.getLon()

