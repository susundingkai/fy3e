# -*- coding: UTF-8 -*-
import os
import h5py
import numpy as np
from numpy import deg2rad, rad2deg, arctan, arcsin, tan, sqrt, cos, sin
from numpy import *
import cv2
from datetime import *
import time
import math
from netCDF4 import Dataset
from skimage import exposure

ea = 6378.137  # 地球的半长轴[km]
eb = 6356.7523  # 地球的短半轴[km]
h = 42164  # 地心到卫星质心的距离[km]
λD = deg2rad(104.7)  # 卫星星下点所在经度

# 列偏移
COFF = {"0500M": 10991.5,
        "1000M": 5495.5,
        "2000M": 2747.5,
        "4000M": 1373.5}
# 列比例因子
CFAC = {"0500M": 81865099,
        "1000M": 40932549,
        "2000M": 20466274,
        "4000M": 10233137}
        
LOFF = COFF  # 行偏移
LFAC = CFAC  # 行比例因子
def latlon2linecolumn(lat, lon, resolution='4000M'):
    """
    (lat, lon) → (line, column)
    resolution：文件名中的分辨率{'0500M', '1000M', '2000M', '4000M'}
    line, column不是整数
    """
    # Step1.检查地理经纬度
    # Step2.将地理经纬度的角度表示转化为弧度表示
    lat = deg2rad(lat)
    lon = deg2rad(lon)
    # Step3.将地理经纬度转化成地心经纬度
    eb2_ea2 = eb**2 / ea**2
    λe = lon
    φe = arctan(eb2_ea2 * tan(lat))
    # Step4.求Re
    cosφe = cos(φe)
    re = eb / sqrt(1 - (1 - eb2_ea2) * cosφe**2)
    # Step5.求r1,r2,r3
    λe_λD = λe - λD
    r1 = h - re * cosφe * cos(λe_λD)
    r2 = -re * cosφe * sin(λe_λD)
    r3 = re * sin(φe)
    # Step6.求rn,x,y
    rn = sqrt(r1**2 + r2**2 + r3**2)
    x = rad2deg(arctan(-r2 / r1))
    y = rad2deg(arcsin(-r3 / rn))
    # Step7.求c,l
    column = COFF[resolution] + x * 2**-16 * CFAC[resolution]
    line = LOFF[resolution] + y * 2**-16 * LFAC[resolution]
    return line, column


# geo_range = [28.2, 41, 117.5, 130.3, 0.05]
# geo_range = [19, 31.8, 114.2, 127, 0.05]
# geo_range = [0,42.8,95,137.8,0.05]
geo_range = [28.2, 41, 117.5, 130.3, 0.05]

lat_S, lat_N, lon_W, lon_E, step = [int(x*10000) for x in geo_range] # int(1000 * x)
# # print(lat_S, lat_N, lon_W, lon_E, step)
# # one less on north,one less on west
lat = np.arange(lat_N-step, lat_S-step, -step)/10000
lon = np.arange(lon_W, lon_E, step)/10000
# # print(lat[0],lat[-1])
# # print(lon[0],lon[-1])

lon_mesh, lat_mesh = np.meshgrid(lon, lat)
line_org, column_org = latlon2linecolumn(lat_mesh, lon_mesh)


def hdf2np(hdf_path):
    """
    input:hdf file path
    output:numpy array 14*1000*1200,dtype=float32  || None

    """
    global line_org, column_org
    res = []
    try:
        with h5py.File(hdf_path, 'r') as f:
            line = np.rint(line_org)-f.attrs['Begin Line Number'][()][0]
            line[line<=0]=0
            line = line.astype(np.uint16)
            column = np.rint(column_org).astype(np.uint16)

            for k in range(1,15):
                nom_name = 'NOMChannel'+'0'*(2-len(str(k)))+str(k)
                # print(nom_name)
                cal_name = 'CALChannel'+'0'*(2-len(str(k)))+str(k) 
                # print(cal_name)
                try:
                    # nom = f["Data"][nom_name][()]
                    # cal = f["Calibration"][cal_name][()]
                    nom = f[nom_name][()]
                    cal = f[cal_name][()]

                except:
                    with open('./error.log','a') as f:
                        f.write(hdf_path+' Channel:'+str(k)+'\n')
                    return 

                channel = nom[line, column]
                CALChannel = cal.astype(np.float32)

                # if k != 7:
                #     CALChannel = np.append(CALChannel, 0)
                #     channel[channel >= 65534] = 4096
                # else:
                #     # fill with 0
                #     CALChannel[65535] = 0

                CALChannel = np.append(CALChannel, 0)
                channel[channel >= 65534] = 4096

                res.append(CALChannel[channel])

            # save
            return np.array(res,dtype=np.float32)


    except:
        with open('./error.log','a') as f:
            f.write('Can not open:'+hdf_path+'\n')

        return None

# npy_15 = hdf2np("FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20221118000000_20221118001459_4000M_V0001.HDF")
# for i in range(15):
#     channel = npy_15[i,:,:]
#     channel = (channel-np.min(channel))/(np.max(channel)-np.min(channel))*255
#     cv2.imwrite('/Users/kaka/Desktop/H8_202301100600/pic/'+str(i)+'.png',channel)


# print(npy_15)
# print("npy_15",npy_15[0])

def make_changecol_RGB(np_out):

    # Forest_exist = (np_out[2] - np_out[1])/(np_out[2] + np_out[1])
    Forest_exist = np_out[2] / np_out[1]
    temp = (Forest_exist>1.5)
    channel2,channel1 = np_out[1].copy(),np_out[2].copy()
    channel1[temp] = (0.55*channel1+0.45*channel2)[temp]
    print(channel1.shape)
    print(channel2.shape)

    # for i in range(1024):
    #     for j in range(1024):
    #         if Forest_exist[i][j] > 1.5:
    #             tmp = np_out[1,i,j]
    #             np_out[1,i,j] = np_out[2,i,j]
    #             np_out[2,i,j] = tmp
    #             np_out[1, i, j] = 0.55* np_out[1, i, j] + 0.45 * np_out[2, i, j]

    b = np_out[0,:,:]
    b = (b-np.min(b))/(np.max(b)-np.min(b))*255
    g = channel1
    g = (g-np.min(g))/(np.max(g)-np.min(g))*255
    r = channel2
    r = (r-np.min(r))/(np.max(r)-np.min(r))*230
    changecol_pic = cv2.merge([b,g,r])
    # cv2.imwrite("./RGB.png",changecol_pic)
    return changecol_pic

# npy_15 = hdf2np("FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20221118000000_20221118001459_4000M_V0001.HDF")
# print("npy_14",npy_14[0])
# changecol_pic = make_changecol_RGB(npy_14)
# cv2.imwrite("./RGB.png",changecol_pic)


# np_out = hdf2np("./source/FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_20210408050000_20210408051459_4000M_V0001.HDF")
def make_RGB(np_out):
    b = np_out[1, :, :]
    b = (b - np.min(b)) / (np.max(b) - np.min(b)) * 255
    g = np_out[2, :, :]
    g = (g - np.min(g)) / (np.max(g) - np.min(g)) * 255
    r = np_out[12, :, :]
    r = (r - np.min(r)) / (np.max(r) - np.min(r)) * 255
    FY4_nc = cv2.merge([b,g,r])
    return FY4_nc


def img_merge(img_dic, gamma_dic):
    """
    Input three images (R, G, B) and gamma
    Merge them and return.
    """
    rgb = []
    for key in img_dic:
        rgb.append(img_dic[key])
    gamma = []
    for key in gamma_dic:
        gamma.append(gamma_dic[key])

    # gamma变换
    gamma_img_r = exposure.adjust_gamma(rgb[0], float(gamma[0]))
    gamma_img_g = exposure.adjust_gamma(rgb[1], float(gamma[1]))
    gamma_img_b = exposure.adjust_gamma(rgb[2], float(gamma[2]))
    cv2.imwrite('gamma_r.png', gamma_img_r)
    img = cv2.merge([gamma_img_b, gamma_img_g, gamma_img_r])

    return img

def substract(img_a, img_b, ranges, channels, channel):
    """
    return A - B with range (tuple)
    """
    maximum, minimum = ranges
    maximum = int(maximum)
    minimum = int(minimum)
    img_a = img_a.astype(np.int32)
    img_b = img_b.astype(np.int32)

    # img_a = recover_orgin_data(img_a, channels[0])
    # img_b = recover_orgin_data(img_b, channels[1])

    img = img_a - img_b

        # maximum = max(np.unique(img)) -4
    if channel =='G':
        # print(np.unique(img))
        print(img[242][12])
        print(img[242][11])
        print(img[242][10])

        print("**************")
        img[img >= maximum] = maximum - 10
    img[img >= maximum] = maximum
    img[img <= minimum] = minimum
    img = cv2.normalize(img, None, 0, 255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC3)
    print(img[242][12])
    print(img[242][11])
    print(img[242][10])

    print("**************")

    return img


# def recover_orgin_data(img, channel):
#     if channel == 0:
#         return img
#
#     log_root = math.log(0.0223, 10)
#     denom = (1 - log_root) * 0.75
#
#     if channel in range(1, 7):
#         img = img * denom / 255 + log_root
#         img_temp = img.tolist()
#         for i in range(len(img_temp)):
#             img_temp[i] = np.power(10, img_temp[i])
#         img = np.array(img_temp)
#         img = img * 255
#     else:
#         img = img + 200
#     return img


# npy_14 = hdf2np("./source/FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_20180411120000_20180411121459_4000M_V0001.HDF")
# npy_14 = hdf2np("./source/FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_20180630130000_20180630131459_4000M_V0001.HDF")
def make_merged(np_out):
    #做夜间海雾图
    channels = ['R', 'G', 'B']
    img_dic,range_dic,channel_dic,gamma_dic = {},{},{},{}
    list1 = [13,12,12]
    list2 = [12,8,-1]

    for i in range(3):
        ch = channels[i]
        # range_dic = { 'R' : (2, -4) , 'G' : (10,0) , 'B' : (293,243)}
        # range_dic = {'R': (6, -14), 'G': (20, -33), 'B': (290, 205)}
        range_dic = { 'R' : (2, -4) , 'G' : (9,0) , 'B' : (293,243)}
        channel_dic = {'R': (13, 12), 'G': (12, 8), 'B': (12, 0)}
        gamma_dic = {'R': "1.0", 'G': "1.0", 'B': "1.0"}
        img_a = np_out[list1[i] - 1, : , : ]
        img_b = np.zeros(img_a.shape)  # TODO: add dtype attribute
        if list2[i] != -1:
            img_b = np_out[list2[i] - 1, :, :]
        img_dic[ch] = substract(img_a, img_b, range_dic[ch], channel_dic[ch], ch)

        for key, value in img_dic.items():
            if value is None:
                print("value is None")

    merged_img = img_merge(img_dic, gamma_dic)
    return merged_img




def night_detect(np_out):
    #检测夜间海雾
    merged_img = make_merged(np_out)

    b = merged_img[:, :, 0]
    g = merged_img[:, :, 1]
    r = merged_img[:, :, 2]

    image_b = cv2.merge([np.zeros(b.shape, np.uint8), g, np.zeros(b.shape, np.uint8)])
    # night_npy = array([[0 for i in range(1024)] for i in range(1024)])

    nightFog_exit = image_b[:,:,1]
    temp = np.logical_and(95 < nightFog_exit, nightFog_exit < 180)
    output = np.zeros(image_b.shape[:2],np.uint8)
    output[temp] = 255
    output = cv2.merge([output, np.zeros(output.shape, np.uint8),  np.zeros(output.shape, np.uint8)])
    # image_b[temp] = (255,0,0)
    night_npy = np.zeros(temp.shape,np.uint8)
    # print(night_npy.shape)
    night_npy[temp] = 1

    # for i in range(image_b.shape[0]):
    #     for j in range(image_b.shape[1]):
    #         if image_b[i][j][1] > 95 and image_b[i][j][1] < 180:
    #             image_b[i][j] = (255, 0, 0)
    #             night_npy[i][j] = 1
    #         else:
    #             image_b[i][j] = (0, 0, 0)
    #             night_npy[i][j] = 0
    # merged_img作夜间图，night_npy为1024*1024二值数组,output作夜间海雾蓝色图
    # return night_npy,merged_img,image_b,image_g
    # return night_npy
    return night_npy,merged_img

from skimage import data,exposure
import skimage
def true_RGB(npy):
    # _npy=np.array(npy*255,np.uint8)
    _npy=npy
    B,G,R=_npy[0],_npy[1],_npy[2]
    B = skimage.util.img_as_int(B)
    G = skimage.util.img_as_int(G)
    R = skimage.util.img_as_int(R)
    img3 = cv2.merge([R, G, B])
    # img3 = exposure.adjust_log(img3, inv=True)#调整对比度
    # img3 = exposure.adjust_gamma(img3, 1.2)  # 图像调暗
    T = 0.5
    for i in range(len(img3)):
        for j in range(len(img3[0])):
            r = img3[i][j][0]
            g = img3[i][j][1]
            b = img3[i][j][2]
            # img3[i][j] = (r * 0.6, g, b)
            # if r / g > T:
            #     img3[i][j] = (g, r * 0.7, b)
            img3[i][j] = (r, g, b)
            if r / g > T:
                img3[i][j] = (g, r, b)
    # img3 = exposure.adjust_gamma(img3, 0.7)  # 图像调暗
    img3=skimage.util.img_as_ubyte(img3)
    return img3
# ***********************************
# npy_14 = hdf2np("./source/FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_20180630130000_20180630131459_4000M_V0001.HDF")
# npy_14 = hdf2np("./source/FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_20180301114500_20180301115959_4000M_V0001.HDF")
# gamma_dic = {'R': "1.0", 'G': "1.0", 'B': "1.0"}
# npy_14 = hdf2np('/Users/ssdk/Desktop/fy4a/FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_20180121000000_20180121001459_4000M_V0001.HDF')
# print(npy_14)
# b = make_RGB(npy_14)
# b=cv2.resize(b,(b.shape[0]*4,b.shape[1]*4),interpolation=cv2.INTER_NEAREST)
# cv2.imwrite("20220104180000.png",b)
# a,c = night_detect(npy_14)
# print(a.shape)
# print(np.sum(a == 1))
# c=cv2.resize(c,(b.shape[0]*4,b.shape[1]*4),interpolation=cv2.INTER_NEAREST)
# # cv2.imwrite("0522b.png",b)
# cv2.imwrite("0522c.png",c)

# t=true_RGB(npy_14)
# cv2.imwrite("t.png",t)
# **************************************
# #242,11
# #
# # npy_14 = hdf2np("./source/FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_20180301114500_20180301115959_4000M_V0001.HDF")
# # npy_15 = hdf2np("./source/FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_20180506190000_20180506191459_4000M_V0001.HDF")
# # npy_16 = hdf2np("./source/FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_20180411120000_20180411121459_4000M_V0001.HDF")
# npy_16 = hdf2np("./source/FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_20180630130000_20180630131459_4000M_V0001.HDF")
#
# print(npy_16[13-1][242][12],npy_16[12-1][242][12],npy_16[8-1][242][12])
# print(npy_16[13-1][242][11],npy_16[12-1][242][11],npy_16[8-1][242][11])
# print(npy_16[13-1][242][10],npy_16[12-1][242][10],npy_16[8-1][242][10])
# print("**************")
# lj,merged_img,a ,g = night_detect(npy_16)
#
# # res =[]
# # for i in range(merged_img.shape[0]):
# #     for j in range(merged_img.shape[1]):
# #         if merged_img[i][j][1] == 255 and merged_img[i][j][2] == 128:
# #             res.append((i,j))
# # print(res)
# # lj,merged_img1,a1,g1 = night_detect(npy_15)
# # lj,merged_img2,a2,g2 = night_detect(npy_16)
# cv2.imwrite("./test11111.png",merged_img )
# # cv2.imwrite("./test111121.png",a )
# # cv2.imwrite("./test11113.png",merged_img1 )
# # cv2.imwrite("./test111131.png",a1 )
# # cv2.imwrite("./test11114.png",merged_img2 )
# # cv2.imwrite("./test111141.png",a2 )
# ************************************
path = ("/Users/ssdk/Desktop/NAS/data/users/ssdk/fy4a/hdf")
# i = 0
# # npy_14 = hdf2np("./source/FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_20190924180000_20190924181459_4000M_V0001.HDF")
for file in os.listdir(path):
    npy_14 = hdf2np(path +"/"+ file)
    rgb=make_RGB(npy_14)
    # a,small_red = night_detect(npy_14)
    cv2.imwrite("/Users/ssdk/Desktop/NAS/data/users/ssdk/fy4a/nc/"+file.replace("HDF","png"),rgb)