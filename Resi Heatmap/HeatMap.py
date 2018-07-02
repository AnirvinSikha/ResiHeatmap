import plotly.plotly as py
import pandas as pd
import plotly.figure_factory as ff

#py.tools.set_credentials_file(username='ASikha', api_key='e9SmIFsps2jBwfKF0olK')
fips = ['06021', '06023', '06027',
        '06029', '06033', '06059',
        '06047', '06049', '06051',
        '06055', '06061']
values = range(len(fips))

fig = ff.create_choropleth(fips=fips, values=values)
py.iplot(fig, filename='choropleth of some cali counties - full usa scope')
fig = dict( data=data, layout=layout )
py.iplot( fig, validate=False, filename='d3-world-map' )
