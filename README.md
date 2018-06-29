# atb

### install
1. pip install prompt_toolkit
2. pip install beautifulsoup4
3. pip install lxml

when update pip to 10.0, there's an error: "cannot import name main". You can solve this in two ways:
1. modify /usr/bin/pip3
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
