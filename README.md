# atb

### install
1. pip install prompt_toolkit
2. pip install beautifulsoup4
3. pip install lxml
4. pip install requests

when update pip to 10.0, there's an error: "cannot import name main". You can solve this in two ways:
1. modify /usr/bin/pip3

### some comment
1. update pip: pip install --upgrade pip.
2. sometimes install lxml may fail, check if libxml and libxml-dev is installed.
3. when compile lxml fail, try this: 
```
export C_INCLUDE_PATH=/data/data/termux.com/files/usr/include/:/data/data/termux.com/files/usr/include/lxml2
export CPLUS_INCLUDE_PATH=/data/data/termux.com/files/usr/include/:/data/data/termux.com/files/usr/include/lxml2
```
4. if still fail, try this:
```
pkg install libxslt libxslt-dev
```

### about github
You can do the following:
1. git init
2. git add README.md
3. git commit -m 'readme'
4. git remote add origin https://github.com/chouqiu/atb.git
5. git push -u origin master

```
from pip import __main__  
if __name__ == '__main__':  
    sys.exit(__main__._main()) 
```
2. use original pip3 plus sudo: sudo pip3 install xxxx
 
### changelog
* 2018-06-17 v2.3
> 1. support seaching
> 2. modify some bugs

* 2018-06-19 v2.4
> 1. modify some miner bugs

* 2018-06-22 v2.5
> 1. modify some miner bugs

* 2018-06-29 v2.6
> 1. modify some miner bugs

* 2018-07-04 v2.7
> 1. modify some minor bugs...

* 2018-08-19 v2.8
> 1. add task queue
> 2. you can set concurrency using 'setc'
> 3. modify some minor bugs...

* 2018-08-23 v2.9
> 1. support code 301..

* 2018-10-06 v3.0
> 1. add help menu

* 2019-02-04 v3.1
> 1. support store path, and socket access...

* 2019-02-07 v3.2
> 1. some bugs...

* 2019-03-05 v3.3
> 1. some bugs...

* 2019-03-18 v3.4
> 1. rebuild the code
> 2. support detect 301/302 jump
