#! /bin/bash
python /project/train/src_repo/jishi_detection/voc_annotation.py
python /project/train/src_repo/jishi_detection/train.py | tee -a /project/train/log/logs.txt
