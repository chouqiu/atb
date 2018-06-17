# -*- coding: utf-8 -*-

import re
import os
import socket
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from urllib.request import *
from urllib.error import *
from urllib import parse
from time import *
from random import *
import ssl
import requests
# import json
from bs4 import BeautifulSoup

ssl._create_default_https_context = ssl._create_unverified_context
socket.setdefaulttimeout(60)
info_lock = threading.Lock()
info_arr = []
download_count = 0
video_lock = threading.Lock()
video_arr = {}
video_sort = []
video_show_idx = 0
main_host="http://www.999avtb.com/"

class MyExcept(Exception):
    pass


def sort_rate():
    global video_arr
    global video_sort
    video_sort = []
    for vid in video_arr:
        rate = video_arr[vid]['rate']
        irate = int(rate.split('%')[0])
        fromidx = 0
        toidx = len(video_sort)
        mid = 0
        while toidx >= 0 and toidx > fromidx:
            mid = int(fromidx + (toidx - fromidx) / 2)
            crate = int(video_arr[video_sort[mid]]['rate'].split('%')[0])
            if crate > irate:
                fromidx = mid + 1
            elif crate < irate:
                toidx = mid - 1
            else:
                break
            mid = fromidx
            #print("%d %d %d"%(fromidx, toidx, len(video_sort)))

        video_sort.insert(mid, vid)
        #print("insert %s/%s to %d" % (rate, vid, mid))


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
        block_sz = 256 * 1024
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


# type=0: list, type=1: download
def fetch_url(arg, arg_type, isshow=False, use_req=False):
    global info_lock
    global info_arr
    global download_count
    global video_arr
    global video_lock
    # 网址
    # Accept - Language: zh - CN
    # Connection: Keep - Alive
    # Cookie: JSESSIONID=76782BCA557E307FBC7F29CB08E250FF;tk=VDAxKt94hbSfakQbTHXBgDSCDexK3E0EK7VJsIrwE7Mko1210;route=9036359bb8a8a461c164a04f8f50b252;BIGipServerotn=1290797578.38945.0000;BIGipServerpool_passport=300745226.50215.0000;current_captcha_type=Z;_jc_save_fromStation=%u5E7F%u5DDE%2CGZQ;_jc_save_toStation=%u6DF1%u5733%2CSZQ;_jc_save_fromDate=2017-10-07;_jc_save_toDate=2017-10-03;_jc_save_wfdc_flag=dc
    print("get args: %s" % (arg,))
    url = arg

    urlitems = url.split("/")
    h = urlitems[2]
    if len(urlitems) > 3:
        cgi = urlitems[3].split("?")[0]
    else:
        cgi = "/"
    print("fetch host: %s %s" % (h, cgi))

    info = {}
    info["url"] = url
    info["stat"] = 0
    info["file"] = cgi
    info["file_size"] = -1
    info["file_dl"] = 0
    info["host"] = h

    if arg_type == 1:
        info_lock.acquire()
        info["id"] = len(info_arr)
        info_arr.append(info)
        info_lock.release()

    try:
        # url = "http://www.avtb004.com/4048/"
        headers = {
            'User-Agent': 'Mozilla/5.0(Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
            'Host': h}
        # 'Accept':'text/html, application/xhtml+xml, image/jxr, */*',
        # 'Accept-Encoding':'gzip, deflate, br',
        # 'Cookie':'JSESSIONID=76782BCA557E307FBC7F29CB08E250FF;tk=VDAxKt94hbSfakQbTHXBgDSCDexK3E0EK7VJsIrwE7Mko1210;route=9036359bb8a8a461c164a04f8f50b252;BIGipServerotn=1290797578.38945.0000;BIGipServerpool_passport=300745226.50215.0000;current_captcha_type=Z;_jc_save_fromStation=%u5E7F%u5DDE%2CGZQ;_jc_save_toStation=%u6DF1%u5733%2CSZQ;_jc_save_fromDate=2017-10-07;_jc_save_toDate=2017-10-03;_jc_save_wfdc_flag=dc'}

        # 爬取结果
        down_ok = 1
        http_ok = False
        retry = 1
        data = ""
        # 请求
        if use_req == False:
            request = Request(url=url, headers=headers)

            while not http_ok and retry <= 10:
                try:
                    response = urlopen(request)
                    http_ok = True
                except HTTPError as e:
                    #print("http error: %d, wait: %d, retry: %d" % (e.code, waitSec, retry))
                    if arg_type == 1:
                        info_lock.acquire()
                        info_arr[info["id"]]["stat"] = -3
                        info_lock.release()
                    waitSec = randint(3, 10)
                    sleep(waitSec)
                finally:
                    retry = retry + 1

            if retry > 10:
                raise MyExcept("http retry fail")

            # 设置解码方式
            data = response.read()
            data = data.decode('utf-8', errors='ignore')
        else:
            while not http_ok and retry <= 10:
                try:
                    request = requests.get(url=url, headers=headers)
                    request.raise_for_status()
                    request.encoding = 'utf-8'
                    http_ok = True
                except Exception as e:
                    if arg_type == 1:
                        info_lock.acquire()
                        info_arr[info["id"]]["stat"] = -3
                        info_lock.release()
                    waitSec = randint(3, 10)
                    sleep(waitSec)
                finally:
                    retry = retry + 1

            if retry > 10:
                raise MyExcept("http retry fail")
            
            data = request.text


        # 打印结果
        soup = BeautifulSoup(data, "lxml")
        found = 0

        # 抓取视频链接
        for child in soup.find_all("source", label="360p"):
            found = found + 1
            print(child["src"])
            downrst = fetch_link(child["src"], info["id"])
            if isshow:
                print("get link %s, %d" % (downrst[0], downrst[1]))
            break

        found_list = 0
        print("")
        video_lock.acquire()
        for child in soup.find_all("a", class_="thumbnail") :
            vinfo = child['href'].split('/')
            #if len(vinfo) < 3 :
            #    break
            found_list = found_list + 1
            video_arr.update({vinfo[1]:{'name':vinfo[2]}})
            for cc in child.find_all("span", class_="video-rating") :
                video_arr[vinfo[1]].update({'rate':cc.get_text().strip()})
                break
            if isshow:
                vid = vinfo[1]
                print("%s [%s]  %s" % (vid, video_arr[vid]['rate'], video_arr[vid]['name']))

        video_lock.release()

        if found_list > 0 :
            print("get list from %s: %d" % (url, found_list))
        
        if found <= 0 and found_list <= 0 :
            print("no resource found for url %s." % (url))
            down_ok = 0


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
        print("get url %s fail2: %s" % (url, e))
    finally:
        if down_ok <= 0 and arg_type == 1 :
            info_lock.acquire()
            info_arr[info["id"]]["stat"] = -2
            fn = info_arr[info["id"]]["file"]
            info_lock.release()
            if re.match(r"\.", fn):
                os.remove(fn)
                print("remove file: %s ..." % (fn))

    info_lock.acquire()
    if download_count > 0 :
        download_count = download_count - 1
    else :
        print("thread running but counter invalid: %d" % (download_count))
    info_lock.release()


if __name__ == "__main__":
    # threads = {}
    input_sess = PromptSession(history=FileHistory("history.txt"), auto_suggest=AutoSuggestFromHistory(), enable_history_search=True)
    while True:
        user_input = input_sess.prompt("URL> ")
        if user_input == "exit" or user_input == "quit":
            print("current threads %d, exiting ..." % (download_count))
            break
        if len(user_input) > 2 :
            # print(user_input)
            if download_count >= 10:
                print("current %d threads running ,please wait..." % (download_count))
                continue
            else:
                uu = user_input
                if re.match(r"^[0-9]+$", user_input) :
                    uu = main_host + user_input
                if re.match(r"^http", uu) :
                    info_lock.acquire()
                    download_count = download_count+1
                    info_lock.release()
                    t = threading.Thread(target=fetch_url, args=(uu, 1, True))
                    t.setDaemon(True)
                    # threads[t.getName()] = 1
                    t.start()
        if user_input == 'l' or re.match(r"^list$", user_input) :
            print("fetch list ...")
            video_lock.acquire()
            video_arr = {}
            video_show_idx = 0
            video_sort = []
            video_lock.release()
            info_lock.acquire()
            download_count = download_count+3
            info_lock.release()
            t = threading.Thread(target=fetch_url, args=(main_host, 0))
            t1 = threading.Thread(target=fetch_url, args=(main_host+"recent/2/", 0))
            t2 = threading.Thread(target=fetch_url, args=(main_host+"recent/3/", 0))
            t.setDaemon(True)
            t.start()
            t1.setDaemon(True)
            t1.start()
            t2.setDaemon(True)
            t2.start()
        if re.match(r"^s ", user_input) or re.match(r"^search", user_input):
            scon = user_input.split(" ")[1]
            print("searching %s" % (scon))
            if len(scon) > 0:
                surl = main_host+"search/video/?s="+scon
                info_lock.acquire()
                download_count = download_count+3
                info_lock.release()
                t = threading.Thread(target=fetch_url, args=(surl, 0, True, True))
                t.setDaemon(True)
                t.start()
                t1 = threading.Thread(target=fetch_url, args=(surl+"&page=2", 0, True, True))
                t1.setDaemon(True)
                t1.start()
                t2 = threading.Thread(target=fetch_url, args=(surl+"&page=3", 0, True, True))
                t2.setDaemon(True)
                t2.start()
        if user_input == 'n' or re.match("^next$", user_input) :
            video_lock.acquire()
            if video_show_idx >= len(video_arr) :
                video_show_idx = 0
            print("show list from %d/%d" % (video_show_idx, len(video_arr)))

            if len(video_sort) <= 0 or len(video_arr) != len(video_sort):
                sort_rate()
                print("total sort list: %d" % (len(video_sort)))

            show_cnt = 0
            while video_show_idx < len(video_sort) and show_cnt < 10 :
                vid = video_sort[video_show_idx]
                print("%s [%s]  %s" % (vid, video_arr[vid]['rate'], video_arr[vid]['name']))
                show_cnt = show_cnt + 1
                video_show_idx = video_show_idx + 1

            video_show_idx = video_show_idx % len(video_sort)
            video_lock.release()

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

        print("current threads: %d" % (download_count))
