#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

from collections import OrderedDict
from ApiData.Tushare import basic_code_list

class ManageCodeTable:
    # A股指数代码
    indexes = OrderedDict([
                        ('上证指数', 'sh.000001'),
                        ('深证成指', 'sz.399001'),
                        ('创业板指', 'sz.399006'),
                        ('中小板指', 'sz.399005'),
                        ])

    def __init__(self, syslog_obj):

        self._stock_codes_table = {}
        self.syslog = syslog_obj

    def update_stock_code(self):
        # A股全市场股票代码
        self.syslog.re_print("从TuSharePro获取股票基本信息...\n")

        code_group = basic_code_list(['ts_code', 'name'])

        if code_group.empty != True:

            for index, row in code_group.iterrows():
                num, sym = row["ts_code"].lower().split(".")
                bs_code = sym + "." + num
                self._stock_codes_table[row["name"]] = bs_code
        else:
            self.syslog.re_print("从TuSharePro获取股票基本信息异常...\n")
            raise AttributeError('股票基本信息为空!!!检查tushare的pro.stock_basic接口')

        self.syslog.re_print("从TuSharePro获取股票基本信息成功!\n")

    def refresh_stock_code(self):
        pass

    @property
    def stock_codes(self):
        return self._stock_codes_table

    @property # 知识点： @property装饰器负责把一个方法变成属性调用
    def stock_all_codes(self):
        """
        返回所有个股和大盘指数
        """
        return dict(self.stock_codes, **self.indexes)

    def get_code(self, name):
        return self.stock_all_codes[name]

    def get_name(self, code):
        for name, code_ in self.stock_all_codes.items():
            if code_ == self.conv_code(code):
                return name
        return None

    def conv_code(self, code):

        if code.find('.') == 6: # tushare的代码格式
            num, sym = code.lower().split(".")
            bs_code = sym + "." + num
            return bs_code

        elif code.find('.') == -1: # 正常代码格式
            if code[0] == '6':
                bs_code = "sh."+code
            else:
                bs_code = "sz." + code
            return bs_code
        else:
            return code
