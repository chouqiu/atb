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

def sort_rate():
    global video_arr
    global video_sort
    video_sort = []
    for vid in video_arr:
        irate = video_arr[vid]['rate']
        fromidx = 0
        toidx = len(video_sort) - 1
        mid = 0
        while toidx >= 0 and toidx > fromidx:
            mid = int(fromidx + (toidx - fromidx) / 2)
            crate = int(video_arr[video_sort[mid]]['rate'])
            if crate > irate:
                fromidx = mid + 1
            elif crate < irate:
                toidx = mid - 1
            else:
                break
            mid = fromidx
            #print("%d %d %d"%(fromidx, toidx, len(video_sort)))

        if mid < len(video_sort) and video_arr[video_sort[mid]]['rate'] > irate:
            video_sort.insert(mid+1, vid)
        else:
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
    while fail <= 5:
        headers = {
            'User-Agent': 'Mozilla/5.0(Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
            'Host': file_host,
        }
        if file_size_dl > 0:
            headers["Range"] = "bytes=%d-" % (file_size_dl,)
            print("continue downloading %s from %d ... " % (file_name, file_size_dl))

        request = Request(url=url, headers=headers)
        u = urlopen(request)
        # file_size_dl = 0

        if fail == 0:
            if os.path.exists(file_name):
                file_size_dl = -3
                break
            file_size = int(u.info().get("Content-Length"))

        if idx >= 0:
            if info_arr[idx]["stat"] == 0:
                info_lock.acquire()
                info_arr[idx]["stat"] = 1
                info_arr[idx]["file_size"] = file_size
                info_arr[idx]["retry"] = 0
                info_lock.release()
                print("file size: %d" % (file_size,))

            info_lock.acquire()
            info_arr[idx]["file"] = file_name
            # info_arr[id]["file_size"] = file_size
            info_arr[idx]["file_dl"] = file_size_dl
            info_lock.release()

        if file_size <= 0:
            raise MyExcept("fetch %s fail: invalid size %d" % (file_name, file_size))

        f = open(store_path+'/'+file_name, 'ab+')
        #f.seek(file_size_dl)
        block_sz = 256 * 1024
        cnt = 0
        while True:
            try:
                buffer = u.read(block_sz)
                if not buffer:
                    raise MyExcept("read buff invalid")
            except Exception as e:
                if idx >= 0 and file_size_dl != file_size:
                    fail = fail + 1
                    info_lock.acquire()
                    info_arr[idx]["stat"] = -3
                    info_arr[idx]["retry"] = fail
                    info_lock.release()
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

            if file_size_dl > file_size:
                print("%s download size bias: %d" % (file_name, file_size_dl-file_size))
                file_size_dl = file_size
                break

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
    info["retry"] = 0

    if arg_type == 1:
        info_lock.acquire()
        info["id"] = len(info_arr)
        info_arr.append(info)
        info_lock.release()

    try:
        # 爬取结果
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
            data = sock.http_get(get_host, get_path, debug=0)

        print("get data len: %d" % (len(data)))

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
        try:
            for child in soup.find_all("a", class_="thumbnail") :
                vinfo = child['href'].split('/')
                vid = vinfo[1]
                #if len(vinfo) < 3 :
                #    break
                found_list = found_list + 1
                video_arr.update({vid:{'name':vinfo[2], 'rate':0}})
                for cc in child.find_all("span", class_="video-rating") :
                    #video_arr[vid].update({'rate':int(cc.get_text().strip().split('%')[0])})
                    video_arr[vid].update({'rate':int(re.findall(r"[^0-9]([0-9]+)%", cc.get_text())[0])})
                    break
                if isshow:
                    if 'rate' not in video_arr[vid].keys() or 'name' not in video_arr[vid].keys():
                        video_arr[vid].update({'rate':0})
                        video_arr[vid].update({'name':"NULL"})
                        print("%s invalid" % (vid))
                    else:
                        print("%s [%d%%]  %s" % (vid, video_arr[vid]['rate'], video_arr[vid]['name']))
        except Exception as e:
            print("parse url %s fail: %s" % (arg, e))
        video_lock.release()

        if found_list > 0 :
            print("get list from %s: %d" % (url, found_list))
        
        if found <= 0 and found_list <= 0 :
            print("no resource found for url %s." % (url))
            downrst[1] = -1
            downrst[0] = "no resource found"


            # 打印爬取网页的各类信息
            # print(type(response))
            # print(response.geturl())
            # print(response.info())
            # print(response.getcode())
    except Exception as e:
        downrst[1] = -1
        downrst[0] = e
        print("%s: %s fetch fail, %s" % (__name__, arg, e))
    finally:
        if downrst[1] < 0 and arg_type == 1 :
            print("get url %s fail: %d %s" % (url, downrst[1], downrst[0]))
            info_lock.acquire()
            info_arr[info["id"]]["stat"] = -2
            fn = info_arr[info["id"]]["file"]
            info_lock.release()
            if re.match(r".", fn) and os.path.exists(store_path+'/'+fn):
                s.remove(fn)
                print("remove file: %s ..." % (fn))


def check_queue(arg, arg_type, isshow=False, use_req=False):
    global info_lock
    global download_count

    is_check_queue = True
    while is_check_queue:
        fetch_url(arg, arg_type, isshow, use_req)
        if arg_type == 0:
            break
        task_lock.acquire()
        if len(task_queue) > 0:
            arg = make_url(task_queue.pop())
            print("start %s in queue, left %d" % (arg, len(task_queue)))
        else :
            print("no task in queue")
            is_check_queue = False
        task_lock.release()

    info_lock.acquire()
    if download_count > 0 :
        download_count = download_count - 1
    else :
        print("thread running but counter invalid: %d" % (download_count))
    info_lock.release()


def run_download(argu, is_page=False):
    global info_lock
    global download_count

    info_lock.acquire()
    download_count = download_count+1
    info_lock.release()
    if is_page:
        t = threading.Thread(target=check_queue, args=(argu, 0, True, True))
    else:
        t = threading.Thread(target=check_queue, args=(argu, 1, False, True))
    t.setDaemon(True)
    # threads[t.getName()] = 1
    t.start()


def make_url(vid):
    global video_arr
    
    if vid in video_arr.keys():
        return main_host + vid + "/" + video_arr[vid]['name'] + "/"
    return main_host + vid + "/"


if __name__ == "__main__":
    # threads = {}
    input_sess = PromptSession(history=FileHistory("history.txt"), auto_suggest=AutoSuggestFromHistory(), enable_history_search=True)
    while True:
        user_input = input_sess.prompt("URL> ")
        if user_input == "exit" or user_input == "quit":
            print("current threads %d, exiting ..." % (download_count))
            break
        if re.match(r"^[0-9]+$", user_input) :
            uu = make_url(user_input)
            # print(user_input)
            if download_count >= task_currency :
                task_lock.acquire()
                #task_queue.append(uu)
                task_queue.append(user_input)
                print("current %d threads running, put in queue %d..." % (download_count, len(task_queue)))
                task_lock.release()
                continue
            else:
                run_download(uu)
        if user_input == 'l' or re.match(r"^list$", user_input) :
            print("fetch list ...")
            video_lock.acquire()
            video_arr = {}
            video_show_idx = 0
            video_sort = []
            video_lock.release()
            run_download(main_host, True)
            for i in range(2, max_page+1):
                run_download(main_host+"recent/%d/"%(i), True)
        if re.match(r"^s ", user_input) or re.match(r"^search", user_input):
            scon = user_input.split(" ")[1]
            print("searching %s" % (scon))
            if len(scon) > 0:
                surl = main_host+"search/video/?s="+scon
                run_download(surl, True)
                for i in range(2, max_page+1):
                    run_download(surl+"&page=%d"%(i), True)
        if user_input == 'n' or user_input == 'rn' or re.match("^next$", user_input) or re.match("^renext$", user_input) :
            do_next = 1
            if user_input == 'rn' or re.match("^renext$", user_input) :
                do_next = 0
            video_lock.acquire()
            if video_show_idx >= len(video_arr) or do_next == 0 :
                video_show_idx = 0
            print("show list from %d/%d" % (video_show_idx, len(video_arr)))

            if len(video_sort) <= 0 or len(video_arr) != len(video_sort):
                sort_rate()
                print("total sort list: %d" % (len(video_sort)))

            show_cnt = 0
            while video_show_idx < len(video_sort) and show_cnt < 10 :
                vid = video_sort[video_show_idx]
                print("%s [%d%%]  %s" % (vid, video_arr[vid]['rate'], video_arr[vid]['name']))
                show_cnt = show_cnt + 1
                video_show_idx = video_show_idx + 1

            if show_cnt > 0:
                video_show_idx = video_show_idx % len(video_sort)
            video_lock.release()
        if re.match(r"^setc ", user_input):
            new_sc = int(user_input.split(" ")[1])
            print("set currency: %d" % (new_sc))
            task_currency = new_sc
            left = task_currency - download_count
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
            task_lock.acquire()
            qlen = len(task_queue)
            print("total %d task in queue" % (qlen))
            for i in range(0, qlen):
                vname = "invalid"
                if task_queue[i] in video_arr.keys():
                    vname = video_arr[task_queue[i]]['name']
                print("%s - %s" % (task_queue[i], vname))
            task_lock.release()

        if re.match(r"^showh$", user_input):
            hlen = len(host_list)
            print("total host: %d" % hlen)
            for i in range(0, hlen):
                print("%s - %s" % (i, host_list[i]))
            print("-------------------")
            print("current main: %s" % main_host)

        if re.match(r"^seth ", user_input):
            hlen = len(host_list)
            hid = int(user_input.split(" ")[1])
            print("current host %s" % main_host)
            if hid >= 0 and hid < hlen:
                main_host = host_list[hid]
                print("new host %s" % main_host)
            else:
                print("invalid host id: %d" % hid)

        if re.match(r"^setsp ", user_input):
            nsp = user_input.split(" ")[1]
            store_path = nsp
            print("current store path: %s" % (store_path))

        if re.match(r"^showsp", user_input):
            print("current store path: %s" % (store_path))
        
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

        if user_input == "":
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
                    tail = "%s Retry ... %d" % (tail, info["retry"])

                print("%d. %s %.1fM --- %s" % (info["id"], info["file"], info["file_size"] / 1024 / 1024, tail))
            info_lock.release()

        print("current threads: %d" % (download_count))
