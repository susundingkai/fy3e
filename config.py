# -*- coding:utf-8 -*-
'''
@Project     : fypy

@File        : config.py

@Modify Time :  2022/10/27 16:13   

@Author      : Lee    

@Version     : 1.0   

@Description :

'''
import os
import sys
import numpy as np
import datetime

# FY3 10度块 编码对应关系
FY3Block10CoefX = {
    "00":0.0,
    "10":10.0,
    "20":20.0,
    "30":30.0,
    "40":40.0,
    "50":50.0,
    "60":60.0,
    "70":70.0,
    "80":80.0,
    "90":90.0,
    "A0":100.0,
    "B0":110.0,
    "C0":120.0,
    "D0":130.0,
    "E0":140.0,
    "F0":150.0,
    "G0":160.0,
    "H0":170.0,
    "I0":-10.0,
    "J0":-20.0,
    "K0":-30.0,
    "L0":-40.0,
    "M0":-50.0,
    "N0":-60.0,
    "O0":-70.0,
    "P0":-80.0,
    "Q0":-90.0,
    "R0":-100.0,
    "S0":-110.0,
    "T0":-120.0,
    "U0":-130.0,
    "V0":-140.0,
    "W0":-150.0,
    "X0":-160.0,
    "Y0":-170.0,
    "Z0":-180.0,
}

FY3Block10CoefY = {
    "00":  10.0,
    "10":  20.0,
    "20":  30.0,
    "30":  40.0,
    "40":  50.0,
    "50":  60.0,
    "60":  70.0,
    "70":  80.0,
    "80":  90.0,
    "90":   0.0,
    "A0": -10.0,
    "B0": -20.0,
    "C0": -30.0,
    "D0": -40.0,
    "E0": -50.0,
    "F0": -60.0,
    "G0": -70.0,
    "H0": -80.0,
}


ProdInfo = {
    'FY3D' :{
        'MERSI' : {
            'CLA': {
                'sdsname': ['Global High Cloud Amount Day', 'Global High Cloud Amount Night'],
            },
            'CLM': {
                'sdsname': ['CLM_DAILY_D', 'CLM_DAILY_N',
                            'MERSI_NDVI_D', 'MERSI_NDVI_N'],
            },
            'GFR': {
                'sdsname': ['FIRES'],
            },
            'LST': {
                'sdsname': ['MERSI_25Km_LST_D', 'MERSI_25Km_LST_N',
                            'MERSI_1Km_LST_D', 'MERSI_1Km_LST_N',
                            'MERSI_obt_LST_D', 'MERSI_obt_LST_N'],
            },
            'NDVI': {
                'sdsname': ['5KM_NDVI', '250m NDVI'],
            },
            'NVI': {
                'sdsname': ['5KM_NDVI', '250m NDVI'],
            },
            'PWV': {
                'sdsname': ['MERSI_PWV'],
            },
            'SST': {
                'sdsname': ['sea_surface_temperature'],
            },
            'SIC': {
                'sdsname': ['Daily_Sea_Ice_Both', 'Both'],
            },
            'TPW': {
                'sdsname': ['MERSI_TPW', 'MERSI_DAY_TPWSDS', 'MERSI_NIGHT_TPWSDS'],
            },
        },
        'MWRI'  : {
            'CLW': {
                'sdsname': [''],
            },
            'MRR': {
                'sdsname': ['RainRate'],
            },
            'SWE': {
                'sdsname': ['SWE_Northern_Daily', 'SWE_Southern_Daily'],
            },
            'SWS': {
                'sdsname': ['SWS_ORBIT', 'SWS_Ascending', 'SWS_Descending'],
            },
        },
        'MWHS'  : {
            'RDT': {
                'sdsname': ['Rain Detection'],
            },
        },
        'TSHS' : {
            'AVP': {
                'sdsname': ['/DATA/TSHS_AT_Prof', '/DATA/TSHS_AH_Prof',
                            '/GEO/Latitude','/GEO/Longitude'],
            },
        },
        'GNOS' : {
            'ATP' : {
                'sdsname': ['Temp'],
            }
        },
    },
    'FY4A':{
        'AGRI' : {
            'CIX': {
                'sdsname': ['Convective_Initiation'],
            },
            'CLM': {
                'sdsname': ['CLM'],
            },
            'CLP': {
                'sdsname': ['CLP'],
            },
            'CLT': {
                'sdsname': ['CLT'],
            },
            'CTH': {
                'sdsname': ['CTH'],
            },
            'CTP': {
                'sdsname': ['CTP'],
            },
            'CTT': {
                'sdsname': ['CTT'],
            },
            'DSD': {
                'sdsname': ['DST'],
            },
            'FHS': {
                'sdsname': ['FPA'],
            },
            'FOG': {
                'sdsname': ['FOG'],
            },
            'LST': {
                'sdsname': ['LST'],
            },
            'SST': {
                'sdsname': ['SST'],
            },
            'QPE': {
                'sdsname': ['Precipitation'],
            },
            'SNC': {
                'sdsname': ['SNC'],
            },
        },
        'LMI' : {
            'LMIE': {
                'sdsname': [''],
            },
            'LMIG': {
                'sdsname': [''],
            },
        },
        'GIIRS' : {
            'AVP': {
                'sdsname': ['AT_Prof'],
            },
        }
    }
}