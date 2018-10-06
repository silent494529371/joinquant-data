# encoding: UTF-8

from __future__ import print_function
import sys
import json
from datetime import datetime
from time import time, sleep

from pymongo import MongoClient, ASCENDING

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME

import  jqdatasdk

# 加载配置
config = open('config.json')
setting = json.load(config)

MONGO_HOST = setting['MONGO_HOST']
MONGO_PORT = setting['MONGO_PORT']
JQDATA_USER = setting['JQDATA_USER']
JQDATA_PASSWORD = setting['JQDATA_PASSWORD']
Five_MIN_DB_NAME = 'VnTrader_5Min_Db'

mc = MongoClient(MONGO_HOST, MONGO_PORT)        # Mongo连接
db = mc[Five_MIN_DB_NAME]                         # 数据库



#----------------------------------------------------------------------
def generateVtBar(symbol, time, d):
    """生成K线"""
    bar = VtBarData()
    bar.vtSymbol = symbol
    bar.symbol = symbol
    bar.open = float(d['open'])
    bar.high = float(d['high'])
    bar.low = float(d['low'])
    bar.close = float(d['close'])
    bar.date = datetime.strptime(time[0:10], '%Y-%m-%d').strftime('%Y%m%d')
    bar.time = time[11:]
    bar.datetime = datetime.strptime(bar.date + ' ' + bar.time, '%Y%m%d %H:%M:%S')
    bar.volume = d['volume']
    
    return bar

#----------------------------------------------------------------------
def downMinuteBarBySymbol(symbol, info, today, pre_trade_day):
    start = time()

    symbol_name = info['name']
    cl = db[symbol_name]
    cl.ensure_index([('datetime', ASCENDING)], unique=True)  # 添加索引

    # 在此时间段内可以获取期货夜盘数据
    #skip_paused=False get_price(security, start_date=None, end_date=None, frequency='daily', 
    #fields=None, skip_paused=False, fq='pre', count=None)
    #minute_df = jqdatasdk.get_price(symbol, start_date=pre_trade_day + " 20:30:00",end_date=today + " 20:30:00", frequency='5minute')
    minute_df = jqdatasdk.get_price(symbol, start_date=pre_trade_day + " 20:30:00",end_date=today + " 20:30:00", frequency='minute',skip_paused=True)

    # 将数据传入到数据队列当中
    for index, row in minute_df.iterrows():
        bar = generateVtBar(symbol_name, str(index), row)
        d = bar.__dict__
        flt = {'datetime': bar.datetime}
        cl.replace_one(flt, d, True)

    e = time()
    cost = (e - start) * 1000

    print(u'合约%s数据下载完成%s - %s，耗时%s毫秒' % (symbol_name, pre_trade_day, today, cost))

#----------------------------------------------------------------------
# 当日数据下载，定时任务使用
def downloadAllMinuteBar():
    jqdatasdk.auth(JQDATA_USER, JQDATA_PASSWORD)
    """下载所有配置中的合约的分钟线数据"""
    print('-' * 50)
    print(u'开始下载合约分钟线数据')
    print('-' * 50)

    today = datetime.today().date()

    trade_date_list = jqdatasdk.get_trade_days(end_date=today, count=3)

    #symbols_df = jqdatasdk.get_all_securities(types=['futures'], date=today)
    symbols_df = jqdatasdk.get_all_securities(types=['futures'], date=today)
    #symbols_df = jqdatasdk.get_dominant_future('AU', '2018-09-30') #jinsong
    #downMinuteBarBySymbol(symbols_df, row, str(today), str(trade_date_list[-2]))

    for index, row in symbols_df.iterrows():
        downMinuteBarBySymbol(index, row, str(today), str(trade_date_list[-2]))

    print('-' * 50)
    print(u'合约分钟线数据下载完成')
    print('-' * 50)
    return

def downloadDonmainMinuteBar():
    jqdatasdk.auth(JQDATA_USER, JQDATA_PASSWORD)
    """下载所有配置中的合约的分钟线数据"""
    print('-' * 50)
    print(u'开始下载合约分钟线数据')
    print('-' * 50)

    today = datetime.today().date()

    trade_date_list = jqdatasdk.get_trade_days(end_date=today, count=3)

    #symbols_df = jqdatasdk.get_all_securities(types=['futures'], date=today)
    symbols_df = jqdatasdk.get_dominant_future('AG', '2018-09-30') #jinsong
    downMinuteBarBySymbol(symbols_df,  {'name': 'AG1812'}, str(today), str(trade_date_list[-2]))

    print('-' * 50)
    print(u'合约分钟线数据下载完成')
    print('-' * 50)
    return

#----------------------------------------------------------------------
# 按日期一次性补全数据
def downloadMinuteBarByDate(start_date, end_date=datetime.today().date()):
    jqdatasdk.auth(JQDATA_USER, JQDATA_PASSWORD)
    """下载所有配置中的合约的分钟线数据"""
    print('-' * 50)
    print(u'开始下载合约分钟线数据')
    print('-' * 50)

    trade_date_list = jqdatasdk.get_trade_days(start_date=start_date, end_date=end_date)

    i = 0
    for trade_date in trade_date_list:
        if i == 0:
            i = 1
            continue

        symbols_df = jqdatasdk.get_all_securities(types=['futures'], date=trade_date)

        for index, row in symbols_df.iterrows():
            downMinuteBarBySymbol(index, row, str(trade_date_list[i]), str(trade_date_list[i-1]))

        i += 1

    print('-' * 50)
    print(u'合约分钟线数据下载完成')
    print('-' * 50)
    return


if __name__ == '__main__':
	
    #def downloadMinuteBarByDate(start_date, end_date=datetime.today().date()):
    jqdatasdk.auth(JQDATA_USER, JQDATA_PASSWORD)
    #xxx=jqdatasdk.get_dominant_future('AU','2018-09-30')
    #print xxx
    #downloadMinuteBarByDate('2018-09-30')
    #downloadAllMinuteBar();
    downloadDonmainMinuteBar()