#-----------------------------------------------------------------------#
#   predict.py将单张图片预测、摄像头检测、FPS测试和目录遍历检测等功能
#   整合到了一个py文件中，通过指定mode进行模式的修改。
#-----------------------------------------------------------------------#
import time
import copy
import cv2
from PIL import Image

from yolo import YOLO

if __name__ == "__main__":
    image = Image.open("/home/ys/zyn/car_plate/image/test/171.jpg")
    t1=time.time()
    yolo = YOLO()

    # yolo.origin(["paper_napkin","folder","fruit knife"], 'H:\yolov4-pytorch-master\yolov4-pytorch-master\model_data\\paper_napkin_folder_FruitKnife_ep140-loss0.447-val_loss0.567.pth')
    # yolo.origin(["paper napkin","folder","fruit knife","hammer","melon seeds","toilet water","soda","water","cola"], 'H:\yolov4-pytorch-master\yolov4-pytorch-master\model_data\\all_ep150-loss0.651-val_loss0.420.pth')
    yolo.origin(["plate"], '/home/ys/zyn/car_plate/yolov4-pytorch-master/yolov4-pytorch-master/logs/plate_ep003-loss4.190-val_loss2.236.pth')
    # yolo.origin(["AD calcium milk","soda"], 'H:\sanhey\yolov4\model_data\\chocolate_dishSoap_laundryDetergent_shampoo_ep150-loss0.531-val_loss0.412.pth')


    result1 = yolo.detect_image(image)


    t2=time.time()
    result1.show()
    # print(result[0][:, :4])
    print(t2-t1)


