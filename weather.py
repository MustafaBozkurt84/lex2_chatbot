import pandas as pd
import requests
import json
from datetime import datetime


def weather_api(city_name):
    API_key = 'c262736f349754e53e4ec4f616dedd26'
    api_url=f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_key}'
    x = requests.get(api_url)
    x=x.json()
    dict_wheather={}
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    for key, value in x['main'].items():

        dict_wheather[key]=round(value- 273.15)
    dict_wheather['city']=x['name']
    dict_wheather['pressure']=x['main']['pressure']
    dict_wheather['humidity']=x['main']['humidity']
    dict_wheather['wind']=x['wind']['speed']
    dict_wheather['sunrise']=x['sys']['sunrise']
    dict_wheather['sunrise']=x['sys']['sunset']
    dict_wheather['current_time']=current_time
    return dict_wheather