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
2. use original pip3: sudo pip3 install xxxx
 
