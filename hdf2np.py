import h5py
import numpy as np
import tifffile as tf
from osgeo import gdal
from fy3pro import FY3Orbit, fy3pro
from fypy.tools import readhdf
import shapely.geometry
import os
from tqdm import tqdm
def hdf2np(geo_filepath,data_filepath):
    pass

def check_points(data_file,center_point):
    x,y=center_point
    data_hdf= h5py.File(data_file, 'r')
    lat_list=data_hdf.attrs['Orbit Point Latitude']
    lon_list=data_hdf.attrs['Orbit Point Longitude']
    point = shapely.geometry.Point(x,y)
    poly_context = {'type': 'MULTIPOLYGON',
    'coordinates': [[[[lon_list[i],lat_list[i]] for i in range(4)]]]}
    poly_shape = shapely.geometry.shape(poly_context)
    return poly_shape.intersects(point)

def write2tif(data_file,geo_file,geo_range,outpath):
    fp=open("./log.txt","w") 
    center_point=((geo_range[0]+geo_range[1])/2,(geo_range[2]+geo_range[3])/2)
    if not check_points(data_file,center_point):
        print("no inter: ",os.path.split(data_file)[1])
        fp.write("no inter: "+os.path.split(data_file)[1]+"\n")
        return
    print("getinter: "+os.path.split(data_file)[1])
    fp.write("getinter: "+os.path.split(data_file)[1]+"\n")
    geo_hdf= h5py.File(geo_file, 'r')
    lat=geo_hdf['Geolocation']['Latitude']
    lon=geo_hdf['Geolocation']['Longitude']
    lat=np.array(lat)
    lon=np.array(lon)
    mpro = fy3pro()
    band1 = mpro.Calibration(data_file, '/Data/EV_1KM_LL')
    band25 = mpro.Calibration(data_file, '/Data/EV_1KM_Emissive')
    band67 =mpro.Calibration(data_file, '/Data/EV_250_Aggr.1KM_Emissive')
    bandAll=np.concatenate([band1,band25,band67],axis=0)
    mpro = FY3Orbit(bandAll, lat, lon, dstfile=os.path.join(outpath,os.path.split(data_file)[1].replace("HDF","tif")),
                resolution=0.025, vmin=0, vmax=25000, resampleAlg=gdal.GRIORA_Bilinear,
                minX=116.2,maxX=129.0,minY=28.7,maxY=41.5)

if __name__=='__main__':
    DATA_ROOT="K:/FY3E/MERSI/1000M"
    GEO_ROOT="K:/FY3E/MERSI/GEO1K"
    OUTPUT="E:/fy4e"
    for dir in os.listdir(DATA_ROOT):
        for filename in list(filter(lambda x:x.endswith("HDF"),os.listdir(os.path.join(DATA_ROOT,dir)))) :
            data_filepath=os.path.join(DATA_ROOT,dir,filename)
            geo_filepath=os.path.join(GEO_ROOT,dir,filename.replace("1000M","GEO1K"))
            write2tif(data_filepath,geo_filepath,[116.2,129.0,28.7,41.5],OUTPUT)

            
    # geo_file="K:/FY3E/MERSI/GEO1K/20230306/FY3E_MERSI_GRAN_L1_20230306_1840_GEO1K_V0.HDF"
    # data_file="K:/FY3E/MERSI/1000M/20230306/FY3E_MERSI_GRAN_L1_20230306_1840_1000M_V0.HDF"

    
    # # write2tif(data_file,geo_file,[73.39911225249426,135.1873203714432,3.737891241334588,53.66164651851026],OUTPUT)
    # geo_hdf= h5py.File(geo_file, 'r')
    # data_hdf= h5py.File(data_file, 'r')
    # lat=geo_hdf['Geolocation']['Latitude']
    # lon=geo_hdf['Geolocation']['Longitude']
    # lat=np.array(lat)
    # lon=np.array(lon)
    # # with open("lonlat.csv","w") as fp:
    # #     for i in range(lat.shape[0]):
    # #         for j in range(lat.shape[1]):
    # #             fp.write(str(lat[i][j])+", "+str(lon[i][j])+"\n")

    
    # mpro = fy3pro()
    # band1 = mpro.Calibration(data_file, '/Data/EV_1KM_LL')
    # band25 = mpro.Calibration(data_file, '/Data/EV_1KM_Emissive')
    # band67 =mpro.Calibration(data_file, '/Data/EV_250_Aggr.1KM_Emissive')
    # bandAll=np.concatenate([band1,band25,band67],axis=0)
    
    # # lat = readhdf(geo_file, '/Geolocation/Latitude')
    # # lon = readhdf(geo_file, '/Geolocation/Longitude')
    # # mpro = FY3Orbit(band25, lat, lon, dstfile=r'./test100-1.tif',
    # #                 resolution=0.025, vmin=0, vmax=25000, resampleAlg=gdal.GRIORA_Bilinear,
    # #                 minX=116.2,maxX=129.0,minY=28.7,maxY=41.5)
    # mpro = FY3Orbit(band67, lat, lon, dstfile=r'./test100-1.tif',
    #                 resolution=0.025, vmin=0, vmax=25000, resampleAlg=gdal.GRIORA_Bilinear)
    # #                 # minX=73.39911225249426,maxX=135.1873203714432,minY=3.737891241334588,maxY=53.66164651851026)
    pass