#!/home/tod/anaconda3/bin/python3
# coding: utf-8

# In[11]:


from __future__ import division
PATH="/home/tod/anaconda3/bin"
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import datetime
from datetime import date
import sys
import scipy

sys.stdout = open("out.txt","w")
sys.stderr = open("err.txt","w")

datafile = "/home/tod/data/lightning_sensor/lightning_sensor_data.csv"

title = 'Tucson Lightning Sensor Data'

# Values to normalize environmental data - done primarily to make the plot look better.
norm_pressure = 900

#Read .CSV file into a Pandas Data Structure below
df = pd.read_csv(datafile, parse_dates=True, infer_datetime_format='True', dayfirst=True, low_memory=False)
df = df.dropna()

#Fix Date Formats Below

def parse_dates(x):
    return datetime.datetime.strptime(x, '%H:%M:%S - %Y/%m/%d')
    
x = []
dist_filter = df['Distance'] > 0
timestamp = df['Time']
y1 = df['Humidity (%)']
y1b = df['Distance']
y1c = (df['Pressure (HP-900)'] - norm_pressure)*3
y1d = df['Temperature (deg F)']
y1e = df['Full Light Spectrum'] / 5.0
y1f = df['IR Spectrum'] / 5.0
y2 = df['Energy'] / 3.0

for t in timestamp:
    x.append(parse_dates(t))
  

today = date.today()
now = datetime.datetime.now()

def plot_data(period, date_lim):  
    output_file = ("/home/tod/data/lightning_sensor/lightning_sensor_data_plot-%s.pdf" % period)    
    d = scipy.zeros(len(y1f))
    with PdfPages(output_file) as pdf:
        try:
            fig, ax1 = plt.subplots(figsize=(12, 8))
            plt.xticks(rotation=45)
            ax2 = ax1.twinx()
            ax1.plot(x, y1, 'g-')
            ax1.plot(x, y1c, 'c-')
            ax1.plot(x, y1d, 'm-')
            ax1.plot(x, y1e, 'b:')
            ax1.fill_between(x,y1e,where=y1f>=d, interpolate=True, color='lightcyan')  
            ax1.plot(x, y1f, 'g:')
            ax1.fill_between(x,y1f,where=y1f>=d, interpolate=True, color='greenyellow')
            ax2.plot(x, y2, 'b-')
            ax1.plot(x, y1b, 'r*')

            ax1.set_xlabel('Time/Date')
            ax1.set_ylabel('Environmental Data and Lightning Distance', color='k')
            #ax1.set_xlim(left=datetime.date(2018, 7, 20))
            ax1.set_ylim(0,120)
            #ax1.set_xlim(left=date_lim, right=today)
            ax1.set_xlim(left=date_lim, right=now)
            ax2.set_ylabel('Lightning Energy', color='b')
            ax2.set_ylim(0,500000)
    
            #ax2.legend(loc='best')
            ax1.legend(loc='best')
            plt.xticks(rotation=45)

            plt.title('Lightning activity fused with Weather data for Tucson (85718)')
            #plt.show()
    
            fig.savefig('/home/tod/data/lightning_sensor/lightning_%s.png' % period)

            pdf.savefig(fig)  # or you can pass a Figure object to pdf.savefig
            plt.close()

            # We can also set the file's metadata via the PdfPages object:
            d = pdf.infodict()
            d['Title'] = title
            d['Author'] = u'W. Tod Newman'
            d['Subject'] = 'Fusion of Lightning sensor data with environmental sensor data'
            d['Keywords'] = 'lightning, tucson, humidity, pressure, temperature'
            d['CreationDate'] = datetime.datetime(2018, 7, 13)
            d['ModDate'] = datetime.datetime.today()
        except Exception as error:
            print( "<p>Error: %s</p>" % str(error) )

for period in ['day', 'week', 'month', 'year']:
    if period == 'day':
        #date_lim = date(today.year, today.month, today.day-1)
        date_lim = now - datetime.timedelta(days=2)
        plot_data(period, date_lim)
    if period == 'week':
        date_lim = now - datetime.timedelta(days=7)
        plot_data(period, date_lim)
    if period == 'month':
        date_lim = now - datetime.timedelta(days=20)
        plot_data(period, date_lim)
    if period == 'year':
        try:
            date_lim = today - datetime.timedelta(days=60)
            plot_data(period, date_lim)
        except:
            print("We must not have a full year's worth of data yet")
            print(period, date_lim)
  
        
