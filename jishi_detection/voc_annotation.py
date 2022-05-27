import os
import random
import xml.etree.ElementTree as ET

from utils.utils import get_classes

annotation_mode     = 0

classes_path        = '/project/train/src_repo/jishi_detection/model_data/class.txt'
trainval_percent    = 1
train_percent       = 0.6


VOCdevkit_sets  = [('2007', 'train'), ('2007', 'val')]
classes, _      = get_classes(classes_path)

def convert_annotation(year, image_id, list_file):
    in_file = open('/home/data/1043/%s.xml'%(image_id), encoding='utf-8')
    tree=ET.parse(in_file)
    root = tree.getroot()

    for obj in root.iter('object'):
        difficult = 0 
        if obj.find('difficult')!=None:
            difficult = obj.find('difficult').text
        cls = obj.find('name').text
        if cls not in classes or int(difficult)==1:
            continue
        cls_id = classes.index(cls)
        xmlbox = obj.find('bndbox')
        b = (int(float(xmlbox.find('xmin').text)), int(float(xmlbox.find('ymin').text)), int(float(xmlbox.find('xmax').text)), int(float(xmlbox.find('ymax').text)))
        list_file.write(" " + ",".join([str(a) for a in b]) + ',' + str(cls_id))
#     for obj in root.iter('polygon'):
#         cls = obj.find('class').text
#         if cls not in classes:
#             continue
#         cls_id = classes.index(cls)
#         xmlbox = obj.find('points')
#         (x1,y1)=( int(xmlbox.text.split(";")[0].split(",")[0]),int(xmlbox.text.split(";")[0].split(",")[1]) )
#         (x2,y2)=( int(xmlbox.text.split(";")[1].split(",")[0]),int(xmlbox.text.split(";")[1].split(",")[1]) )
#         (x3,y3)=( int(xmlbox.text.split(";")[2].split(",")[0]),int(xmlbox.text.split(";")[2].split(",")[1]) )
#         (x4,y4)=( int(xmlbox.text.split(";")[3].split(",")[0]),int(xmlbox.text.split(";")[3].split(",")[1]) )
#         xmin=sorted([x1,x2,x3,x4])[0]
#         xmax=sorted([x1,x2,x3,x4])[-1]
#         ymin=sorted([y1,y2,y3,y4])[0]
#         ymax=sorted([y1,y2,y3,y4])[-1]
        
#         b = (xmin, ymin, xmax, ymax)
#         list_file.write(" " + ",".join([str(a) for a in b]) + ',' + str(cls_id))
        
if __name__ == "__main__":
    random.seed(0)
    if annotation_mode == 0 or annotation_mode == 1:
        print("Generate txt in ImageSets.")
        xmlfilepath     = "/home/data/1043"
        saveBasePath    = "/project/train/src_repo/jishi_detection/Main"
        temp_xml        = os.listdir(xmlfilepath)
        total_xml       = []
        for xml in temp_xml:
            if xml.endswith(".xml"):
                total_xml.append(xml)

        num     = len(total_xml)  
        list    = range(num)  
        tv      = int(num*trainval_percent)  
        tr      = int(tv*train_percent)  
        trainval= random.sample(list,tv)  
        train   = random.sample(trainval,tr)  
        
        print("train and val size",tv)
        print("train size",tr)
        ftrainval   = open(os.path.join(saveBasePath,'trainval.txt'), 'w')  
        ftest       = open(os.path.join(saveBasePath,'test.txt'), 'w')  
        ftrain      = open(os.path.join(saveBasePath,'train.txt'), 'w')  
        fval        = open(os.path.join(saveBasePath,'val.txt'), 'w')  
        
        for i in list:  
            name=total_xml[i][:-4]+'\n'  
            if i in trainval:  
                ftrainval.write(name)  
                if i in train:  
                    ftrain.write(name)  
                else:  
                    fval.write(name)  
            else:  
                ftest.write(name)  
        
        ftrainval.close()  
        ftrain.close()  
        fval.close()  
        ftest.close()
        print("Generate txt in ImageSets done.")

    if annotation_mode == 0 or annotation_mode == 2:
        print("Generate 2007_train.txt and 2007_val.txt for train.")
        for year, image_set in VOCdevkit_sets:
            image_ids = open('/project/train/src_repo/jishi_detection/Main/%s.txt'%(image_set), encoding='utf-8').read().strip().split()
            list_file = open('/project/train/src_repo/jishi_detection/%s_%s.txt'%(year, image_set), 'w+', encoding='utf-8')
            for image_id in image_ids:
                list_file.write("/home/data/1043/%s.jpg"%(image_id))

                convert_annotation(year, image_id, list_file)
                list_file.write('\n')
            list_file.close()
        print("Generate 2007_train.txt and 2007val.txt for train done.")
