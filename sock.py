import requests
import socket
import struct
from urllib.request import *
from urllib.error import *
from avtb_global import *

socket.setdefaulttimeout(10)

#socket.socket(socket_family,socket_type,protocal=0)
#socket_family 可以是 AF_UNIX 或 AF_INET。socket_type 可以是 SOCK_STREAM 或 SOCK_DGRAM。protocol 一般不填,默认值为 0。

# url = "http://www.avtb004.com/4048/"
#headers = {
#    'User-Agent': 'Mozilla/5.0(Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
#    'Host': h}
# 'Accept':'text/html, application/xhtml+xml, image/jxr, */*',
# 'Accept-Encoding':'gzip, deflate, br',
# 'Cookie':'JSESSIONID=76782BCA557E307FBC7F29CB08E250FF;tk=VDAxKt94hbSfakQbTHXBgDSCDexK3E0EK7VJsIrwE7Mko1210;route=9036359bb8a8a461c164a04f8f50b252;BIGipServerotn=1290797578.38945.0000;BIGipServerpool_passport=300745226.50215.0000;current_captcha_type=Z;_jc_save_fromStation=%u5E7F%u5DDE%2CGZQ;_jc_save_toStation=%u6DF1%u5733%2CSZQ;_jc_save_fromDate=2017-10-07;_jc_save_toDate=2017-10-03;_jc_save_wfdc_flag=dc'}

global_headers = {}
global_http_buffer_len = 40960

def request_get(host, path, debug=0):
    http_ok = False
    retry = 1

    global_headers = {'Host': host}
    request = Request(url="https://%s/%s"%(host,path), headers=global_headers)

    while not http_ok and retry < 10:
        try:
            response = urlopen(request)
            http_ok = True
        except HTTPError as e:
            #print("http error: %d, wait: %d, retry: %d" % (e.code, waitSec, retry))
            if arg_type == 1:
                info_lock.acquire()
                info_arr[info["id"]]["stat"] = -3
                info_arr[info["id"]]["retry"] = retry
                info_lock.release()
            waitSec = randint(3, 10)
            sleep(waitSec)
        finally:
            retry = retry + 1

    if retry >= 10:
        raise MyExcept("http retry fail")

    # 设置解码方式
    data = response.read()
    data = data.decode('utf-8', errors='ignore')
    return data

def urllib_get(url, host, path, debug=0):
    http_ok = False
    retry = 1
    global_headers = {'Host': host}

    while not http_ok and retry < 10:
        try:
            request = requests.get(url=url, headers=global_headers, verify=False)
            request.raise_for_status()
            request.encoding = 'utf-8'
            http_ok = True
        except Exception as e:
            if arg_type == 1:
                info_lock.acquire()
                info_arr[info["id"]]["stat"] = -3
                info_arr[info["id"]]["retry"] = retry
                info_lock.release()
            waitSec = randint(3, 10)
            sleep(waitSec)
        finally:
            retry = retry + 1

    if retry >= 10:
        raise MyExcept("http retry fail")
    
    data = request.text
    return data


def http_get(url, debug=0):
    #获取tcp/ip套接字
    tcpSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #tcpSock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack("ll", 10, 0))
    #tcpSock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, struct.pack("ll", 10, 0))

    #获取udp/ip套接字
    #udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #由于 socket 模块中有太多的属性。我们在这里破例使用了'from module import *'语句。使用 'from socket import *',我们就把 socket 模块里的所有属性都带到我们的命名空间里了,这样能 大幅减短我们的代码。
    #例如tcpSock = socket(AF_INET, SOCK_STREAM)

    items = re.findall(r"(https?):\/\/([^\/\\]*)(\/?.*)", url)
    if debug > 0:
        print(items)
        
    if len(items) < 1:
        print("http_get: invalid host %s" % (url))
        return ""

    port = 80
    if items[0][0] == "https":
        port = 443

    domain = items[0][1]
    path = items[0][2]
    if not path:
        path = "/"

    try:
        ret = tcpSock.connect_ex((domain, port))
        tcpSock.setblocking(False)
        if debug > 0 :
            print("conn to [%s:%d] ret: %d" % (domain, port, ret))

        if ret != 0 :
            print("connect to %s:%d error: %d" % (domain, port, ret))
            return ""
        cmd = "GET %s HTTP/1.1\r\n" % (path)
        host = "Host: %s\r\n" % (domain)
        ua = "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36 OPR/58.0.3135.79\r\n"
        ret = tcpSock.send(cmd.encode('utf-8'))
        ret += tcpSock.send(host.encode('utf-8'))
        ret += tcpSock.send(ua.encode('utf-8'))
        ret += tcpSock.send("\r\n".encode('utf-8'))
        if debug > 0 :
            print("%s%s%s" % (cmd,host,ua))
            print("send ret: %d" % (ret))
    except Exception as e:
        print("http_get: connect to %s fail" % (domain))
        return ""

    msg = ""
    content_len = -1
    content_msg = ""
    while True:
        try:
            byte = tcpSock.recv(global_http_buffer_len)
            if not byte or len(byte) <= 0:
                break
            
            msg += byte.decode('utf-8', errors='ignore')
            last = byte[len(byte)-30:len(byte)]
            if debug > 0 :
                print("recv len: %d/%d" % (len(byte), len(msg)))
                print("last: %s" % (last))
                print(msg)

            last = last.decode("utf-8", errors="ignore")

            tmp = re.findall(r"Content-Length: *([0-9]+)", msg)
            if len(tmp) > 0 :
                if debug > 0:
                    print("recv content-len: %d" % (int(tmp[0])))
                content_len = int(tmp[0])

            tmp = re.findall(r"[^\r\n]\r\n\r\n(.*$)", msg, re.S)
            if len(tmp) > 0:
                cstr = ""
                for tmpstr in tmp:
                    cstr += tmpstr
                    if debug > 0:
                        print("content part: %s" % (tmpstr))
                    
                if debug > 0 :
                    print("content recv len: %d/%d" % (len(cstr), len(tmp)))
                # 12 is a magic number...
                if content_len > 0 and len(cstr) >= content_len - 12:
                    if debug > 0 :
                        print("recv all data:%d/%d" % (len(cstr), content_len))
                    break
                
            if re.match(r"HTTP/1\.1 [0-13-9][0-9][0-9] ", msg):
                if debug > 0:
                    print("receive NOT 200 response")
                break
                
            #if last == "   \r\n0\r\n\r\n":
            if re.match(r"\s+\r\n0\r\n\r\n$", last):
                if debug > 0:
                    print("ending in 0 and return.")
                break

            if re.match(r"\r\n[\s\t]+\r\n[\s\t]+", last):
                if debug > 0:
                    print("ending in multispace and return.")
                break

        except OSError:
            pass

    tcpSock.close()
    return msg

if __name__ == '__main__':
    msg = http_get("http://www.avtbdizhi.com", debug=1)
