import base64
import hashlib
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import json
import pickle
session = requests.session()

response = session.get("http://satellite.nsmc.org.cn/PortalSite/Sup/user/Login.aspx")
soup= BeautifulSoup(response.text,"lxml")
__EVENTTARGET=""
__EVENTARGUMENT=""
__VIEWSTATE=soup.select("#__VIEWSTATE")[0]["value"]
__VIEWSTATEGENERATOR=soup.select("#__VIEWSTATEGENERATOR")[0]["value"]
__EVENTVALIDATION=soup.select("#__EVENTVALIDATION")[0]["value"]
TextBox_UserID="susundingkai2022@163.com"
TextBox_Psw="y+cr9dU-}WG4S.UN"
TextBox_Code=0

TextBox_Psw=hashlib.md5(TextBox_Psw.encode("ascii")).hexdigest()
#获取验证码
response1=session.get("http://satellite.nsmc.org.cn/PortalSite/Sup/user/LoginGenCodeImg.aspx")

with open("./gen.gif",'wb') as f:
    f.write(response1.content)
genCodeIMG=Image.open("gen.gif")
plt.figure("记住验证码后关闭该图片！")
plt.imshow(genCodeIMG)
plt.show()
TextBox_Code=input("请输入验证码:").strip("\n")
url = "http://satellite.nsmc.org.cn/PortalSite/Sup/user/Login.aspx"

payload={"__EVENTTARGET":"",
"__EVENTARGUMENT":"",
"__VIEWSTATE":__VIEWSTATE,
"__VIEWSTATEGENERATOR":__VIEWSTATEGENERATOR,
"__EVENTVALIDATION":__EVENTVALIDATION,
"TextBox_UserID":TextBox_UserID,
"TextBox_Psw":TextBox_Psw,
"TextBox_Code":TextBox_Code,
"CheckSave":"on",
"btnOk.x":"13",
"btnOk.y":"8"
}
HEADERS = {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}
response2 = session.post( url,headers=HEADERS, data=payload)

HEADERS = {
  'Content-Type': 'application/json'}
url="http://satellite.nsmc.org.cn/PortalSite/WebServ/CommonService.asmx/IsLogin"
response3 = session.post(url,headers=HEADERS, data=json.dumps({}))
with open('login.cookies','wb') as f:
  pickle.dump(session.cookies, f)
print(response3.text)