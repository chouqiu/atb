import re
import ssl
import threading
import sock

ssl._create_default_https_context = ssl._create_unverified_context
info_lock = threading.Lock()
info_arr = []
download_count = 0
video_lock = threading.Lock()
video_arr = {}
video_sort = []
video_show_idx = 0
task_lock = threading.Lock()
task_queue = []
task_currency = 1
max_page = 20
max_download_retry = 30
max_url_retry = 3

#main_host="http://www.999avtb.com/"
main_host = 0
host_list = ["http://www.avtb0077.com", "http://www.avtbdizhi.com"]

store_path='.'

def show_video_info(do_next):
    global video_arr
    global video_lock
    global video_show_idx
    global video_sort
    
    video_lock.acquire()
    if video_show_idx >= len(video_arr) or do_next == 0 :
        video_show_idx = 0
    print("show list from %d/%d" % (video_show_idx, len(video_arr)))

    if len(video_sort) <= 0 or len(video_arr) != len(video_sort):
        sort_rate(debug=0)
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

def find_video_info(vidx):
    global video_lock
    global video_arr
    vinfo = False
    video_lock.acquire()
    if vidx in video_arr.keys():
        vinfo = video_arr[vidx]
    video_lock.release()
    return vinfo

def init_video_info():
    global video_arr
    global video_lock
    global video_show_idx
    global video_sort

    video_lock.acquire()
    video_arr = {}
    video_show_idx = 0
    video_sort = []
    video_lock.release()

def update_video_info(vid, vname, vrate):
    global video_arr
    global video_lock

    video_lock.acquire()
    video_arr.update({vid:{'name':vname, 'rate':0}})
    video_arr[vid].update({'rate':vrate})
    video_lock.release()


def show_file_info():
    global info_lock
    global info_arr

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


def get_new_file_info(url="-", host="-"):
    info = {}
    info["url"] = url
    info["stat"] = 0
    info["file_id"] = 0
    info["file"] = "NA"
    info["file_size"] = -1
    info["file_dl"] = 0
    info["host"] = host
    info["retry"] = 0
    return info

def create_new_file_info(info):
    global info_arr
    global info_lock

    if "file_size" not in info.keys():
        print("create_new_file_info: invalid info struct")
        return False

    info_lock.acquire()
    info["id"] = len(info_arr)
    info_arr.append(info)
    info_lock.release()
    return info

def update_file_stat(infoidx, file_size=-1, stat=0):
    global info_arr
    global info_lock

    fn = "NULL"
    info_lock.acquire()
    if infoidx >=0 and infoidx < len(info_arr):
        if file_size >= 0:
            info_arr[infoidx]["file_dl"] = file_size
        info_arr[infoidx]["stat"] = stat 
        fn = info_arr[infoidx]["file"]
    else:
        print("update_file_stat: invalid file info index: %d stat %d" % (infoidx, stat))
        fn = ""
    info_lock.release()

    return fn

def update_file_info_ex(info, infoidx):
    global info_arr
    global info_lock

    if infoidx < 0 or infoidx >= len(info_arr):
        print("update_file_info_ex: invalid info index %d" % (infoidx))
        return False

    info_lock.acquire()
    if info["file"] != "NA":
        info_arr[infoidx]["file"] = info["file"]
    if info["file_size"] >= 0:
        info_arr[infoidx]["file_size"] = info["file_size"]
    if info["stat"] != 0:
        info_arr[infoidx]["stat"] = info["stat"]
    if info["file_id"] > 0:
        info_arr[infoidx]["file_id"] = info["file_id"]
    if info["file_dl"] > 0:
        info_arr[infoidx]["file_dl"] = info["file_dl"]
    if info["retry"] > 0:
        info_arr[infoidx]["retry"] = info["retry"]
        
    info_lock.release()

def update_file_info(file_name, file_size, file_size_dl, infoidx):
    global info_arr
    global info_lock

    if info_arr[infoidx]["stat"] == 0:
        info_lock.acquire()
        info_arr[infoidx]["stat"] = 1
        info_arr[infoidx]["file_size"] = file_size
        info_arr[infoidx]["retry"] = 0
        info_lock.release()
        print("file size: %d" % (file_size,))

    info_lock.acquire()
    info_arr[infoidx]["file"] = file_name
    # info_arr[id]["file_size"] = file_size
    info_arr[infoidx]["file_dl"] = file_size_dl
    info_lock.release()

def write_file(file_name, file_size, file_size_dl, infoidx, urlsock):
    global info_arr
    global info_lock

    f = open(get_fullpath(file_name), 'ab+')
    #f.seek(file_size_dl)
    block_sz = 256 * 1024
    cnt = 0
    while True:
        try:
            buffer = urlsock.read(block_sz)
            if not buffer:
                raise MyExcept("read buff invalid")
        except Exception as e:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        if infoidx >= 0 and cnt % 30 == 0:
            # print("%s: %d/%d  %.2f%%" % (file_name, file_size_dl, file_size, file_size_dl*100/file_size))
            info = get_new_file_info()
            info["file_dl"] = file_size_dl
            info["stat"] = 1
            update_file_info_ex(info, infoidx)

        cnt = cnt + 1

        if file_size_dl > file_size:
            print("%s download size bias: %d" % (file_name, file_size_dl-file_size))
            file_size_dl = file_size
            break

    f.close()
    return file_size_dl


def get_download_count():
    global download_count
    return download_count;

def inc_download_count():
    global download_count
    info_lock.acquire()
    download_count = download_count + 1
    info_lock.release()

def dec_download_count():
    global download_count
    info_lock.acquire()
    download_count = download_count - 1
    info_lock.release()

def test_host():
    global host_list
    
    # HTTP/1.1 301 Moved Permanently
    # Server: nginx/1.13.7
    # Date: Mon, 18 Mar 2019 10:14:37 GMT
    # Content-Type: text/html
    # Content-Length: 185
    # Connection: keep-alive
    # Location: http://www.avtbu.com/

    mod301 = re.compile(r"Location: (http.+?)[\r\n]")
    mod200 = re.compile(r"HTTP/1\.1 ([0-9]*) ")

    for hid in range(len(host_list)):
        msg = sock.http_get(host_list[hid], debug=0)
        hcode = mod200.findall(msg)

        if not hcode:
            print("host [%s] ... fail" % (host_list[hid]))
            continue

        if re.match(r"^3[0-9][0-9]$", hcode[0]):
            newurl = mod301.findall(msg)
            if newurl:
                print("host [%s] %s ... redirect to %s" % (host_list[hid], hcode[0], newurl[0]))
                host_list[hid] = newurl[0]
            else:
                print("host [%s] %s ... not find redirect url" % (host_list[hid], hcode[0]))
        elif hcode[0] == "200":
            print("host [%s] ... OK" % (host_list[hid]))
            continue
        else:
            print("host [%s] ... code %s" % (host_list[hid], hcode[0]))

def get_main_host():
    global main_host
    global host_list
    return host_list[main_host]

def set_main_host(id):
    global main_host
    global host_list
    
    if id >= 0 and id < len(host_list):
        main_host = id
        print("main host change to: %s" % (get_main_host()))
    else:
        print("invalid host id")

def show_host_list():
    global host_list
    for hid in range(len(host_list)):
        print("%d. %s" % (hid, host_list[hid]))

def get_url(cgi):
    return get_main_host() + "/" + cgi;

def format_str(str):
    return re.sub(r"[ \t\r\n]+", "", str)

def get_fullpath(fname):
    global store_path
    return store_path+'/'+fname

def get_store():
    global store_path
    return store_path

def set_store(path):
    global store_path
    if not path:
        path = "./"
    store_path = path

def make_url(vid):
    global video_arr
    
    if vid in video_arr.keys():
        return get_url(vid+"/"+video_arr[vid]['name']+"/")
    return get_url(vid+"/")

def get_max_download_retry():
    global max_download_retry
    return max_download_retry

def get_max_url_retry():
    global max_url_retry
    return max_url_retry

def sort_rate(debug=0):
    global video_arr
    global video_sort
    video_sort = []
    if debug > 0:
        print("sort_rate debug: total %d" % (len(video_arr)))

    for vid in video_arr:
        irate = video_arr[vid]['rate']
        fromidx = 0
        toidx = len(video_sort) - 1
        mid = 0
        if debug > 0:
            print("sort %s/%d" % (vid, len(video_arr)))

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
        if debug > 0:
            print("insert %s/%s to %d" % (rate, vid, mid))


class MyExcept(Exception):
    pass

