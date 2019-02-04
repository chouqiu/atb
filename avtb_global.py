import ssl
import threading
import socket

ssl._create_default_https_context = ssl._create_unverified_context
socket.setdefaulttimeout(60)
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
max_page = 5

#main_host="http://www.999avtb.com/"
main_host="http://www.avtbq.com/"
host_list=["http://www.avtbm.com", "https://www.ppp251.com"]

store_path='.'

class MyExcept(Exception):
    pass

