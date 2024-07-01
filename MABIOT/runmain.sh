#!/bin/bash

python main.py

if [ $? -eq 0 ]; then
    /home/pi/jiangboCloud/myshutdown.sh master
else
    echo "Python脚本执行失败"
fi
