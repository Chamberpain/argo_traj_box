import numpy as np
import pandas as pd
from ftplib import FTP 
import requests
import os
from netCDF4 import Dataset
import pickle

def wrap_lon180(lon):
    lon = np.atleast_1d(lon).copy()
    angles = np.logical_or((lon < -180), (180 < lon))
    lon[angles] = wrap_lon360(lon[angles] + 180) - 180
    return lon

def wrap_lon360(lon):
    lon = np.atleast_1d(lon).copy()
    positive = lon > 0
    lon = lon % 360
    lon[np.logical_and(lon == 0, positive)] = 360
    return lon

def download_meta_file_and_compile_df():
	url = 'http://soccom.ucsd.edu/floats/SOCCOM_float_stats.html'
	html = requests.get(url).content  
	df_list = pd.read_html(html)[0] 
	wmoID_list = df_list['TrajMBARI dataWMOID'].values
	wmoID_list = wmoID_list[wmoID_list!=-999]
	wmoID_list = [str(dummy) for dummy in wmoID_list]

	def ftp_download(server_path,dummy=True):
		try:
			link = 'usgodae.org'
			ftp = FTP(link) 
			ftp.login()		
			filename = os.path.basename(server_path)
			relative_change = os.path.relpath(os.path.dirname(server_path),ftp.pwd())
			ftp.cwd(relative_change)
			if dummy:
				file = open('dummy','wb')
			else:
				file = open(filename, 'wb')
			ftp.retrbinary('RETR %s' % filename,file.write,8*1024)
			file.close()
			ftp.close()
		except:
			print('Ive experienced a timeout error, trying again')
			ftp_download(server_path,dummy=dummy)

	global_prof_filename = '/pub/outgoing/argo/ar_index_global_prof.txt'
	global_meta_filename = '/pub/outgoing/argo/ar_index_global_meta.txt'

	ftp_download(global_prof_filename,dummy=False)
	ftp_download(global_meta_filename,dummy=False)

	df_ = pd.read_csv(global_meta_filename.split('/')[-1],skiprows=8)
	df_['wmo_id']=[_[1].split('/')[1] for _ in df_.file.iteritems()]
	try:
		with open('position_system_list','rb') as fp:
			position_system_list = pickle.load(fp)
		wmo_list, position_list = zip(*position_system_list)
	except IOError:
		wmo_list = []
		position_system_list = []
	df_query = df_[~df_['wmo_id'].isin(wmo_list)]
	for k,token in enumerate(df_query['file'].iteritems()):
		print('Hi Susan, im working on file '+str(k)+' of '+str(len(df_query)))
		file = '/pub/outgoing/argo/dac/' + token[1]
		ftp_download(file)
		ncfid = Dataset('dummy')
		float_id = ncfid.variables['PLATFORM_NUMBER'][:]
		try:
			float_id = ''.join([_.decode("utf-8") for _ in float_id.data[~float_id.mask].tolist()])
		except AttributeError:
			float_id = ''.join([_.decode("utf-8") for _ in float_id.data[~float_id.mask].tolist()[0]])

		pos_system = ncfid.variables['POSITIONING_SYSTEM'][:]
		try:
			pos_system = ''.join([_.decode("utf-8") for _ in pos_system.data[~pos_system.mask].tolist()])
		except AttributeError:
			pos_system = ''.join([_.decode("utf-8") for _ in pos_system.data[~pos_system.mask].tolist()[0]])

		position_system_list.append((float_id,pos_system))
		if (token[0]%100)==0:
			with open('position_system_list', 'wb') as fp:
			    pickle.dump(position_system_list, fp)
	with open('position_system_list', 'wb') as fp:
	    pickle.dump(position_system_list, fp)
	position_type_dict = dict(position_system_list)
	df_ = pd.read_csv(os.path.basename(global_prof_filename),skiprows=8)
	df_ = df_.dropna(subset=['date'])
	df_['date'] = [int(_) for _ in df_.date.values]
	df_['date'] = pd.to_datetime(df_.date,format='%Y%m%d%H%M%S')
	df_['Cruise'] = [dummy.split('/')[1] for dummy in df_['file'].values]
	df_ = df_[['Cruise','date','latitude','longitude']]
	df_ = df_.sort_values(by=['Cruise','date'])
	df_ = df_[df_.longitude!=99999]
	df_ = df_[df_.longitude!=-999]
	df_ = df_[df_.longitude<=180]
	df_['SOCCOM'] = df_.Cruise.isin(wmoID_list)
	df_['Position Type']=[position_type_dict[_[1]] for _ in df_.Cruise.iteritems()]		
	df_.loc[df_['Position Type']=='IRIDIUM','Position Type']='GPS'
	df_.loc[df_['Position Type']=='GPSIRIDIUM','Position Type']='GPS'
	df_.loc[df_['Position Type']=='IRIDIUMGPS','Position Type']='GPS'
	df_.loc[df_['Position Type']=='GTS','Position Type']='GPS'
	df_.loc[df_['Position Type']=='ARGOS','Position Type']='ARGOS'
	df_ = df_[df_['Position Type'].isin(['GPS','ARGOS'])]
	assert df_.longitude.min()>-180
	assert df_.longitude.max()<=180
	assert df_.latitude.min()>-90
	assert df_.latitude.max()<90
	df_.to_pickle(os.path.dirname(os.path.abspath(__file__))+'/traj_df.pickle')
	print('trajectory data has been downloaded and recompiled')
	return df_

def load_df():
	return pd.read_pickle(os.path.dirname(os.path.abspath(__file__))+'/traj_df.pickle')
