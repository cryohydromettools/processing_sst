import sys
sys.path.append('lib_gmi/')
from lib_gmi.gmi_daily_v8 import GMIdaily
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

# declaration functions
def read_data(filename='data/gmi/f35_20161001v8.2.gz'):
    dataset = GMIdaily(filename, missing=missing)
    if not dataset.variables: sys.exit('problem reading file')
    return dataset

def show_variables(ds):
    print()
    print('Variables:')
    for var in ds.variables:
        print(' '*4, var, ':', ds.variables[var].long_name)

def show_validrange(ds):
    print()
    print('Valid min and max and units:')
    for var in ds.variables:
        print(' '*4, var, ':', \
              ds.variables[var].valid_min, 'to', \
              ds.variables[var].valid_max,\
              '(',ds.variables[var].units,')')
              

### function to insert variables to dataset
def insert_var(ds, var, name, units, long_name):
    ds[name] = (('lat','lon'), var)
    ds[name].attrs['units'] = units
    ds[name].attrs['long_name'] = long_name
    ds[name].attrs['_FillValue'] = -9999


ilon = (169,174)
ilat = (273,277)
iasc = 0
avar = 'sst'
missing = -999.

dataset = read_data()
print(show_variables(dataset))
print(show_validrange(dataset))

## create netcdf gmi
ds = xr.Dataset()

ds.coords['lon'] = dataset.variables['longitude'] - 180
ds.lon.attrs['standard_name'] = 'lon'
ds.lon.attrs['long_name'] = 'longitude'
ds.lon.attrs['units'] = 'degrees_east'

ds.coords['lat'] = dataset.variables['latitude']
ds.lat.attrs['standard_name'] = 'lat'
ds.lat.attrs['long_name'] = 'latitude'
ds.lat.attrs['units'] = 'degrees_north'

# Valid min and max and units: sst : -3.0 to 34.5 ( deg Celsius )
sst = dataset.variables['sst'][:,:,:]
sst[sst < -3 ]   = np.nan
sst[sst > 34.5 ] = np.nan
sst = np.nanmean(sst, axis=0)
sst = np.concatenate((sst[:,720:1440],sst[:,0:720]), axis=1)

insert_var(ds, sst,'SST','°C','Sea Surface Temperature')

sst_mod  = xr.open_dataset('data/modis/A2016275.L3m_DAY_SST_sst_4km.nc')
nsst_mod = xr.open_dataset('data/modis/A2016275.L3m_DAY_NSST_sst_4km.nc')
print(nsst_mod)


## create netcdf modis

ds_modis = xr.Dataset()

ds_modis.coords['lon'] = sst_mod['lon'].values
ds_modis.lon.attrs['standard_name'] = 'lon'
ds_modis.lon.attrs['long_name'] = 'longitude'
ds_modis.lon.attrs['units'] = 'degrees_east'

ds_modis.coords['lat'] = sst_mod['lat'].values
ds_modis.lat.attrs['standard_name'] = 'lat'
ds_modis.lat.attrs['long_name'] = 'latitude'
ds_modis.lat.attrs['units'] = 'degrees_north'

# Valid min and max and units: sst : -2.0 to 45 ( deg Celsius )
sst_modis = np.dstack((sst_mod['sst'].values, nsst_mod['sst'].values))
sst_modis[sst_modis < -2] = np.nan
sst_modis[sst_modis > 45] = np.nan
sst_modis = np.nanmean(sst_modis, axis=2)
insert_var(ds_modis, sst_modis,'SST','°C','Sea Surface Temperature')

# Interpolate from modis to gmi
sst_modisi = ds_modis.interp(lat=ds['lat'], lon=ds['lon'])

# plot sst gmi and modis
fig, axes = plt.subplots(ncols=2, figsize=(12, 4))
ds['SST'].plot(ax=axes[0], vmin = -3, vmax = 45, cmap = 'jet', clim=(-3, 45))
sst_modisi['SST'].plot(ax=axes[1], vmin = -3, vmax = 45, cmap = 'jet', clim=(-3, 45))
fig.savefig('plots/sst_gmi_modis.png',dpi = 300, bbox_inches = 'tight',pad_inches = 0.1)

# plot diference SST GMI - MODIS
fig, axes = plt.subplots(figsize=(6, 4))
(ds['SST']-sst_modisi['SST']).plot(vmin = -3, vmax = 8, cmap = 'jet', clim=(-3, 8), cbar_kwargs={'label': 'SST GMI - MODIS [°C]'})
fig.savefig('plots/sst_diff_gmi_modis.png',dpi = 300, bbox_inches = 'tight',pad_inches = 0.1)

# plot hist diference SST GMI - MODIS
fig, axes = plt.subplots(figsize=(6, 4))
(ds['SST']-sst_modisi['SST']).plot.hist(bins=50)
axes.set_xlim(-8,8)
axes.set_ylabel('Frequency')
axes.set_xlabel('SST GMI - MODIS [°C]')
axes.set_title('')
fig.savefig('plots/hist_gmi_modis.png',dpi = 300, bbox_inches = 'tight',pad_inches = 0.1)

# plot profile SST GMI and MODIS
fig, axes = plt.subplots(figsize=(6, 4))
ds['SST'].sel(lat=0,  method='nearest').plot(label='GMI', lw=0.8)
ds_modis['SST'].sel(lat=0,  method='nearest').plot(label='MODIS', lw=0.8)
axes.set_title('')
axes.legend(loc='best',ncol=2, frameon=False)
fig.savefig('plots/profile_sst.png',dpi = 300, bbox_inches = 'tight',pad_inches = 0.1)












