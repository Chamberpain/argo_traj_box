import pandas as pd
import oceans
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
import os


def dataframe_plot(df_,m):
	lon_list = df_.longitude.values
	lat_list = df_.latitude.values
	m.plot(lon_list,lat_list,latlon=True)

def map_particle_plot(dataframe):
	m = Basemap(projection='cea',llcrnrlat=lllat,urcrnrlat=urlat,llcrnrlon=lllon,urcrnrlon=urlon,resolution='c',lon_0=0,fix_aspect=False)
	m.drawcoastlines(linewidth=1.5)
	line_space=20
	fontsz=10
	parallels = np.arange(-90,0,float(line_space)/2)
	m.drawparallels(parallels,labels=[1,0,0,0],fontsize=fontsz)
	meridians = np.arange(-360.,360.,float(line_space))
	m.drawmeridians(meridians,labels=[0,0,0,1],fontsize=fontsz)

	m.plot(lon,lat,marker='s',color='gold',markersize=10,zorder=10,markeredgecolor='black',markeredgewidth=2,latlon=True)
	lat_min = lat- degree_size
	lat_max = lat+ degree_size
	lon_min = oceans.datasets.datasets.wrap_lon180(lon-degree_size)[0]
	lon_max = oceans.datasets.datasets.wrap_lon180(lon+degree_size)[0]
	df_cut = dataframe[((dataframe.longitude<lon_max)&(dataframe.longitude>lon_min))&((dataframe.latitude<lat_max)&(dataframe.latitude>lat_min))]
	cruise_date_df = []
	print('the cruises are')
	print(df_cut.Cruise.unique())
	for cruise in df_cut.Cruise.unique():
		token = dataframe[(dataframe.Cruise==cruise)]
		cutoff = df_cut[df_cut.Cruise==cruise].index.min()
		token = token[token.index>=cutoff]
		if len(token)<=2:
			continue
		else:
			dataframe_plot(token,m)

sose_df_file = os.getenv("HOME")+'/iCloud/Data/Processed/transition_matrix/sose_particle_df.pickle'
sose_df = pd.read_pickle(sose_df_file)
sose_df['latitude'] = sose_df['Lat']
sose_df['longitude'] = sose_df['Lon']
df = pd.read_pickle('traj_df.pickle')

polarstern_loc = [(-65.5, 30.0),
(-63.0, 30.0),
(-61.0, 30.0),
(-51.0, 30.0),
(-44.0, 30.0),
(-35.0, 30.0),
(-33.3335, 28.2012),
   ]

degree_size = 0.5

lllat=-70
urlat=-15
lllon=0
urlon=140
df = df[(df.longitude<urlon+20)&(df.longitude>lllon-20)] #this prevents wrapping issues
sose_df = sose_df[(sose_df.longitude<urlon+20)&(sose_df.longitude>lllon-20)] #this prevents wrapping issues

data_list = [(polarstern_loc,'I6S ')]
for dlist,name in data_list:
	for loc in dlist:
		lat,lon = loc
		print('the location is '+str(loc))
		plt.figure()
		plt.suptitle(name+str(lat)+' , '+str(lon))
		plt.subplot(2,1,1)
		plt.title('Argo')
		map_particle_plot(df)
		plt.subplot(2,1,2)
		plt.title('SOSE')
		map_particle_plot(sose_df)
		plt.savefig(name[:-1]+'_'+str(lat)+' , '+str(lon)+'.png')
		plt.close()