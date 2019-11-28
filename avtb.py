# -*- coding: utf-8 -*-

import re
import os
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from urllib.request import *
from urllib.error import *
#from urllib import parse
from time import *
from random import *
import requests
# import json
from bs4 import BeautifulSoup
from avtb_global import *
import sock
import time
import random

def fetch_link(url, idx, debug=0):
    file_info = url.split('/')
    file_name = file_info[-1].split('?')[0]
    file_host = file_info[2]
    print("fetching %s (%s) ..." % (file_name, file_host))

    file_size_dl = 0
    file_size = 0
    fail = 0
    while fail <= get_max_download_retry():
        headers = {
            'User-Agent': 'Mozilla/5.0(Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
            'Host': file_host,
        }
        if file_size_dl > 0:
            headers["Range"] = "bytes=%d-" % (file_size_dl,)
            if debug > 0:
                print("continue downloading %s from %d ... " % (file_name, file_size_dl))

        try:
            request = Request(url=url, headers=headers)
            u = urlopen(request)
            # file_size_dl = 0

            if fail == 0:
                file_size = int(u.info().get("Content-Length"))

            if idx >= 0:
                update_file_info(file_name, file_size, file_size_dl, idx)

            if file_size <= 0:
                raise MyExcept("fetch_link: fetch %s fail, invalid size %d" % (file_name, file_size))

            if os.path.exists(get_fullpath(file_name)) and fail <= 0:
                file_size_dl = -3
                break

            file_size_dl = write_file(file_name, file_size, file_size_dl, idx, u)

            if file_size_dl == file_size:
                break
            else:
                raise MyExcept("fetch_link: download file fail: %d/%d" % (file_size_dl/file_size))

        except Exception as e:
            fail = fail + 1
            info = get_new_file_info()
            info["stat"] = -3
            info["retry"] = fail
            update_file_info_ex(info, idx)
        finally:
            if debug > 0:
                print("waiting for retry %s/%d ..." % (file_name, fail))
            time.sleep(random.randint(3,8))

    ret = -1
    if file_size_dl == file_size and file_size > 0:
        if idx >= 0:
            update_file_stat(idx, file_size_dl, 2)
        print("%s: %d ... Done" % (file_name, file_size_dl))
        ret = file_size
    elif file_size_dl == -3:
        if idx >= 0:
            update_file_stat(idx, file_size, 3)
        print("%s: %d ... already exists" % (file_name, file_size))
        ret = 0
    else:
        print("download %s fail: retry %d" % (file_name, fail))
        ret = -1

    return [file_name, ret]


# type=0: list, type=1: download
def fetch_url(arg, arg_type, isshow=False, use_req=False, debug=0):
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

    info = get_new_file_info(url, h)

    if arg_type == 1:
        info = create_new_file_info(info)

    if not info:
        print("init file info fail: %s::%s" % (h, cgi))
        return

    get_url_fail = 0
    while get_url_fail < get_max_url_retry():
        try:
            # 爬取结果
            found = 0
            found_list = 0
            downrst = ["OK", 1]
            data = ""
            get_host = urlitems[2]
            get_path = '/'.join(urlitems[3:len(urlitems)])
            if len(get_path) == 0:
                get_path = '/'
            else:
                get_path = '/' + get_path

            # 请求
            if use_req == False:
                data = sock.request_get(get_host, get_path)
            else:
                data = sock.http_get(url, debug=0)

            print("get data len: %d" % (len(data)))

            # 打印结果
            soup = BeautifulSoup(data, "lxml")

            # 抓取视频链接
            for child in soup.find_all("source", label="360p"):
                found = found + 1
                vsrc = format_str(child["src"])
                if debug > 0 :
                    print(child["src"])
                downrst = fetch_link(child["src"], info["id"])
                if isshow:
                    print("get link %s, %d" % (downrst[0], downrst[1]))
                break

            if debug > 0 :
                print("")
            try:
                for child in soup.find_all("a", class_="thumbnail") :
                    vinfo = child['href'].split('/')
                    vid = vinfo[1]
                    vname = format_str(vinfo[2])
                    vrate = 0
                    #if len(vinfo) < 3 :
                    #    break
                    found_list = found_list + 1
                    for cc in child.find_all("span", class_="video-rating") :
                        #video_arr[vid].update({'rate':int(cc.get_text().strip().split('%')[0])})
                        vrate = int(re.findall(r"[^0-9]([0-9]+)%", cc.get_text())[0])
                        break

                    update_video_info(vid, vname, vrate)

                    if isshow:
                        print("%s [%d%%]  %s" % (vid, vrate, vname))
            except Exception as e:
                print("parse url %s fail: %s" % (arg, e))

            if found > 0 or found_list > 0 :
                if found_list > 0 :
                    print("get list from %s: %d" % (url, found_list))
                break
            else:
                #print("no resource found for url %s." % (url))
                #downrst[1] = -1
                #downrst[0] = "no resource found"
                raise MyExcept("no resource found")


                # 打印爬取网页的各类信息
                # print(type(response))
                # print(response.geturl())
                # print(response.info())
                # print(response.getcode())
        except Exception as e:
            downrst[1] = -1
            downrst[0] = e
            get_url_fail = get_url_fail + 1

        time.sleep(random.randint(1,2))

    if get_url_fail >= get_max_url_retry():
        print("Download fail: %s fetch fail, %s, file found %d, video list found %d" % (arg, downrst[0], found, found_list))
        return -1
    if downrst[1] < 0 and arg_type == 1 :
        print("Download fail: get url %s fail: %d %s" % (url, downrst[1], downrst[0]))
        fn = update_file_stat(infoidx=info["id"], stat=-2)
        if re.match(r".", fn) and os.path.exists(get_fullpath(fn)):
            os.remove(get_fullpath(fn))
            print("remove file: %s ..." % (fn))
        return -2
    return 0


def check_queue(arg, arg_type, isshow=False, use_req=False):
    is_check_queue = True
    vid = 0
    while is_check_queue:
        if arg_type == 1:
            task_lock.acquire()
            if len(task_queue) > 0:
                vid = task_queue.pop()
                arg = make_url(vid)
                print("start %s in queue, left %d" % (arg, len(task_queue)))
            else :
                print("no task in queue")
                is_check_queue = False
            task_lock.release()
            
        ret = fetch_url(arg, arg_type, isshow, use_req)
        if arg_type == 0:
            break

        if ret < 0 :
            task_lock.acquire()
            task_queue.insert(0, vid)
            print("video %d download fail, readd in queue" % (vid))
            task_lock.release()


    if get_download_count() > 0 :
        dec_download_count()
    else :
        print("thread running but counter invalid: %d" % (get_download_count()))


def run_download(argu, is_page=False):
    if is_page == True:
        print("run_download: %s" %(argu))
    else:
        print("run_download from taskqueue")
    inc_download_count()
    if is_page:
        t = threading.Thread(target=check_queue, args=(argu, 0, True, True))
    else:
        t = threading.Thread(target=check_queue, args=(argu, 1, False, True))
    t.setDaemon(True)
    # threads[t.getName()] = 1
    t.start()


if __name__ == "__main__":
    # threads = {}
    input_sess = PromptSession(history=FileHistory("history.txt"), auto_suggest=AutoSuggestFromHistory(), enable_history_search=True)
    test_host()

    while True:
        user_input = input_sess.prompt("URL> ")
        if user_input == "exit" or user_input == "quit":
            print("current threads %d, exiting ..." % (get_download_count()))
            break
        if re.match(r"^[0-9]+$", user_input) :
            task_lock.acquire()
            #task_queue.append(uu)
            task_queue.append(user_input)
            print("current %d threads running, put in queue %d..." % (get_download_count(), len(task_queue)))
            task_lock.release()
            #uu = make_url(user_input)
            # print(user_input)
            if get_download_count() >= task_currency :
                continue
            else:
                run_download("")

        if user_input == 'l' or re.match(r"^list$", user_input) :
            print("fetch list ...")
            init_video_info()
            run_download(get_main_host(), True)
            for i in range(2, max_page+1):
                run_download(get_url("recent/%d/"%(i)), True)
        if re.match(r"^s ", user_input) or re.match(r"^search", user_input):
            scon = user_input.split(" ")[1]
            print("searching %s" % (scon))
            if len(scon) > 0:
                surl = get_url("search/video/?s="+scon)
                run_download(surl, True)
                for i in range(2, max_page+1):
                    run_download(surl+"&page=%d"%(i), True)
        if user_input == 'n' or user_input == 'rn' or re.match("^next$", user_input) or re.match("^renext$", user_input) :
            do_next = 1
            if user_input == 'rn' or re.match("^renext$", user_input) :
                do_next = 0

            show_video_info(do_next)

        if re.match(r"^setc [0-9]+", user_input):
            new_sc = int(user_input.split(" ")[1])
            print("set currency: %d" % (new_sc))
            task_currency = new_sc
            left = task_currency - get_download_count() 
            if left > 0:
                for i in range(0, left):
                    uu = ""
                    task_lock.acquire()
                    if len(task_queue) > 0:
                        uu = task_queue.pop()
                        print("ready to start queue %d - %s" % (len(task_queue), uu))
                    task_lock.release()
                    if uu != "":
                        run_download(make_url(uu))
        if re.match(r"^queue$", user_input) or user_input == "q":
            show_file_info()
            print("-------------------")
            task_lock.acquire()
            qlen = len(task_queue)
            print("total %d task in queue" % (qlen))
            for i in range(0, qlen):
                vinfo = find_video_info(task_queue[i])
                if vinfo:
                    print("%s - %s" % (task_queue[i], vinfo["name"]))
                else :
                    print("%s - invalid" % (task_queue[i]))
            task_lock.release()

        if re.match(r"^showh$", user_input):
            show_host_list()
            print("-------------------")
            print("current main: %s" % get_main_host())

        if re.match(r"^seth [0-9]+", user_input):
            hid = int(user_input.split(" ")[1])
            print("current host %s" % get_main_host())
            set_main_host(hid)

        if re.match(r"^setsp ", user_input):
            nsp = user_input.split(" ")[1]
            set_store(nsp)
            print("current store path: %s" % (get_store()))

        if re.match(r"^showsp", user_input):
            print("current store path: %s" % (get_store()))
        
        if re.match(r"^help$", user_input) or user_input == "h":
            print("--- HELP MENU ---")
            print("%s --- %s" % ("setc <currency number>", "set currency for downloading"))
            print("%s --- %s" % ("queue or q", "show current tasks in queue"))
            print("%s --- %s" % ("n and rn", "show next 10 videos in the list, rn means reset index to 0"))
            print("%s --- %s" % ("search or s <keyword>", "search for keyword"))
            print("%s --- %s" % ("list or l", "get new list"))
            print("%s --- %s" % ("quit or exit", "exit console"))
            print("%s --- %s" % ("video id", "add video to downloading queue"))
            print("%s --- %s" % ("seth <id>", "set current video host"))
            print("%s --- %s" % ("showh", "show video host"))
            print("%s --- %s" % ("setsp <store path>", "set current video store path"))
            print("%s --- %s" % ("showsp", "show video store path"))

        print("------")

        #if user_input == "":

        print("current threads: %d" % (get_download_count()))
