
# coding: utf-8

# In[11]:


from __future__ import division
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import datetime
import sys
import scipy

sys.stdout = open("out.txt","w")
sys.stderr = open("err.txt","w")
#get_ipython().run_line_magic('matplotlib', 'inline')


datafile = "/home/tod/data/lightning_sensor/lightning_sensor_data.csv"
output_file = "/home/tod/data/lightning_sensor/lightning_sensor_data_plot.pdf"
title = 'Tucson Lightning Sensor Data'

# Values to normalize environmental data
norm_pressure = 900


#Read .CSV file into a Pandas Data Structure below

#df = pd.read_csv(datafile,  infer_datetime_format='True',  date_parser=parse_dates, dayfirst=True, low_memory=False)
df = pd.read_csv(datafile, parse_dates=True, infer_datetime_format='True', dayfirst=True, low_memory=False)
#df = pd.read_csv(datafile, index_col='Time', parse_dates=True, infer_datetime_format='True', dayfirst=True, low_memory=False)
#df['Time'] = pd.to_datetime(df['Time'].str.strip(), dayfirst = False)
df = df.dropna()



#Fix Date Formats Below

def parse_dates(x):
    return datetime.datetime.strptime(x, '%H:%M:%S - %Y/%m/%d')
    
x = []

timestamp = df['Time']
y1 = df['Humidity (%)']
y1b = df['Distance']
y1c = df['Pressure (HP-900)'] - norm_pressure
y1d = df['Temperature (deg F)']
y1e = df['Full Light Spectrum'] / 5.0
y1f = df['IR Spectrum'] / 5.0
y2 = df['Energy'] / 3.0

for t in timestamp:
    x.append(parse_dates(t))
  
d = scipy.zeros(len(y1f))
  
with PdfPages(output_file) as pdf:
    try:
        fig, ax1 = plt.subplots(figsize=(12, 8))
        plt.xticks(rotation=45)
        ax2 = ax1.twinx()
        ax1.plot(x, y1, 'g-')
        ax1.plot(x, y1b, 'r*')
        ax1.plot(x, y1c, 'c-')
        ax1.plot(x, y1d, 'm-')
        ax1.plot(x, y1e, 'b:')
        ax1.fill_between(x,y1e,where=y1f>=d, interpolate=True, color='lightcyan')  
        ax1.plot(x, y1f, 'g:')
        ax1.fill_between(x,y1f,where=y1f>=d, interpolate=True, color='greenyellow')  
        ax2.plot(x, y2, 'b-')

        ax1.set_xlabel('Time/Date')
        ax1.set_ylabel('Environmental Data and Lightning Distance', color='k')
        #ax1.set_xlim(left=datetime.date(2018, 7, 20))
        ax2.set_ylabel('Lightning Energy', color='b')
    
        #ax2.legend(loc='best')
        ax1.legend(loc='best')
    
        plt.xticks(rotation=45)

        plt.title('Lightning activity fused with Weather data for Tucson (85718)')
        #plt.show()
    
        fig.savefig('/home/tod/data/lightning_sensor/lightning1.png')



        pdf.savefig(fig)  # or you can pass a Figure object to pdf.savefig
        plt.close()

        # We can also set the file's metadata via the PdfPages object:
        d = pdf.infodict()
        d['Title'] = title
        d['Author'] = u'W. Tod Newman\xe4nen'
        d['Subject'] = 'Fusion of Lightning sensor data with environmental sensor data'
        d['Keywords'] = 'lightning, tucson, humidity, pressure, temperature'
        d['CreationDate'] = datetime.datetime(2018, 7, 13)
        d['ModDate'] = datetime.datetime.today()
    except Exception as error:
        print( "<p>Error: %s</p>" % str(error) )

        
