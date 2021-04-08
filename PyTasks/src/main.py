import os
import sys
import logging
import time
from datetime import datetime
import pytz
import schedule
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

import Weather
import Slack
import Shinobi


##
## Config
##

# Logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s-%(levelname)s: %(message)s')

# Initialize Influx Client
token = os.environ['TOKEN']
org = os.environ['ORG']
bucket = os.environ['BUCKET']

client = InfluxDBClient(url=os.environ['DB_HOST'], token=token)
write_api = client.write_api(write_options=SYNCHRONOUS)
hostname = os.environ['HOSTNAME']

##
## Current Weather
##

def PingCurrentWeather():
    logging.info('pinging weather api')
    current_weather = Weather.FetchCurrentWeather()
    dt = datetime.fromtimestamp(current_weather['dt']).astimezone(pytz.utc)
    logging.info(dt)
    for key, value in Weather.ParseCurrentWeather(current_weather).items():
        point = Point(key).tag("host", hostname).field("value", value).time(dt, WritePrecision.S)
        write_api.write(bucket, org, point)


PingCurrentWeather()
schedule.every(5).minutes.do(PingCurrentWeather)

##
## Forecast
##

def PingForecast():
    logging.info('pinging forecast')
    forecast = Weather.FetchForecast()
    status = Weather.CheckForecast(forecast)
    # Send status to slack
    response = Slack.SendMessage(message='2 day Forecast:\n' + status)

PingForecast()
schedule.every().day.at("09:00").do(PingForecast)
schedule.every().day.at("18:00").do(PingForecast)


##
## Shinobi (CCTV)
##

def PingShinobi():
    logging.info('pinging forecast')
    image_loc = Shinobi.GetMonitorImage('tFQOqEJbXK', 'QqMhCbk4hz')
    Slack.UploadFile(image_loc, 'test.jpg')

PingShinobi()
schedule.every().day.at("09:00").do(PingForecast)
schedule.every().day.at("18:00").do(PingForecast)


while True:
    try:
        schedule.run_pending()
    except Exception as e:
        logging.exception(e)
    time.sleep(60) # wait one minute
