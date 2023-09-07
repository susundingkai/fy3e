import json
import pickle
from bs4 import BeautifulSoup
import demjson3
import requests
import json
from datetime import datetime
import time
import os
from  datetime import datetime,timedelta
from tqdm import tqdm
# "productID": "FY4A-_AGRI--_N_DISK_1047E_L1-_FDI-_MULT_NOM_YYYYMMDDhhmmss_YYYYMMDDhhmmss_4000M_V0001.HDF", #fy4a
# "productID": "FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_YYYYMMDDhhmmss_YYYYMMDDhhmmss_4000M_Vnnnn.HDF", #fy4b
# "FY4B-_GHI---_N_REGX_1330E_L1-_FDI-_MULT_NOM_YYYYMMDDhhmmss_YYYYMMDDhhmmss_2000M_Vnnnn.HDF"
productID="FY4B-_GHI---_N_REGX_1330E_L1-_GEO-_MULT_NOM_YYYYMMDDhhmmss_YYYYMMDDhhmmss_2000M_Vnnnn.HDF"  
sta="fy4b"
session=requests.session()
with open('login.cookies', 'rb') as f:
    session.cookies.update(pickle.load(f))
#check if login
def isLogin():
    HEADERS = {
    'Content-Type': 'application/json'}
    url="http://satellite.nsmc.org.cn/PortalSite/WebServ/CommonService.asmx/IsLogin"
    response = session.post(url,headers=HEADERS, data=json.dumps({}))
    return response.json()
#get search count
def getCount(startDate,endDate,startTime="00:00:00",endTime="23:59:59"):
    url = "http://satellite.nsmc.org.cn/PortalSite/WebServ/DataService.asmx/GetArcDataCountByProduction"

    payload = json.dumps({
    "ischecked": False,
    "productID": productID,
    "txtBeginDate": startDate,
    "txtBeginTime": startTime,
    "txtEndDate": endDate,
    "txtEndTime": endTime,
    "cbAllArea": "on",
    "converStatus": "All",
    "East_CoordValue": "",
    "West_CoordValue": "",
    "North_CoordValue": "",
    "South_CoordValue": "",
    "rdbIsEvery": "on",
    "where": ""
    })
    headers = {
    'Content-Type': 'application/json',
    'Cookie': 'userInfo=DXWEgpN7nfdL693bxyJU1RtipBVuiYN9MPyvCpyb9T3nhWdvBnabbKW6%2b9uHijI6b8bLUvIsb9u04QwGq6GMOQVsltqyFzwjpEtxoAFXNaLrfwazstbx6l%2faAsJdmBH3a7uONLkwIYK04%2b7auEIk2vb4TbIybDfkwUtsMa5FVQm6LyLl57aUVO6%2fKEU%2fhQ4KfMIuGqDCnTA%3d; .ASPXANONYMOUS=rvSZ6f992QEkAAAAZjUwODhhMzQtOTZhNi00Y2Q3LWE5MGItNDNmZmU1YmU2NjFmR7t2u_c3ZNef_sGC-sIsI7WFBio1; .ASPXAUTH=7CAF5BA3D4E97D41845658A9277AFD8457C882596C4AA6A47EB2AEE62D399D40934E66102FEA1CAC8B2F3076285F604533BBAA902B8D521FB8260F170C01444DAE87CA51C9CCE4F0A2E618389BF263B7787148A55BCA863DB51FD7DB9E290FD4D1AB14C6F22DE4DF339AA625D7B0CE58003C6D1F; ASP.NET_SessionId=en5lblcvvtpk5x4ir05l4gqe; UserLanguage=zh-CN'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    data=response.json()
    data=data["d"]
    data=demjson3.decode(data)
    return int(data[1]["count"])

#get file list 2021-02-01
def getFileList(startDate,endDate,i,startTime="00:00:00",endTime="23:59:59"):
    url = "http://satellite.nsmc.org.cn/PortalSite/WebServ/DataService.asmx/GetArcDatasByProduction"
    payload = json.dumps({
    "productID":productID,
    "txtBeginDate": startDate,
    "txtBeginTime": startTime,
    "txtEndDate": endDate,
    "txtEndTime": endTime,
    "cbAllArea": "on",
    "converStatus": "All",
    "East_CoordValue": "",
    "West_CoordValue": "",
    "North_CoordValue": "",
    "South_CoordValue": "",
    "rdbIsEvery": "on",
    "beginindex": (i*30)+1,
    "endindex": (i+1)*30,
    "sortName": "DATABEGINDATE",
    "sortOrder": "desc",
    "where": ""
    })
    headers = {
    'Content-Type': 'application/json',
    }
    response = session.post( url, headers=headers, data=payload)
    data=response.json()
    data=data["d"]
    if(data==""):
        return []
    data=demjson3.decode(data)
    return data
# with open("./1.json","r") as f:
#     data=json.load(f)
# data=data["d"]
# data=demjson3.decode(data)

#select file
def selectFile(filename):
    url = "http://satellite.nsmc.org.cn/PortalSite/WebServ/CommonService.asmx/selectOne"
    payload = {
    "filename": filename,
    "ischecked": True,
    "satellitecode": sta, #fy4a fy4b
    "datalevel": "L1"
    }
    headers = {
    'Content-Type': 'application/json',
    }
    response = session.post(url, headers=headers, data=json.dumps(payload))
    # print(response.text)
    pass
#check left #lblDayFree
def checkLeft():
    url = "http://satellite.nsmc.org.cn/PortalSite/Data/ShoppingCart.aspx"
    payload={}
    headers = {
    'Cookie': 'userInfo=DXWEgpN7nfdL693bxyJU1RtipBVuiYN9MPyvCpyb9T3nhWdvBnabbKW6%2b9uHijI6b8bLUvIsb9u04QwGq6GMOQVsltqyFzwjpEtxoAFXNaLrfwazstbx6l%2faAsJdmBH3a7uONLkwIYK04%2b7auEIk2vb4TbIybDfkwUtsMa5FVQm6LyLl57aUVO6%2fKEU%2fhQ4KfMIuGqDCnTA%3d; .ASPXANONYMOUS=rvSZ6f992QEkAAAAZjUwODhhMzQtOTZhNi00Y2Q3LWE5MGItNDNmZmU1YmU2NjFmR7t2u_c3ZNef_sGC-sIsI7WFBio1; .ASPXAUTH=7CAF5BA3D4E97D41845658A9277AFD8457C882596C4AA6A47EB2AEE62D399D40934E66102FEA1CAC8B2F3076285F604533BBAA902B8D521FB8260F170C01444DAE87CA51C9CCE4F0A2E618389BF263B7787148A55BCA863DB51FD7DB9E290FD4D1AB14C6F22DE4DF339AA625D7B0CE58003C6D1F; ASP.NET_SessionId=en5lblcvvtpk5x4ir05l4gqe; UserLanguage=zh-CN'
    }
    response = session.get( url, headers=headers, data=payload)
    soup= BeautifulSoup(response.text,"lxml")
    left=soup.select("#lblDayFree")[0].text
    left=float(left[1:-3])
    return left
def submit():
    url = "http://satellite.nsmc.org.cn/PortalSite/WebServ/CommonService.asmx/Submit"

    payload = json.dumps({
    "chkIsPushMode": False,
    "chkIsSendMail": True,
    "radioBtnlist_ftp": "0"
    })
    headers = {
    'Content-Type': 'application/json',
    }
    response = session.post(url, headers=headers, data=payload) 
if __name__=='__main__':
    root="/Users/ssdk/Desktop/NAS/data/users/ssdk/fy4e"
    file_list=os.listdir(root)
    time_list=[datetime.strptime("".join(filename.split("_")[-4:-2])[:-2],"%Y%m%d%H")  for filename in file_list]
    startDates=[time.strftime("%Y-%m-%d") for time in time_list]
    endDates=[time.strftime("%Y-%m-%d") for time in time_list]
    startTimes=[time.strftime("%H:%M:%S") for time in time_list]
    endTimes=[(time+timedelta(minutes=59,seconds=59)).strftime("%H:%M:%S") for time in time_list]

    print(isLogin())
    # startDate='2023-01-13'
    # endDate='2023-01-13'
    for i in range(len(startDates)):
        startDate=startDates[i]
        endDate =endDates[i]
        startTime=startTimes[i]
        endTime=endTimes[i]
        count=getCount(startDate,endDate,startTime=startTime,endTime=endTime)
        # print(count)
        times=(count//30)+1
        fileList=[]
        for i in range(times):
            fileList+=getFileList(startDate,endDate,i,startTime=startTime,endTime=endTime)

        for fileObj in tqdm(fileList):
            date=fileObj["DATACREATEDATE"]
            date=datetime.strptime(date,"%Y/%m/%d %H:%M:%S")
            # if(date.minute==0):
            selectFile(fileObj["ARCHIVENAME"])
        #可以先把submit注释掉，这样就会留在购物车，不会提交订单        
    submit()
        # print("Left: ",checkLeft(),"MB")
    pass