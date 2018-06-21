import json
import matplotlib as plt
import numpy as np
import requests
import os
import Parser
import datetime



LA = "USA_CA_Los.Angeles.Intl.AP.722950_TMY3_HIGH.csv"
ratesEWeek = "RateEweek.csv"

LosAngeles = Parser.fileParse(LA)
rates = Parser.fileParse(ratesEWeek)

def run():
    output = []
    week = True
    weekend = False
    weekCount = 0 #0 - Mon, 1 - Tues, 2 - Wed, 3 - Thurs, 4 - Fri. weekCount < 5
    weekendCount = 0 #0 - Sat, 1 - Sun weekendCount < 2
    totalHour = 0 #total hour goes from 0 - 8759 inclusive
    dailyHour = 0 #daily hour goes from 0 - 23 inclusive, resets everyday
    month = 1
    while totalHour <= 8760:
        month_date = LosAngeles.convertMonth(LosAngeles.getTotalHour()[totalHour])
        day_date = LosAngeles.convertDay(LosAngeles.getTotalHour()[totalHour])
        date =  datetime.date(2013, month_date, day_date) #the date in 2013
        is_week = "week"
        if date.weekday() >= 5: #5,6 = Saturday, Sunday. 0-4 is Monday-Friday
            is_week = "weekend"

        r_Week = rates.getWeek() == is_week
        r_Month = rates.getMonth() == month_date
        #r_Hour = rates.getHour(totalHour//24) == (totalHour // 24)
        rate_value = rates.getHour(totalHour//24)[r_Week & r_Month]

        print rate_value
        print LosAngeles.getElectricity()[totalHour]
        print rate_value * LosAngeles.getElectricity()[totalHour]
        totalHour += 1

run()




