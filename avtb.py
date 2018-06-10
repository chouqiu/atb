# -*- coding: utf-8 -*-

import os
import socket
import threading
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from urllib.request import *
from urllib.error import *
from time import *
from random import *
import ssl
# import json
from bs4 import BeautifulSoup

ssl._create_default_https_context = ssl._create_unverified_context
socket.setdefaulttimeout(60)
info_lock = threading.Lock()
info_arr = []


class MyExcept(Exception):
    pass


def fetch_link(url, idx):
    file_info = url.split('/')
    file_name = file_info[-1].split('?')[0]
    file_host = file_info[2]
    print("fetching %s (%s) ..." % (file_name, file_host))

    file_size_dl = 0
    file_size = 0
    fail = 0
    while fail <= 8:
        headers = {
            'User-Agent': 'Mozilla/5.0(Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
            'Host': file_host,
        }
        if file_size_dl > 0:
            headers["Range"] = "bytes=%d-" % (file_size_dl,)

        request = Request(url=url, headers=headers)
        u = urlopen(request)
        file_size = int(u.info().get("Content-Length"))
        # file_size_dl = 0

        if idx >= 0:
            if info_arr[idx]["stat"] == 0:
                info_lock.acquire()
                info_arr[idx]["stat"] = 1
                info_arr[idx]["file_size"] = file_size
                info_lock.release()
                print("file size: %d" % (file_size,))

            info_lock.acquire()
            info_arr[idx]["file"] = file_name
            # info_arr[id]["file_size"] = file_size
            info_arr[idx]["file_dl"] = file_size_dl
            info_lock.release()

        if file_size <= 0:
            raise MyExcept("fetch %s fail: invalid size %d" % (file_name, file_size))

        if fail == 0 and os.path.exists(file_name):
            file_size_dl = -3
            break

        f = open(file_name, 'wb')
        f.seek(file_size_dl)
        block_sz = 4 * 1024 * 1024
        cnt = 0
        while True:
            try:
                buffer = u.read(block_sz)
            except Exception as e:
                if idx >= 0 and file_size_dl != file_size:
                    info_lock.acquire()
                    info_arr[idx]["stat"] = -3
                    info_lock.release()
                    fail = fail + 1
                break

            if not buffer:
                break

            file_size_dl += len(buffer)
            f.write(buffer)
            if idx >= 0 and cnt % 30 == 0:
                # print("%s: %d/%d  %.2f%%" % (file_name, file_size_dl, file_size, file_size_dl*100/file_size))
                info_lock.acquire()
                info_arr[idx]["file_dl"] = file_size_dl
                info_arr[idx]["stat"] = 1
                info_lock.release()

            cnt = cnt + 1

        f.close()
        if file_size_dl == file_size:
            break

    ret = -1
    if file_size_dl == file_size:
        if idx >= 0:
            info_lock.acquire()
            info_arr[idx]["file_dl"] = file_size_dl
            info_arr[idx]["stat"] = 2
            info_lock.release()
        print("%s: %d ... Done" % (file_name, file_size_dl))
        ret = file_size
    elif file_size_dl == -3:
        if idx >= 0:
            info_lock.acquire()
            info_arr[idx]["file_dl"] = file_size
            info_arr[idx]["stat"] = 3
            info_lock.release()
        print("%s: %d ... already exists" % (file_name, file_size))
        ret = 0
    else:
        print("down fail: %d" % (fail,))
        ret = -1

    return [file_name, ret]


def down_file(url, id):
    file_info = url.split('/')
    file_name = file_info[-1].split('?')[0]
    file_host = file_info[2]
    print("downloading %s (%s) ..." % (file_name, file_host))

    file_size_dl = 0
    file_size = 0
    fail = 0
    while fail <= 8:
        headers = {
            'User-Agent': 'Mozilla/5.0(Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
            'Host': file_host,
            }
        if file_size_dl > 0:
            headers["Range"] = "bytes=%d-" % (file_size_dl,)

        request = Request(url=url, headers=headers)
        u = urlopen(request)
        file_size = int(u.info().get("Content-Length"))
        # file_size_dl = 0

        if info_arr[id]["stat"] == 0:
            info_lock.acquire()
            info_arr[id]["stat"] = 1
            info_arr[id]["file_size"] = file_size
            info_lock.release()
            print("file size: %d" % (file_size,))

        info_lock.acquire()
        info_arr[id]["file"] = file_name
        # info_arr[id]["file_size"] = file_size
        info_arr[id]["file_dl"] = file_size_dl
        info_lock.release()

        if file_size <= 0:
            raise MyExcept("down fail: invalid size %d" % (file_size))

        if fail == 0 and os.path.exists(file_name):
            file_size_dl = -3
            break

        f = open(file_name, 'wb')
        f.seek(file_size_dl)
        block_sz = 64 * 1024
        cnt = 0
        while True:
            try:
                buffer = u.read(block_sz)
            except Exception as e:
                if file_size_dl != file_size:
                    info_lock.acquire()
                    info_arr[id]["stat"] = -3
                    info_lock.release()
                    fail = fail + 1
                break

            if not buffer:
                break

            file_size_dl += len(buffer)
            f.write(buffer)
            if cnt % 30 == 0:
                # print("%s: %d/%d  %.2f%%" % (file_name, file_size_dl, file_size, file_size_dl*100/file_size))
                info_lock.acquire()
                info_arr[id]["file_dl"] = file_size_dl
                info_arr[id]["stat"] = 1
                info_lock.release()

            cnt = cnt + 1

        f.close()
        if file_size_dl == file_size:
            break

    if file_size_dl == file_size:
        info_lock.acquire()
        info_arr[id]["file_dl"] = file_size_dl
        info_arr[id]["stat"] = 2
        info_lock.release()
        print("%s: %d ... Done" % (file_name, file_size_dl))
    elif file_size_dl == -3:
        info_lock.acquire()
        info_arr[id]["file_dl"] = file_size
        info_arr[id]["stat"] = 3
        info_lock.release()
        print("%s: %d ... already exists" % (file_name, file_size))
    else:
        raise MyExcept("down fail: %d" % (fail))


def fetch_url(args):
    # 网址
    # Accept - Language: zh - CN
    # Connection: Keep - Alive
    # Cookie: JSESSIONID=76782BCA557E307FBC7F29CB08E250FF;tk=VDAxKt94hbSfakQbTHXBgDSCDexK3E0EK7VJsIrwE7Mko1210;route=9036359bb8a8a461c164a04f8f50b252;BIGipServerotn=1290797578.38945.0000;BIGipServerpool_passport=300745226.50215.0000;current_captcha_type=Z;_jc_save_fromStation=%u5E7F%u5DDE%2CGZQ;_jc_save_toStation=%u6DF1%u5733%2CSZQ;_jc_save_fromDate=2017-10-07;_jc_save_toDate=2017-10-03;_jc_save_wfdc_flag=dc

    url = args
    h = ""
    try:
        h = url.split('/')[2]
    except Exception as e:
        print("url %s invalid." % (url,))
        return

    info = {}
    info["url"] = url
    info["host"] = h
    info["stat"] = 0
    info["file"] = "NULL"
    info["file_size"] = -1
    info["file_dl"] = 0
    info_lock.acquire()
    info["id"] = len(info_arr)
    info_arr.append(info)
    info_lock.release()

    print("fetch host: %s" % (h))
    # url = "http://www.avtb004.com/4048/"
    headers = {
        'User-Agent': 'Mozilla/5.0(Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
        'Host': h}
    # 'Accept':'text/html, application/xhtml+xml, image/jxr, */*',
    # 'Accept-Encoding':'gzip, deflate, br',
    # 'Cookie':'JSESSIONID=76782BCA557E307FBC7F29CB08E250FF;tk=VDAxKt94hbSfakQbTHXBgDSCDexK3E0EK7VJsIrwE7Mko1210;route=9036359bb8a8a461c164a04f8f50b252;BIGipServerotn=1290797578.38945.0000;BIGipServerpool_passport=300745226.50215.0000;current_captcha_type=Z;_jc_save_fromStation=%u5E7F%u5DDE%2CGZQ;_jc_save_toStation=%u6DF1%u5733%2CSZQ;_jc_save_fromDate=2017-10-07;_jc_save_toDate=2017-10-03;_jc_save_wfdc_flag=dc'}

    # 请求
    request = Request(url=url, headers=headers)

    # 爬取结果
    down_ok = 1
    try:
        http_ok = False
        retry = 1
        while not http_ok and retry <= 10:
            try:
                response = urlopen(request)
                http_ok = True
            except HTTPError as e:
                waitSec = randint(3, 10)
                print("http error: %d, wait: %d, retry: %d" % (e.code, waitSec, retry))
                sleep(waitSec)
            finally:
                retry = retry + 1

        if retry > 10:
            return

        data = response.read()

        # 设置解码方式
        data = data.decode('utf-8', errors='ignore')

        # 打印结果
        soup = BeautifulSoup(data, "lxml")
        for child in soup.find_all("source", label="360p"):
            print(child["src"])
            fetch_link(child["src"], info["id"])
            break

            # 打印爬取网页的各类信息
            # print(type(response))
            # print(response.geturl())
            # print(response.info())
            # print(response.getcode())
    except MyExcept as e:
        down_ok = 0
        print("get url %s fail: %s" % (url, e))
    except Exception as e:
        down_ok = 0
        print("get url %s fail." % (url,))
    finally:
        if down_ok <= 0:
            info_lock.acquire()
            info_arr[info["id"]]["stat"] = -2
            fn = info_arr[info["id"]]["file"]
            info_lock.release()
            if fn != "NULL":
                os.remove(fn)
                print("remove fail: %s ..." % (fn))


if __name__ == "__main__":
    # threads = {}
    while True:
        user_input = prompt("URL> ", history=FileHistory("history.txt"), auto_suggest=AutoSuggestFromHistory())
        if user_input == "exit" or user_input == "quit":
            print("current threads %d, exiting ..." % (threading.active_count()))
            break
        if user_input:
            # print(user_input)
            if threading.active_count() >= 10:
                print("current %d threads running ,please wait..." % (threading.active_count()))
                continue
            else:
                t = threading.Thread(target=fetch_url, args=(user_input,))
                t.setDaemon(True)
                # threads[t.getName()] = 1
                t.start()

        info_lock.acquire()
        for info in info_arr:
            tail = "%.1f%%" % (info["file_dl"] * 100 / info["file_size"])
            if info["stat"] == 2:
                tail = "Done"
            elif info["stat"] == 3:
                tail = "Exists"
            elif info["stat"] == -2:
                tail = "Fail"
            elif info["stat"] == -3:
                tail = "%s Retry .." % (tail)

            print("%d. %s %.1fM --- %s" % (info["id"], info["file"], info["file_size"] / 1024 / 1024, tail))
        info_lock.release()

        print("current threads: %d" % (threading.active_count()))
