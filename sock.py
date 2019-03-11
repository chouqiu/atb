import requests
from urllib.request import *
from urllib.error import *
from avtb_global import *
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

def request_get(host, path, debug=0):
    http_ok = False
    retry = 1

    global_headers = {'Host': host}
    request = Request(url="http://%s/%s"%(host,path), headers=global_headers)

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

def urllib_get(host, path, debug=0):
    http_ok = False
    retry = 1
    global_headers = {'Host': host}

    while not http_ok and retry < 10:
        try:
            request = requests.get(url=url, headers=global_headers)
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


def http_get(host, path, debug=0):
    #获取tcp/ip套接字
    tcpSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #获取udp/ip套接字
    #udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #由于 socket 模块中有太多的属性。我们在这里破例使用了'from module import *'语句。使用 'from socket import *',我们就把 socket 模块里的所有属性都带到我们的命名空间里了,这样能 大幅减短我们的代码。
    #例如tcpSock = socket(AF_INET, SOCK_STREAM)

    ret = tcpSock.connect_ex((host, 80))
    tcpSock.setblocking(False)
    if debug > 0 :
        print("conn ret: %d" % (ret))
    ret = tcpSock.send(("GET %s HTTP/1.1\r\n" % (path)).encode('utf-8'))
    ret = tcpSock.send(("Host: %s\r\n" % (host)).encode('utf-8'))
    ret = tcpSock.send("\r\n".encode('utf-8'))
    if debug > 0 :
        print("send ret: %d" % (ret))

    # HTTP/1.1 301 Moved Permanently
    # X-Powered-By: Express
    # Location: http://www.avtbt.com//recent/9/
    mod301 = re.compile(r"HTTP/1\.1 30[0-9] .*Location: (http.*?)[\r\n]", re.S)
    msg = ""
    while True:
        try:
            byte = tcpSock.recv(40960)
            msg += byte.decode('utf-8', errors='ignore')
            if debug > 0 :
                print("recv len: %d/%d" % (len(byte), len(msg)))
                print("last: %s" % (byte[len(byte)-20:len(byte)]))

            last = msg[len(msg)-10:len(msg)]
            if last == "   \r\n0\r\n\r\n" :
                break
            newurl = mod301.findall(msg)
            if newurl :
                print("get new jump url:%s" % (newurl[0]))
                break
                
            if debug > 0 :
                print(msg)
                break
        except OSError:
            pass

    tcpSock.close()
    return msg

if __name__ == '__main__':
    msg = http_get("www.avtbq.com", '/', debug=1)
    print(msg)
