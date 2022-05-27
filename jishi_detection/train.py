
#-------------------------------------#
#       对数据集进行训练
#-------------------------------------#
import os

import numpy as np
import torch
import torch.backends.cudnn as cudnn
import torch.optim as optim
from torch.utils.data import DataLoader

from nets.yolo import YoloBody
from nets.yolo_training import YOLOLoss, weights_init
from utils.callbacks import LossHistory
from utils.dataloader import YoloDataset, yolo_dataset_collate
from utils.utils import get_anchors, get_classes
from utils.utils_fit import fit_one_epoch

'''
训练自己的目标检测模型一定需要注意以下几点：
1、训练前仔细检查自己的格式是否满足要求，该库要求数据集格式为VOC格式，需要准备好的内容有输入图片和标�?
   输入图片�?jpg图片，无需固定大小，传入训练前会自动进行resize�?
   灰度图会自动转成RGB图片进行训练，无需自己修改�?
   输入图片如果后缀非jpg，需要自己批量转成jpg后再开始训练�?

   标签�?xml格式，文件中会有需要检测的目标信息，标签文件和输入图片文件相对应�?

2、训练好的权值文件保存在logs文件夹中，每个epoch都会保存一次，如果只是训练了几个step是不会保存的，epoch和step的概念要捋清楚一下�?
   在训练过程中，该代码并没有设定只保存最低损失的，因此按默认参数训练完会�?00个权值，如果空间不够可以自行删除�?
   这个并不是保存越少越好也不是保存越多越好，有人想要都保存、有人想只保存一点，为了满足大多数的需求，还是都保存可选择性高�?

3、损失值的大小用于判断是否收敛，比较重要的是有收敛的趋势，即验证集损失不断下降，如果验证集损失基本上不改变的话，模型基本上就收敛了�?
   损失值的具体大小并没有什么意义，大和小只在于损失的计算方式，并不是接近于0才好。如果想要让损失好看点，可以直接到对应的损失函数里面除上10000�?
   训练过程中的损失值会保存在logs文件夹下的loss_%Y_%m_%d_%H_%M_%S文件夹中

4、调参是一门蛮重要的学问，没有什么参数是一定好的，现有的参数是我测试过可以正常训练的参数，因此我会建议用现有的参数�?
   但是参数本身并不是绝对的，比如随着batch的增大学习率也可以增大，效果也会好一些；过深的网络不要用太大的学习率等等�?
   这些都是经验上，只能靠各位同学多查询资料和自己试试了�?
'''  
if __name__ == "__main__":
    os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
    # os.environ["CUDA_VISIBLE_DEVICES"]='0'
    #-------------------------------#
    #   是否使用Cuda
    #   没有GPU可以设置成False
    #-------------------------------#
    Cuda = True
    #--------------------------------------------------------#
    #   训练前一定要修改classes_path，使其对应自己的数据�?
    #--------------------------------------------------------#
    classes_path    = '/project/train/src_repo/jishi_detection/model_data/class.txt'
    #---------------------------------------------------------------------#
    #   anchors_path代表先验框对应的txt文件，一般不修改�?
    #   anchors_mask用于帮助代码找到对应的先验框，一般不修改�?
    #---------------------------------------------------------------------#
    anchors_path    = '/project/train/src_repo/jishi_detection/model_data/yolo_anchors.txt'
    anchors_mask    = [[6, 7, 8], [3, 4, 5], [0, 1, 2]]
    #----------------------------------------------------------------------------------------------------------------------------#
    #   权值文件请看README，百度网盘下载。数据的预训练权重对不同数据集是通用的，因为特征是通用的�?
    #   预训练权重对�?9%的情况都必须要用，不用的话权值太过随机，特征提取效果不明显，网络训练的结果也不会好�?
    #
    #   如果想要断点续练就将model_path设置成logs文件夹下已经训练的权值文件�?
    #   当model_path = ''的时候不加载整个模型的权值�?
    #
    #   此处使用的是整个模型的权重，因此是在train.py进行加载的�?
    #   如果想要让模型从0开始训练，则设置model_path = ''，下面的Freeze_Train = Fasle，此时从0开始训练，且没有冻结主干的过程�?
    #   一般来讲，�?开始训练效果会很差，因为权值太过随机，特征提取效果不明显�?
    #----------------------------------------------------------------------------------------------------------------------------#
    model_path      = ""
   
    # model_path      = '/home/ys/zyn/car_jishi/yolov4-pytorch-master/yolov4-pytorch-master/logs/jishi_ep041-loss1.828-val_loss1.782.pth'
    #------------------------------------------------------#
    #   输入的shape大小，一定要�?2的倍数
    #------------------------------------------------------#
    input_shape     = [416, 416]
    #------------------------------------------------------#
    #   Yolov4的tricks应用
    #   mosaic 马赛克数据增�?True or False 
    #   实际测试时mosaic数据增强并不稳定，所以默认为False
    #   Cosine_lr 余弦退火学习率 True or False
    #   label_smoothing 标签平滑 0.01以下一�?�?.01�?.005
    #------------------------------------------------------#
    mosaic              = False
    Cosine_lr           = False
    label_smoothing     = 0

    #----------------------------------------------------#
    #   训练分为两个阶段，分别是冻结阶段和解冻阶段�?
    #   显存不足与数据集大小无关，提示显存不足请调小batch_size�?
    #   受到BatchNorm层影响，batch_size最小为2，不能为1�?
    #----------------------------------------------------#
    #----------------------------------------------------#
    #   冻结阶段训练参数
    #   此时模型的主干被冻结了，特征提取网络不发生改�?
    #   占用的显存较小，仅对网络进行微调
    #----------------------------------------------------#
    Init_Epoch          = 0
    Freeze_Epoch        = 0
    Freeze_batch_size   = 32
    Freeze_lr           = 1e-3
    #----------------------------------------------------#
    #   解冻阶段训练参数
    #   此时模型的主干不被冻结了，特征提取网络会发生改变
    #   占用的显存较大，网络所有的参数都会发生改变
    #----------------------------------------------------#
    UnFreeze_Epoch      = 8
    Unfreeze_batch_size = 12
    Unfreeze_lr         = 1e-4
    #------------------------------------------------------#
    #   是否进行冻结训练，默认先冻结主干训练后解冻训练�?
    #------------------------------------------------------#
    Freeze_Train        = True
    #------------------------------------------------------#
    #   用于设置是否使用多线程读取数�?
    #   开启后会加快数据读取速度，但是会占用更多内存
    #   内存较小的电脑可以设置为2或�?  
    #------------------------------------------------------#
    num_workers         = 8
    #----------------------------------------------------#
    #   获得图片路径和标�?
    #----------------------------------------------------#
    # train_annotation_path   = '/home/ys/zyn/new_database/Main/water/train.txt'
    # val_annotation_path     = '/home/ys/zyn/new_database/Main/water/val.txt'

    train_annotation_path = '/project/train/src_repo/jishi_detection/2007_train.txt'
    val_annotation_path = '/project/train/src_repo/jishi_detection/2007_val.txt'
    #----------------------------------------------------#
    #   获取classes和anchor
    #----------------------------------------------------#
    class_names, num_classes = get_classes(classes_path)
    anchors, num_anchors     = get_anchors(anchors_path)

    #------------------------------------------------------#
    #   创建yolo模型
    #------------------------------------------------------#
    model = YoloBody(anchors_mask, num_classes)
    weights_init(model)
    if model_path != '':
        #------------------------------------------------------#
        #   权值文件请看README，百度网盘下�?
        #------------------------------------------------------#
        print('Load weights {}.'.format(model_path))
        device          = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model_dict      = model.state_dict()
        pretrained_dict = torch.load(model_path, map_location = device)
        pretrained_dict = {k: v for k, v in pretrained_dict.items() if np.shape(model_dict[k]) == np.shape(v)}
        model_dict.update(pretrained_dict)
        model.load_state_dict(model_dict)

    model_train = model.train()
    if Cuda:
        model_train = torch.nn.DataParallel(model)
        cudnn.benchmark = True
        model_train = model_train.cuda()

    yolo_loss    = YOLOLoss(anchors, num_classes, input_shape, Cuda, anchors_mask, label_smoothing)
    loss_history = LossHistory("/project/train/src_repo/jishi_detection/logs","jishi")

    #---------------------------#
    #   读取数据集对应的txt
    #---------------------------#
    with open(train_annotation_path) as f:
        train_lines = f.readlines()
    with open(val_annotation_path) as f:
        val_lines   = f.readlines()
    num_train   = len(train_lines)
    num_val     = len(val_lines)

    #------------------------------------------------------#
    #   主干特征提取网络特征通用，冻结训练可以加快训练速度
    #   也可以在训练初期防止权值被破坏�?
    #   Init_Epoch为起始世�?
    #   Freeze_Epoch为冻结训练的世代
    #   UnFreeze_Epoch总训练世�?
    #   提示OOM或者显存不足请调小Batch_size
    #------------------------------------------------------#
    if True:
        batch_size  = Freeze_batch_size
        lr          = Freeze_lr
        start_epoch = Init_Epoch
        end_epoch   = Freeze_Epoch
        
        optimizer       = optim.Adam(model_train.parameters(), lr, weight_decay = 5e-4)
        if Cosine_lr:
            lr_scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=5, eta_min=1e-5)
        else:
            lr_scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.94)

        train_dataset   = YoloDataset(train_lines, input_shape, num_classes, mosaic=mosaic, train = True)
        val_dataset     = YoloDataset(val_lines, input_shape, num_classes, mosaic=False, train = False)
        gen             = DataLoader(train_dataset, shuffle = True, batch_size = batch_size, num_workers = num_workers, pin_memory=True,
                                    drop_last=True, collate_fn=yolo_dataset_collate)
        gen_val         = DataLoader(val_dataset  , shuffle = True, batch_size = batch_size, num_workers = num_workers, pin_memory=True, 
                                    drop_last=True, collate_fn=yolo_dataset_collate)
                        
        epoch_step      = num_train // batch_size
        epoch_step_val  = num_val // batch_size
        
        if epoch_step == 0 or epoch_step_val == 0:
            raise ValueError("数据集过小，无法进行训练，请扩充数据集")

        #------------------------------------#
        #   冻结一定部分训�?
        #------------------------------------#
        if Freeze_Train:
            for param in model.backbone.parameters():
                param.requires_grad = False

        for epoch in range(start_epoch, end_epoch):
            fit_one_epoch(model_train, model, yolo_loss, loss_history, optimizer, epoch, 
                    epoch_step, epoch_step_val, gen, gen_val, end_epoch, Cuda,"jishi")
            lr_scheduler.step()
            
    if True:
        batch_size  = Unfreeze_batch_size
        lr          = Unfreeze_lr
        start_epoch = Freeze_Epoch
        end_epoch   = UnFreeze_Epoch
        
        optimizer       = optim.Adam(model_train.parameters(), lr, weight_decay = 5e-4)
        if Cosine_lr:
            lr_scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=5, eta_min=1e-5)
        else:
            lr_scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.94)

        train_dataset   = YoloDataset(train_lines, input_shape, num_classes, mosaic=mosaic, train = True)
        val_dataset     = YoloDataset(val_lines, input_shape, num_classes, mosaic=False, train = False)
        print(train_dataset.length)
        gen             = DataLoader(train_dataset, shuffle = True, batch_size = batch_size, num_workers = num_workers, pin_memory=True,
                                    drop_last=True, collate_fn=yolo_dataset_collate)
        gen_val         = DataLoader(val_dataset  , shuffle = True, batch_size = batch_size, num_workers = num_workers, pin_memory=True, 
                                    drop_last=True, collate_fn=yolo_dataset_collate)
                        
        epoch_step      = num_train // batch_size
        epoch_step_val  = num_val // batch_size
        
        if epoch_step == 0 or epoch_step_val == 0:
            raise ValueError("数据集过小，无法进行训练，请扩充数据")

        #------------------------------------#
        #   冻结一定部分训�?
        #------------------------------------#
        if Freeze_Train:
            for param in model.backbone.parameters():
                param.requires_grad = True
        best_loss=10e8
        for epoch in range(start_epoch, end_epoch):
            best_loss=fit_one_epoch(model_train, model, yolo_loss, loss_history, optimizer, epoch, 
                    epoch_step, epoch_step_val, gen, gen_val, end_epoch, Cuda,best_loss)
            lr_scheduler.step()