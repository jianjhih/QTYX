#! /usr/bin/env python
#-*- encoding: utf-8 -*-
#author 元宵大师 本例程仅用于教学目的，严禁转发和用于盈利目的，违者必究

import datetime
import os
import csv
# 邮件发送相关
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr
from tabulate import tabulate
import smtplib

g_text = """
主人好,

以下是双底形态识别概览信息，具体分析结果见《双底形态分析结果.csv》:

{table}

预祝选到牛股！

量化机器人"""

g_html = """
<html><body><p>主人好,</p>
<p>以下是双底形态识别概览信息，具体分析结果见《双底形态分析结果.csv》:</p>
{table}
<p>预祝选到牛股！</p>
<p>量化机器人</p>
</body></html>
"""

def auto_send_email(subject="", content="", attach="", syslog_obj="", **kwargs):
    """
    :param to_address: 收件箱地址
    :param subject: 邮件主题
    :param content: 邮件内容
    :param from_address: 发件箱地址
    :param password: 授权码,需要在qq邮箱中设置获取 设置教程http://service.mail.qq.com/cgi-bin/help?subtype=1&&no=1001256&&id=28
    :param server_address: 服务器地址
    :return:
    使用qq邮箱发送邮件的程序。一般用于报错提醒，需要去qq邮箱中开通密码
    """
    to_address = kwargs["to_address"]
    from_address = kwargs["from_address"]
    password = kwargs["password"]
    server_address = kwargs["server_address"]

    store_path = os.path.dirname(os.path.dirname(__file__)) + '/ConfigFiles/'

    max_try_num = 5
    try_num = 0

    while True:
        try:
            """
            if attach == "":

                # 创建一纯文字的实例
                msg = MIMEText(datetime.datetime.now().strftime("%m-%d %H:%M:%S") + '\n ' + content)
                msg["Subject"] = subject + ' ' + datetime.datetime.now().strftime("%m-%d %H:%M:%S")
                msg["From"] = from_address
                msg["To"] = ';'.join(to_address) # 接收字符串

            else:
                # 构造附件1（附件为csv格式的文本）
                with open(store_path+attach, "r", encoding='GBK') as file:
                    atttext = file.read()

                # 创建一个带附件的实例
                msg = MIMEMultipart()
                msg['Subject'] = subject + ' ' + datetime.datetime.now().strftime("%m-%d %H:%M:%S")
                msg['From'] = from_address
                msg['To'] = ';'.join(to_address) # 接收字符串

                att = MIMEText(atttext, 'base64', 'GBK')
                att["Content-Type"] = 'application/octet-stream'
                att.add_header("Content-Disposition", "attachment", filename="双底形态分析结果.csv")
                msg.attach(att)
            """
            with open(store_path + attach, 'r', encoding='GBK') as csvfile:
                spamreader = csv.reader(csvfile)
                data = list(spamreader)

            # 删除一些列信息 邮件中仅显示重要内容
            for row in data:
                row.pop(-1)
                row.pop(-1)
                row.pop(-5), row.pop(-5), row.pop(-5)
                row.pop(-5), row.pop(-5), row.pop(-5),
                row.pop(-5), row.pop(-5)

            text = g_text.format(table=tabulate(data, headers="firstrow", tablefmt="grid"))
            html = g_html.format(table=tabulate(data, headers="firstrow", tablefmt="html"))

            msg = MIMEMultipart("alternative", None, [MIMEText(text), MIMEText(html, 'html')])
            msg['Subject'] = subject + ' ' + datetime.datetime.now().strftime("%m-%d %H:%M:%S")
            msg['From'] = from_address
            msg['To'] = ';'.join(to_address)  # 接收字符串

            username = from_address
            server = smtplib.SMTP(server_address) # SMTP协议默认端口是25
            server.starttls()
            server.login(username, password)
            server.sendmail(from_address, to_address, msg.as_string())
            server.quit()
            syslog_obj.re_print("邮件发送成功...\n")
            break

        except :
            try_num += 1
            syslog_obj.re_print(f"邮件第{try_num}发送失败...\n")
            if try_num > max_try_num:
                break


