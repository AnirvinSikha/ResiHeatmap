import pandas

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
        return split[2]

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

def main():
    filename = "USA_CA_Los.Angeles.Intl.AP.722950_TMY3_HIGH.csv"
    run = fileParse(filename)
    print run.getTotalHour()[2]
    print run.convertHour(run.getTotalHour()[2])
    print run.convertDay(run.getTotalHour()[2])
    print run.convertMonth(run.getTotalHour()[2])
