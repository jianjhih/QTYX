#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import requests
import time
import pandas as pd
from datetime import datetime
from io import StringIO

def get_content_from_internet(url, max_try_num = 10, sleep_time = 5):
	"""
	从网页爬取数据
	@param:url
	@param:max_try_num
	@param:sleep_time
	@return:返回爬取的网页内容
	"""
	is_success = False
	for i in range(max_try_num):
		try:
			content = requests.get(url, timeout = 30)
			content.encoding = 'GBK'
			is_success = True
			break
		except Exception as e:
			print('第{}次下载数据报错,请检查'.format(i+1))
			time.sleep(sleep_time)

	if is_success:
		return content.text.strip()

def download_stock_hist_from_netease(stock, start = '19900101', end = datetime.now().strftime('%Y%m%d')):
    """
    根据股票代码，从网易财经下载股票历史行情数据
    :param stock: 单支股票的代码 sz000001
    :param start: 历史行情数据开始时间，默认'19900101'
    :param end: 历史行情数据结束时间，默认当天
    :return df: 历史行情DataFrame
    """
    stock_type = stock[0:2]
    stock_symbol = stock[2:8]

    code = '0' + stock_symbol if stock_type == 'sh' else '1' + stock_symbol
    url = 'http://quotes.money.163.com/service/chddata.html?code={0}&start={1}&end={2}&fields=TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER;TCAP;MCAP'.format(code, start, end)
    content = get_content_from_internet(url)
    content = StringIO(content)
    df = pd.read_csv(content, parse_dates = ["日期"], na_values = 'None')
    df['股票代码'] = df['股票代码'].str.lstrip("'")
    df['股票代码'] = stock_type.lower() + df['股票代码']
    df.sort_values(by = ['日期'], ascending = True, inplace = True)
    df.reset_index(drop = True, inplace = True)
    return df
