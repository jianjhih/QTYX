#! /usr/bin/env python 
#-*- encoding: utf-8 -*- 
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import json

class Base_File_Oper():

    @staticmethod
    def load_sys_para(filename):
        with open(filename, 'r', encoding='utf-8') as load_f:
            para_dict = json.load(load_f)
        return para_dict

    @staticmethod
    def save_sys_para(filename, para_dict):
        with open(filename, "w", encoding='utf-8') as save_f:
            json.dump(para_dict, save_f, ensure_ascii=False, indent=4)

    @staticmethod
    def read_tushare_token():
        # 设置token
        with open('./ConfigFiles/token.txt', 'r', encoding='utf-8') as f:
            token = f.read()  # 读取你的token
        return token

    @staticmethod
    def read_log_trade():
        with open('./ConfigFiles/logtrade.txt', 'r', encoding='utf-8') as f:
            info = f.read()
        return info