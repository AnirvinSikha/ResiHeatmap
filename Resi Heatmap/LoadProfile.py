import Parser
import datetime



LA = "USA_CA_Los.Angeles.Intl.AP.722950_TMY3_HIGH.csv"
ratesEWeek = "RateEweek.csv"

LosAngeles = Parser.fileParse(LA)
rates = Parser.fileParse(ratesEWeek)



def run(load, rates):
    date_time = load.getTotalHour()
    consumption = []
    before_solar = []
    import_rates = []


    totalHour = 0 #total hour goes from 0 - 8759 inclusive
    while totalHour < 8760:
        consumption += [load.getElectricity()[totalHour]]

        month_date = load.convertMonth(load.getTotalHour()[totalHour])
        day_date = load.convertDay(load.getTotalHour()[totalHour])
        date =  datetime.date(2013, month_date, day_date) #the date in 2013
        is_week = "week"
        if date.weekday() >= 5: #5,6 = Saturday, Sunday. 0-4 is Monday-Friday
            is_week = "weekend"

        r_Week = rates.getWeek() == is_week
        r_Month = rates.getMonth() == month_date
        hour = totalHour % 24

        rate_value = rates.getHour(hour)[r_Week & r_Month]
        import_rates += [rate_value]
        #print "rate val:" + str(rate_value)
        #print "LA Load prof:" + str(load.getElectricity()[totalHour])
        #print rate_value * load.getElectricity()[totalHour]
        #print "date: " + str(date)
        #print "totalHour:" + str(totalHour)
        #print " "

        before_solar += [rate_value * load.getElectricity()[totalHour]]
        totalHour += 1
    return (date_time, consumption, before_solar, import_rates)






