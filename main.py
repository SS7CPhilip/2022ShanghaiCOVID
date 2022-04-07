import requests
from bs4 import BeautifulSoup
#from random import randint
import datetime
import time
import re
import math
import os
#from geopy.geocoders import BaiduV3
import csv


def bd09_to_gcj02(bd_lat, bd_lon):
    x_pi = 3.14159265358979324 * 3000.0 / 180.0
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
    gg_lng = z * math.cos(theta)
    gg_lat = z * math.sin(theta)
    return (gg_lat, gg_lng)


def Pos2Coord(full_add):
    #Add your API key as the second parameter
	url = 'http://api.map.baidu.com/geocoding/v3/?address=%s&output=json&ak=%s'%(full_add,'Your API Key')
	res = requests.get(url)
	if res.status_code==200:
		val=res.json()
		if val['status']==0:
			retVal={'lng':val['result']['location']['lng'],'lat':val['result']['location']['lat'],\
			'conf':val['result']['confidence'],'comp':val['result']['comprehension'],'level':val['result']['level']}
		else:
			retVal=None
		return retVal
	else:
		print('Cannot geocode this address:'%full_add)


def date_range(start_date):
    current_date = str(datetime.date.today())
    #current_date = time.strftime(str(datetime.date.today()), time.localtime())
    current_date = datetime.datetime.strptime(current_date, '%Y-%m-%d')
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    date_range = []
    while (current_date > start_date):
        str_date = current_date.strftime('%Y-%m-%d')
        #print(str_date)
        date_range.append(str_date)
        current_date = current_date - datetime.timedelta(days=1)
    return date_range


def get_rawdata(date_range):
    cases = {}
    for dd in date_range:
        #time.sleep(randint(3, 7))
        url = 'https://ss.shanghai.gov.cn/search?page=1&view=&contentScope=1&dateOrder=1&tr=5&dr='+str(dd)+'+%E8%87%B3+'+str(dd)+'&format=1&uid=aeb40557-eb1f-5566-6a5a-dafb05907869&sid=0000016f-12d7-2c3c-28c0-49855413294d&re=2&all=1&debug=&siteId=wsjkw.sh.gov.cn&siteArea=all&q=%E6%9C%AC%E5%B8%82%E5%90%84%E5%8C%BA%E7%A1%AE%E8%AF%8A%E7%97%85%E4%BE%8B%E3%80%81%E6%97%A0%E7%97%87%E7%8A%B6%E6%84%9F%E6%9F%93%E8%80%85%E5%B1%85%E4%BD%8F%E5%9C%B0%E4%BF%A1%E6%81%AF'
        #print(url)
        webcode = requests.get(url)
        soup = BeautifulSoup(webcode.text,features="html.parser")

        #Find the result section
        soup = soup.find('div',class_= "other")
        #print(soup)
        #soup = soup.prettify()

        #Find the link to address webpage
        soup = soup.find('a')
        #print(soup)
        soup = soup.get('href')
        #print(str(soup))

        #time.sleep(randint(3, 7))

        url_add = str(soup)
        webcode = requests.get(url_add)
        soup = BeautifulSoup(webcode.text,features="html.parser")
        soup = soup.find('div',class_="Article_content")
        if soup is None:
            soup = BeautifulSoup(webcode.text,features="html.parser")
            soup = soup.find('div',id="ivs_content")
        if soup is None:
            print('Could not find data for this date:', dd)
            continue
        text_body = soup.get_text(strip=True)

        total_stats = text_body.split("各区信息如下：")
        total_stats = re.split('已对相关居住地落实终末消毒措施。|已对相关居住地落实终末消毒措施等。|已对相关居住地落实终末消毒等措施。|已对相关居住地落实消毒等措施。',total_stats[1])
        #print(total_stats)

        district_list = ["黄浦区","徐汇区","长宁区","静安区","普陀区","虹口区","杨浦区","浦东新区","闵行区","宝山区","嘉定区","金山区","松江区","青浦区","奉贤区","崇明区"]
        dict_stats = dict.fromkeys(district_list)
        #print(str(dict_stats))
        for key in dict_stats:
            for stats in total_stats:
                is_current = (key in stats)
                if is_current is True:
                    cases_adds = stats.split("居住于")[1]
                    cases_adds = re.split('，|。|：|、|,',cases_adds)
                    cases_adds.pop(-1)
                    #print(cases_adds)
                    dict_stats[key] = cases_adds
        #print(str(dict_stats))
        cases[dd] = dict_stats
        #print(cases)
    return cases

def output(rawdata):
    cases_dict = {}
    for dd in rawdata:
        for district in rawdata[dd]:
            for add in rawdata[dd][district]:
                full_add = str(district) + str(add)
                cases_dict.setdefault(full_add,[])
                cases_dict[full_add].append(dd)
    #print(cases_dict)

    with open('Cases.csv', 'w', newline='', encoding='utf-8') as csvfile:
        header_key = ['Address', 'Date']
        new_val = csv.DictWriter(csvfile, fieldnames=header_key)

        new_val.writeheader()
        for new_k in cases_dict:
            new_val.writerow({'Address': new_k, 'Date': str(cases_dict[new_k])})

    return cases_dict

def Baidu_geocode(rawdata):
    #geolocator = BaiduV3(api_key='3xwyzf0yaQG1jAEqDGFbnzyDEVp4wnHT',timeout=1000,security_key='F6PkTgi3pp305BCK5GSU3hUvY7QwOoAA')
    geocode_dict = {}
    for dd in rawdata:
        for district in rawdata[dd]:
            for add in rawdata[dd][district]:
                full_add = '上海市' + str(district) + str(add)
                #location = geolocator.geocode(full_add, exactly_one=True)
                geocode_dict.setdefault(full_add,[])
                if geocode_dict[full_add] == []:
                    location = Pos2Coord(full_add)
                    if location is not None:
                        coord_bd = (location['lat'],location['lng'])
                        #print(coord_bd)
                        geocode_dict[full_add].append(coord_bd)
                        coord_gcj = bd09_to_gcj02(coord_bd[0],coord_bd[1])
                        #print(coord_gcj)
                        geocode_dict[full_add].append(coord_gcj)
    #print(geocode_dict)

    with open('Places.csv', 'w', newline='', encoding='utf-8') as csvfile:
        header_key = ['Address', 'Coordinates(BD_GCJ)']
        new_val = csv.DictWriter(csvfile, fieldnames=header_key)

        new_val.writeheader()
        for new_k in geocode_dict:
            new_val.writerow({'Address': new_k, 'Coordinates(BD_GCJ)': str(geocode_dict[new_k])})

    return geocode_dict



#days_list = list(range(19,31))
#Parameter is start date and the program will execute from that date to today
days_list = date_range('2022-03-19')
rawdata = get_rawdata(days_list)
cases_dict = output(rawdata)
prompt = input("Do you want to continue geocoding addresses? This will consume your Baidu quota. y/n?")
if prompt == ("y" or "Y"):
    print("OK. Geocoding...")
    geocode_dict = Baidu_geocode(rawdata)
    print('Done')
elif prompt == ("n" or "N"):
    print("OK. Stopped")
    exit()
    #os.system('pause')
else:
    print("Invalid input. Please try again.")
