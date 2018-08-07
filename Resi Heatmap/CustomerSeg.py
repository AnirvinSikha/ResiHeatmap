from SavingsPerf import *

import os
import matplotlib.pyplot as plt
import seaborn as sns


# Battery spec
capacity_list = [9.3, 9.3*2]
power_rate = 5  # kW
I = 1
e = 0.88  # battery efficiency round trip


# Open profiles
data = pd.read_excel('C:\Users\ctouati\PyCharmProject\EquinoxStorage-/Customer Loads profiles.xlsx', sheetname='Profile')
data['date'] = pd.to_datetime(data['date'], format='%m/%d/%Y %H:%M')
customers = data.iloc[:,6:11].columns

# open rates table
rates = pd.read_excel('C:\Users\ctouati\PyCharmProject\EquinoxStorage-/Rates/Rates.xlsx')
ratelist = rates['Rates']


# Add rates in d

for ratename in ratelist:
    print(ratename)
    rates_filtered = rates[rates.Rates == ratename]
    for i in data.index:
        data.loc[i, ratename] = float(rates_filtered[ data.loc[i,'hour']]/100) # rates are in cents in the excel
        if rates_filtered.export.values == 'yes':
            data.loc[i, str(ratename) + 'export'] = data.loc[i, ratename] - 0.02
        else:
            data.loc[i, str(ratename) + 'export'] = 0

total = pd.DataFrame([]) # col: rate, customer, season, savings for each aglo, perf
k=0
first = True
# Add criterias and get the dispatch for all customer and rates
for capacity in capacity_list:
    for month in [1,6]:
        print('month ' + str(month))
        d = data[data.month == month]
        for ratename in ratelist:
            print(ratename)
            d.loc[:,'rate'] = d.loc[:,str(ratename)]
            d.loc[:,'rate_export'] = d.loc[:,str(ratename)+'export']
            #create a column with criterias
            add_chargesolar(d, ratename, e, I)  # does not dep on customer
            add_grid(d, ratename, e, I)  # does not dep on customer
            for customer in customers:
                print(customer) # customer = customers[1]
                # use temporary variable d.load
                d.loc[:,'load'] = d.loc[:,str(customer)]
                add_highsolar(d,customer,I)
                #get the dispatch for all algorithm, columns name deps on customer, rate, algo
                full_dispatch( d,'all', customer, ratename, e, I, capacity)
                total.loc[k, 'capacity'] = capacity
                total.loc[k, 'customer'] = customer
                total.loc[k, 'rate'] = ratename
                total.loc[k, 'month'] = month
                total.loc[k, 'basic savings'] = savings(d, str(customer) + str(ratename) + 'basic',I)
                total.loc[k, 'improved savings'] = savings(d, str(customer) + str(ratename) + 'improved',I)
                total.loc[k, 'best savings'] = savings(d, str(customer) + str(ratename) + 'best',I)
                total.loc[k, 'optimal savings'] = savings(d, str(customer) + str(ratename) + 'optimal',I)
                k += 1
            print(total)
        total['perf basic'] = total['basic savings'] / total['optimal savings']
        total['perf improved'] = total['improved savings'] / total['optimal savings']
        total['perf best'] = total['best savings'] / total['optimal savings']
        if first == True:
            dall = d
            first = False
        else:
            dall = dall.append(d)


# add rates parameters
for k in total.index:
    print(k)
    total.loc[k, 'tou ratio'] = float(rates[rates.Rates == total.loc[k, 'rate'] ].loc[:,'TOU ratio'])
    total.loc[k, 'peakperiod'] = float(rates[rates.Rates == total.loc[k, 'rate']].loc[:, 'peakperiod'])
    if total.loc[k, 'month'] == 1:
        total.loc[k,'solar/load'] = 0.6
    else:
        total.loc[k, 'solar/load'] = 1.22
    for h in range(0,24):
        total.loc[k,h] = float(rates[rates.Rates == total.loc[k, 'rate'] ].loc[:,h])

d.to_csv('custonerseg_cap.csv')
total.to_csv('total_cap.csv')

total = pd.read_csv('total_cap.csv')
d = pd.read_csv('custonerseg_cap.csv')

# Calculate savings and perf
# Sum up table
w = total[total.month==1]
s = total[total.month==6]


# Graph for WINTER
# on average, optimal savings are the same whatever the customer
s.boxplot( column = ['basic savings' , 'improved savings', 'best savings','optimal savings'], by='customer')
s.boxplot( column = ['perf basic' , 'perf improved', 'perf best'], by='customer')

# average savings for each PV/cap couples
Avr = total[(total.rate!='G') & (total.rate!='J')].groupby(['month','capacity']).agg('mean')
Avr.iloc[:,4:5]


# comapre optimal
cap1=9.3
wpivot= w[w.capacity==cap1].pivot(index='customer', columns='rate', values='optimal savings')
sns.heatmap(wpivot, annot=True).set_title('Optimal savings winter cap=9.3')
spivot= s[s.capacity==cap1].pivot(index='customer', columns='rate', values='optimal savings')
sns.heatmap(spivot, annot=True).set_title('Optimal savings summer cap=9.3')

cap2=18.6
wpivot= w[w.capacity==cap2].pivot(index='customer', columns='rate', values='optimal savings')
sns.heatmap(wpivot, annot=True).set_title('Optimal savings winter cap=18.6')
plt.show()
spivot= s[s.capacity==cap2].pivot(index='customer', columns='rate', values='optimal savings')
sns.heatmap(spivot, annot=True).set_title('Optimal savings summer cap=18.6')
plt.show()

# comapre ruled aglo
cap1=9.3
wpivot= w[w.capacity==cap1].pivot(index='customer', columns='rate', values='best savings')
sns.heatmap(wpivot, annot=True).set_title('Ruled savings winter cap=9.3')
plt.show()
spivot= s[s.capacity==cap1].pivot(index='customer', columns='rate', values='best savings')
sns.heatmap(spivot, annot=True).set_title('Ruled savings summer cap=9.3')

cap2=18.6
wpivot= w[w.capacity==cap2].pivot(index='customer', columns='rate', values='best savings')
sns.heatmap(wpivot, annot=True).set_title('Ruled savings winter cap=18.6')

spivot= s[s.capacity==cap2].pivot(index='customer', columns='rate', values='best savings')
sns.heatmap(spivot, annot=True).set_title('Ruled savings summer cap=18.6')

# compare performances

wpivot= w.pivot(index='customer', columns='rate', values='perf best')
sns.heatmap(wpivot, annot=True, vmin=0.5, vmax=1).set_title('Performance for ruled algorithm winter')

spivot= s.pivot(index='customer', columns='rate', values='perf best')
sns.heatmap(spivot, annot=True, vmin=0.5, vmax=1).set_title('Performance for ruled algorithm summer')

wpivot= w.pivot(index='customer', columns='rate', values='perf basic')
sns.heatmap(wpivot, annot=True, vmin=0.5, vmax=1).set_title('Performance for basic algorithm winter')

spivot= s.pivot(index='customer', columns='rate', values='perf basic')
sns.heatmap(spivot, annot=True, vmin=0.5, vmax=1).set_title('Performance for basic algorithm summer')


delta = spivot - s.pivot(index='customer', columns='rate', values='perf basic')
sns.heatmap(delta, annot=True, vmin=-0.1, vmax=1).set_title('comparison summer ruled - basic')

delta = wpivot - w.pivot(index='customer', columns='rate', values='perf basic')
sns.heatmap(delta, annot=True, vmin=-0.1, vmax=1).set_title('comparison winter ruled - basic')

deltaseason = wpivot - spivot
sns.heatmap(deltaseason, annot=True).set_title('comparison w - s best -')


# correlation: How important is the rate depend on the hour

correlation = total.corr(method='pearson').iloc[1:8,8:12]
sns.heatmap(correlation, annot= True, cbar_kws={"orientation": "horizontal"})


correlation = w.corr(method='pearson').iloc[7:,0:4]
sns.heatmap(correlation,)

for customer in customers:
    print(customer)
    print(w[w.customer ==  customer].corr(method='pearson').iloc[:6,7])



# Plot day use
plt.rcParams.update({'font.size': 10})
rate ='A'
customer='EvePeakers '
fig_alldates = d[['date', 'EvePeakers ', 'solar', 'EvePeakers '+str(rate)+'best storage', rate]]
fig = fig_alldates[ fig_alldates.date >'2017-06-24 00:00:00']
#fig = fig_alldates[ fig_alldates.date <'2017-01-4 00:00:00']
test = fig
test['charge'] = -test['EvePeakers '+str(rate)+'best storage']*(test['EvePeakers '+str(rate)+'best storage']<0)
test['discharge'] = test['EvePeakers '+str(rate)+'best storage']*(test['EvePeakers '+str(rate)+'best storage']>0)
test['netload'] = test['EvePeakers '] - test.solar + test.charge - test.discharge
test = test[['date', 'EvePeakers ','solar','discharge','charge','netload',rate]]

ax1=test[['date', 'EvePeakers ','solar','discharge','charge','netload']].plot.area(x='date', stacked=False, legend= True, colors=['skyblue', 'orange', 'green', 'red', 'mediumpurple'], alpha=0.3, linewidth=1)
plt.ylabel('kW')
plt.ylim(-4, 5)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax2=test.plot(x='date', y=rate, linestyle='dashed', secondary_y=True, color='grey', title = 'EvePeakers Rate '+ str(rate), ax=ax1, legend= False, linewidth=1)
title_font = {'fontname':'Arial', 'size':'12', 'color':'black', 'weight':'normal',
              'verticalalignment':'bottom'}
#plt.legend(loc=9, bbox_to_anchor=(0.5, -0.1), ncol=5)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.set_yticklabels([])
ax2.set_yticks([])
plt.title('EvePeakers Rate ' + str(rate))
#plt.ylabel('Rate $/kWh')
plt.legend(rate)
plt.ylim(-1.5, 0.5)
plt.show()




# option2
plt.plot( 'date', 'EvePeakers ', data=fig, color='skyblue')
plt.fill_between( 'date', 'solar', data=fig, color='yellow', alpha=0.3)
plt.plot( 'date', 'EvePeakers Abest storage', data=fig, color='red')
plt.plot( 'date', 'A',  secondary_y=True, data=fig, color='grey', linestyle='dashed')
