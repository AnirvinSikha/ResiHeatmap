import json
import matplotlib as plt
import numpy as np
import requests
import os
import Parser



LA = "USA_CA_Los.Angeles.Intl.AP.722950_TMY3_HIGH.csv"
ratesEWeek = "RateEweek.csv"

LosAngeles = Parser.fileParse(LA)
rates = Parser.fileParse(ratesEWeek)

def run():
    output = []
    #output[0] = [0, 1,2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    week = True
    weekend = False
    weekCount = 0 #0 - Mon, 1 - Tues, 2 - Wed, 3 - Thurs, 4 - Fri. weekCount < 5
    weekendCount = 0 #0 - Sat, 1 - Sun weekendCount < 2
    totalHour = 1 #total hour goes from 0 - 8760 inclusive
    dailyHour = 0 #daily hour goes from 0 - 23 inclusive, resets everyday
    month = 1
    while totalHour <= 8760:
        print(rates.convertHour(LosAngeles.getTotalHour()[1]) == 0 )
        break

run()




