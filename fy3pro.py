# -*- coding:utf-8 -*-
'''
@Project     : fypy

@File        : __init__.py

@Modify Time :  2022/11/10 14:45

@Author      : Lee

@Version     : 1.0

@Description :

'''
import os
import sys
import numpy as np
import datetime
import h5py
from osgeo import gdal, ogr, osr
import cv2
from fypy.tools import readhdf, readhdf_fileinfo, writehdf, writetiff

from config import FY3Block10CoefX, FY3Block10CoefY, ProdInfo

class fy3pro(object) :

    def __init__(self):
        pass

    def Calibration(self, filename, sdsname):

        # EV_250_Aggr.1KM_RefSB     1~4         # 0.47, 0.55, 0.65, 0.865,
        # EV_1KM_RefSB              5~19        # 1.38, 1.64, 2.13, 0.412,
        #                                         0.443, 0.49, 0.555, 0.67,
        #                                         0.709, 0.746, 0.865, 0.905,
        #                                         0.936, 0.94, 1.03,
        # EV_1KM_Emissive           20~23       # 3.796, 4.046, 7.233, 8.56,
        # EV_250_Aggr.1KM_Emissive  24~25       # 10.714, 11.948

        if 'EV_1KM_Emissive' in sdsname :
            data = readhdf(filename, sdsname)
            return data
            # fileinfo = readhdf_fileinfo(filename)
            fileinfo= h5py.File(filename, 'r')
            wave_length = fileinfo['Calibration']['Effect_Center_WaveLength']
            # wave_length = fileinfo['Effect_Center_WaveLength']
            
            return self.calemiss(data, 10000.0/wave_length[np.arange(2, 6)-1])
            # coef = readhdf(filename, '/Calibration/IR_Cal_Coeff')
            # return self.calref(data, coef[np.arange(2, 6)-1, :])
            # return data

        elif 'EV_250_Aggr.1KM_Emissive' in sdsname :
            data = readhdf(filename, sdsname)
            return data
            # fileinfo = readhdf_fileinfo(filename)
            # fileinfo= h5py.File(filename, 'r')
            # wave_length = fileinfo['Calibration']['Effect_Center_WaveLength']
            # return self.calemiss(data, 10000.0/wave_length[np.arange(6, 8)-1])
            # coef = readhdf(filename, '/Calibration/IR_Cal_Coeff')
            # return self.calref(data, coef[np.arange(6, 8)-1, :])

        elif 'EV_1KM_LL' in sdsname :
            data = readhdf(filename, sdsname)
            data=data[np.newaxis]
            return data
            # fileinfo= h5py.File(filename, 'r')
            # coef = readhdf(filename, '/Calibration/VIS_Cal_Coeff')
            # wave_length = fileinfo['Calibration']['Effect_Center_WaveLength']
            # return self.calemiss(data, 10000.0/wave_length[np.arange(1, 2)-1])
            # return self.calref(data, coef[np.arange(1, 5)-1, :])

        elif 'EV_1KM_RefSB' in sdsname :
            data = readhdf(filename, sdsname)
            coef = readhdf(filename, '/Calibration/VIS_Cal_Coeff')

            return self.calref(data, coef[np.arange(5, 20)-1, :])

        else:
            tmpdata, sdsinfo = readhdf(filename, sdsname,dictsdsinfo={})
            data = tmpdata.copy()
            if 'Slope' in sdsinfo and 'Intercept' in sdsinfo:
                data = data * sdsinfo['Slope'] + sdsinfo['Intercept']

            if 'valid_range' in sdsinfo :
                data[(tmpdata < sdsinfo['valid_range'][0]) | (tmpdata > sdsinfo['valid_range'][1])] = np.nan

            return data
    
    def calref(self, dn, coef):
        coef=coef.transpose((1,2,0))
        coef=cv2.resize(coef,(2000,4),interpolation=cv2.INTER_NEAREST)
        coef=coef.transpose((2,0,1))
        # print(np.array(coef[0, 1,:,np.newaxis]).shape)
        ''' 可见光通道定标 '''
        ref = np.full_like(dn, fill_value=np.nan, dtype=np.float32)
        for i in range(dn.shape[0]) :
            ref[i] = coef[i, 0,:,np.newaxis] + coef[i, 1,:,np.newaxis] * dn[i] + coef[i, 2,:,np.newaxis] * dn[i] * dn[i]

            ref[i, dn[i] == 65535] = np.nan
            ref[i, ref[i]<=0] = 0

        return ref

    def calemiss(self, dn, wavenum):
        ''' 红外波段定标 '''
        temp = dn * 0.01
        temp[(temp<=0) | (temp >= 600.0)] = np.nan

        bt = np.full_like(temp, fill_value=np.nan, dtype=np.float32)

        for i in range(temp.shape[0]) :
            bt[i] = self.planck_r2t(temp[i, :, :], wavenum[i])

        return bt

    def planck_r2t(self, rad, wn):
        '''
        普朗克函数：将辐射值转成亮温（K）

        Parameters
        ----------
        rad : numpy.narray
            mW/(m2.cm-1.sr)
        wn : float or numpy.narray
            wave number(cm^-1)

        Returns
        -------
            numpy.narray
            bright temperature
            units: K
        '''
        # 普朗克系数
        Radiation_C1 = 1.191042953E-5
        Radiation_C2 = 1.4387774

        bt = (Radiation_C2 * wn / np.log(Radiation_C1 * wn * wn * wn / (rad)+1.0))

        return bt


class FY3Block10():

    def __init__(self, SatID, InstID, productName, filelist, sdsname, resolution, outname=None):

        self.resolution = resolution
        self.SatID = SatID
        self.InstID = InstID
        self.SDSName = sdsname

        if isinstance(filelist, list):
            self._MultipleFiles(filelist, productName, outname=outname)
        elif isinstance(filelist, str):
            self._SingleFiles(filelist, productName, outname=outname)

    def _SingleFiles(self, filename, productName, outname=None) :
        '''单个数据产品投影拼接'''
        basename = os.path.basename(filename)
        names = basename.split('_')
        blockID = names[2]

        lat = FY3Block10CoefY[blockID[0:2]]
        lon = FY3Block10CoefX[blockID[2:4]]

        mtrans = [lon, self.resolution, 0,
                  lat, 0, -self.resolution]

        Dict_DataSets = self.GetData(filename, productName)

        ds = writetiff(outname=outname, data=Dict_DataSets[self.SDSName],
                       im_geotrans=mtrans, fillvalue=self.fillvalue)

        return ds

    def _MultipleFiles(self, filelist, productName, outname=None) :
        '''多个数据产品投影拼接'''
        countfile = len(filelist)
        if countfile == 0 :
            return None
        elif countfile == 1 :
            self._SingleFiles(filelist[0], productName)
        else:
            all_ds = []

            for filename in filelist :
                dset = self._SingleFiles(filename, productName)
                all_ds.append(dset)

            if outname is None :
                format = 'MEM'
                outname=''
                creationOptions=[]
            else:
                format = 'GTiff'
                creationOptions=["COMPRESS=LZW"]

            ds = gdal.Warp(outname, all_ds, dstSRS='EPSG:4326', format=format,
                           xRes=self.resolution, yRes=self.resolution, dstNodata=self.fillvalue,
                           srcNodata=self.fillvalue, resampleAlg=gdal.GRA_NearestNeighbour,
                           creationOptions=creationOptions)

            return ds

    def getBoundingBox(self, filelist):

        tileindex = []

        for filename in filelist :
            basename = os.path.basename(filename)
            names = basename.split('_')
            blockID = names[2]

            lat = FY3Block10CoefY[blockID[0:2]]
            lon = FY3Block10CoefX[blockID[2:4]]

            tileindex.append([lat, lon])

        tileindex = np.array(tileindex)
        maxY = np.nanmax(tileindex[:,0])
        minY = np.nanmin(tileindex[:,0])

        maxX = np.nanmax(tileindex[:,1])
        minX = np.nanmin(tileindex[:,1])

        # mtrans = [minX, self.resolution, 0,
        #           minY, 0, self.resolution]

        extent = [minX, maxX+10, minY, maxY+10]

        return extent

    def GetData(self, filename, productName):

        Dict_DataSets = {}

        try:
            if productName in ProdInfo[self.SatID][self.InstID]:
                val, sdsinfo = readhdf(filename, self.SDSName, dictsdsinfo={})
                if 'FillValue' in sdsinfo :

                    if isinstance(sdsinfo['FillValue'], np.ndarray) :
                        self.fillvalue = sdsinfo['FillValue'][0]
                    else:
                        self.fillvalue = sdsinfo['FillValue']

                else:
                    self.fillvalue = 65535

                if 'valid_range' in sdsinfo :
                    vmin = sdsinfo['valid_range'][0]
                    vmax = sdsinfo['valid_range'][1]
                    fillflag = (val<vmin) | (val>vmax)

                if 'Slope' in sdsinfo and 'Intercept' in sdsinfo :
                    val = val * sdsinfo['Slope'] + sdsinfo['Intercept']

                val[fillflag] = self.fillvalue
                if 'valid_range' in sdsinfo :
                    vmin = sdsinfo['valid_range'][0]
                    vmax = sdsinfo['valid_range'][1]
                    fillflag = (val<vmin) | (val>vmax)
                    # val[fillflag] = self.fillvalue

                if productName == 'CLM':
                    data_u8 = np.uint8(val)
                    data_bit = np.unpackbits(data_u8).reshape(data_u8.size, 8)
                    bit21 = data_bit[:, 5] * 4 + data_bit[:, 6] * 2 + data_bit[:, 7]
                    val = bit21.reshape(val.shape)
                    # 001 = Cloudy （1）
                    # 011 = Uncertain （3）
                    # 101 = Probably  Clear （5）
                    # 111 = Confident  Clear （7）
                    val[(val != 1) & (val != 3) & (val != 5) & (val != 7)] = 255
                    val[val==1] = 0
                    val[val==3] = 1
                    val[val==5] = 2
                    val[val==7] = 3
                    self.fillvalue = 255

                key = self.SDSName.replace(' ', '_')
                if '/' in key :
                    key = key.split('/')[-1]
                Dict_DataSets[key] = val
            else:
                print('产品【%s】不在绘图要求列表之内' %(productName))
        except BaseException as  e :
            print('读取【%s】：%s失败！！！' %(productName, filename))

        return Dict_DataSets

class FY3Orbit() :
    '''针对FY-3卫星数据，包含MERSI 5分钟块、
    MWRI 升降轨、MWHS、MWTS等整圈轨道数据的投影、拼接、裁剪'''
    def __init__(self, srcdata, srclat, srclon, dstfile=None,
                 vmin=None, vmax=None, resolution=0.01,
                 minX=None, maxX=None, minY=None, maxY=None,  # 需要投影的区域范围
                 resampleAlg=gdal.GRIORA_NearestNeighbour,
                 srcNodata=-999.0, dstNodata=None, dstSRS="EPSG:4326"):
        '''

        Parameters
        ----------
        srcdata :
        srclat :
        srclon :
        dstfile :
        vmin :
        vmax :
        resolution :
        minX :
        maxX :
        minY :
        maxY :
        resampleAlg :
        srcNodata :
        dstNodata :
        dstSRS :
        '''
        self.TempFile = []

        if dstfile is None :
            srcfile = './tempfile_%s.temp' %(datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S'))
        else:
            srcfile = dstfile

        if dstNodata is None :
            dstNodata = srcNodata

        flag = (srclon > 180) | (srclon < -180) \
             | (srclat > 90)  | (srclat < -90)
        srclon[flag] = np.nan
        srclat[flag] = np.nan
        # srcdata[flag] = np.nan

        # 获取投影数据的范围
        if maxX is None :
            maxX = np.nanmax(srclon)

        if minX is None :
            minX = np.nanmin(srclon)

        if maxY is None :
            maxY = np.nanmax(srclat)

        if minY is None :
            minY = np.nanmin(srclat)

        if vmin is None :
            vmin = np.nanmin(srcdata)

        if vmax is None :
            vmax = np.nanmax(srcdata)

        data = np.array(srcdata).copy()


        if vmax is not None and vmin is not None :
            data[(srcdata < vmin) | (srcdata > vmax)] = srcNodata

        data[np.isnan(data)] = srcNodata

        temphdf = os.path.splitext(srcfile)[0] + '.hdf'
        self.TempFile.append(temphdf)
        # 创建临时的数据文件
        writehdf(temphdf, 'data', data, overwrite=1)
        writehdf(temphdf, 'lon', srclon, overwrite=0)
        writehdf(temphdf, 'lat', srclat, overwrite=0)

        layer = self._GetSourceInfo(temphdf, 'data')

        vrtFile = os.path.splitext(srcfile)[0] + '.vrt'
        self.TempFile.append(vrtFile)

        self._createVrt(vrtFile, temphdf, layer, '/lon', '/lat')

        if dstfile is None :
            format = 'MEM'
            dstfile = None
        else:
            format = 'GTiff'

        geoData = gdal.Warp(dstfile, vrtFile,
                            format=format,  geoloc=True,
                            dstSRS=dstSRS,  resampleAlg=resampleAlg,
                            srcNodata= srcNodata, dstNodata=dstNodata,
                            outputBounds=(minX, minY, maxX, maxY),  # (minX, minY, maxX, maxY)
                            xRes=resolution, yRes=resolution,
                            creationOptions=["COMPRESS=LZW"])

        if geoData == None:
            print('处理失败')
            return None

        width = geoData.RasterXSize #栅格矩阵的列数
        height = geoData.RasterYSize #栅格矩阵的行数
        im_bands = geoData.RasterCount #波段数

        im_data = geoData.ReadAsArray(0, 0, width, height)#获取数据
        im_geotrans = geoData.GetGeoTransform()#获取仿射矩阵信息
        im_proj = geoData.GetProjection()#获取投影信息

        if dstfile is not None :
            print('完成投影转换{}\n'.format(srcfile))

        if vmax is not None and vmin is not None :
            im_data[(im_data < vmin) | (im_data > vmax)] = dstNodata

    def _GetSourceInfo(self, filename, sdsname):
        src_ds = gdal.Open(filename)
        layers = src_ds.GetSubDatasets()

        # 获取sdsname所在的图层栅格索引
        src_raster = self.GetLayer(layers, sdsname)
        if src_raster is None :
            raise Exception('数据集【%s】不在文件中【%s】' %(sdsname, filename))

        return src_raster

    def GetLayer(self, layers, sdsname):
        '''
        获取指定的图层的索引名
        :param layers: tuple
        :return: str
        '''

        if sdsname:
            for layer in layers :
                l_name = layer[0].split(':')[-1].replace('"','')
                # print(self.sdsname, l_name)
                if sdsname in l_name:
                    return layer[0]

        return None

    def _createVrt(self, vrtDir, srcfile, layer, srclon=None, srclat=None):

        if layer is None :
            gdal.Translate(vrtDir,
                           srcfile,
                           format='vrt')
        else:
            gdal.Translate(vrtDir,
                           layer,
                           format='vrt')

        lines = []
        with open(vrtDir, 'r') as f:
            for line in f:
                lines.append(line)
        lines.insert(1,'<Metadata domain="GEOLOCATION">\n')
        lines.insert(2,' <MDI key="LINE_OFFSET">1</MDI>\n')
        lines.insert(3, ' <MDI key="LINE_STEP">1</MDI>\n')
        lines.insert(4, ' <MDI key="PIXEL_OFFSET">1</MDI>\n')
        lines.insert(5, ' <MDI key="PIXEL_STEP">1</MDI>\n')
        lines.insert(6, ' <MDI key="SRS">GEOGCS["WGS84",'
                        'DATUM["WGS_1984",'
                        'SPHEROID["WGS84",6378137,298.257223563,'
                        'AUTHORITY["EPSG","7030"]],'
                        'TOWGS84[0,0,0,0,0,0,0],'
                        'AUTHORITY["EPSG","6326"]],'
                        'PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],'
                        'UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9108"]],'
                        'AUTHORITY["EPSG","4326"]]</MDI>\n')
        lines.insert(7, ' <MDI key="X_BAND">1</MDI>')
        lines.insert(8, ' <MDI key="X_DATASET">HDF5:"{geofile}":/{srclon}</MDI>\n'.format(
            geofile=srcfile, srclon=srclon))
        lines.insert(9, ' <MDI key="Y_BAND">1</MDI>\n')
        lines.insert(10, ' <MDI key="Y_DATASET">HDF5:"{geofile}":/{srclat}</MDI>\n'.format(
            geofile=srcfile, srclat=srclat))
        lines.insert(11, '</Metadata>\n')
        with open(vrtDir, 'w') as f:
            for line in lines:
                f.writelines(line)

    def __del__(self):
        '''
        清理临时文件
        :return:
        '''
        for item in self.TempFile :
            if os.path.isfile(item) :
                try:
                    os.remove(item)
                    # print(item)
                except BaseException as e:
                    print('删除%s失败' %(item))


