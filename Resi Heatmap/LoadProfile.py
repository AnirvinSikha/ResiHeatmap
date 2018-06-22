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
    totalHour = 0 #total hour goes from 0 - 8759 inclusive
    while totalHour < 8760:
        month_date = LosAngeles.convertMonth(LosAngeles.getTotalHour()[totalHour])
        day_date = LosAngeles.convertDay(LosAngeles.getTotalHour()[totalHour])
        date =  datetime.date(2013, month_date, day_date) #the date in 2013
        is_week = "week"
        if date.weekday() >= 5: #5,6 = Saturday, Sunday. 0-4 is Monday-Friday
            is_week = "weekend"

        r_Week = rates.getWeek() == is_week
        r_Month = rates.getMonth() == month_date
        hour = totalHour % 24
        #r_Hour = rates.getHour(totalHour//24) == (totalHour // 24
        #if totalHour == 576:
        #    rate_value = rates.getHour(0)[r_Week & r_Month]
        #else:
        if totalHour == 575:
            print "hello, right over here!"
        rate_value = rates.getHour(hour)[r_Week & r_Month]

        print "rate val:" + str(rate_value)
        print "LA Load prof:" + str(LosAngeles.getElectricity()[totalHour])
        print rate_value * LosAngeles.getElectricity()[totalHour]
        print "date: " + str(date)
        print "totalHour:" + str(totalHour)
        print " "

        totalHour += 1

run()




