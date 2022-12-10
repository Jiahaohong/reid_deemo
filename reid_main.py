#!/usr/bin/python
# encoding: utf-8

# from ast import pattern
import sys
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, qAbs, QRect
from PyQt5.QtGui import QPen, QPainter, QColor, QGuiApplication, QMovie, QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QDirModel, QTreeView, QWidget
import reid
import reid_new, model_zoo
import query
import requests
import json
import os
import numpy as np
import pickle
import cv2
import threading

SERVER_URL = 'http://10.3.18.13:40002'
# SERVER_URL = 'http://127.0.0.1:5900'
IMG_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.ppm', '.bmp', '.pgm', '.tif']
VIDEO_EXTENSIONS = ['.mp4']


class MainCode(QWidget, reid_new.Ui_Form):
    def __init__(self):
        QWidget.__init__(self)
        reid_new.Ui_Form.__init__(self)
        self.setupUi(self)
        self.query_path = ''
        self.gallery_path = ''
        self.gallery_size = 0
        self.page = 0
        self.reid_rank = None
        self.gallery_attr = None
        self.mode = 'image'
        self.queryimg = None

        self.model_zoo = ModelZoo()
        self.model_zoo.ok.clicked.connect(self.modelzoo_select_done)
        self.model_select.clicked.connect(self.modelzoo_select)
        self.model_name.setStyleSheet("color:red")
        self.model = None

        self.is_gallery_uploaded = False
        self.is_retrieval_completed = False

        self.res_ranks = []
        self.x0 = self.y0 = self.x1 = self.y1 = 0
        self.e = QueryCode()
        self.e.ok.clicked.connect(self.selected)

        self.cap = None
        self.frameRate = None
        self.th = threading.Thread(target=self.play_video)

        requests.get(SERVER_URL + '/reset')

        # self.modelzoo_select()

    def set_imagemode(self):  # 图片模式利用图片特征的相似度排序
        self.mode = 'image'

    def set_attrmode(self):  # 属性模式利用属性得分与目标查询属性的相似度排序
        self.mode = 'attr'

    # def set_oscode(self):
    #     self.code ='/os_search'

    # def set_tscode(self):
    #     self.code = '/ts_search'

    def modelzoo_select(self):

        # self.setupUi(self)
        self.model_zoo.show()
        self.model_zoo.setWindowModality(Qt.ApplicationModal)  # 阻塞主窗口

    def modelzoo_select_done(self):
        model = self.model_zoo.select_model()
        if model != self.model:
            self.clear_all()
        if model != self.model and self.is_gallery_uploaded:
            print('-------re-extract gallery features------')
            requests.get(SERVER_URL + '/remove_old_results')
            response = requests.get(SERVER_URL + '/' + model + '/gallery')
            print(response.text)
            self.model = model
            self.reid()
        self.model = model

        self.model_zoo.close()
        print(self.model)
        self.model_name.setText(self.model)

    def clear_all(self):  # 清屏
        self.is_retrieval_completed = False
        # self.querylabel.clear()
        # self.queryattrlabel.clear()
        # self.displaylabel.clear()
        # for i in range(1,11,1):
        #     getattr(self, 'rank' + str(i)).setText('')
        #     getattr(self, 'attr' + str(i)).setText(str(i))

    # 选择query图片并裁剪
    def query(self):
        print('click query')
        self.e.show()

    def selected(self):
        response = requests.get(SERVER_URL + '/clear/query')
        print(response.text)
        self.query_path = self.e.query_path
        (self.queryimg, self.x0, self.y0, self.x1, self.y1) = self.e.requests()
        png = QtGui.QPixmap(self.queryimg).scaled(self.querylabel.width(), self.querylabel.height())
        # box = np.array([self.x0, self.y0, self.x1, self.y1]).astype(int)
        box = (np.array([self.x0, self.y0, self.x1, self.y1]) / self.e.ratio).astype(int)
        # print(self.x0, self.y0, self.x1, self.y1,self.querylabel.width(), self.querylabel.height())
        self.querylabel.setPixmap(png)
        self.e.close()

        self.query_path = self.e.query_path
        box_path = './tmp/query_box.txt'
        np.savetxt(box_path, box, newline=" ", fmt='%d')
        with open(self.query_path, 'rb') as f:
            response = requests.post(SERVER_URL + '/upload/query', files={'file': f})
            print(response.text)
        with open(box_path, 'rb') as f:
            response = requests.post(SERVER_URL + '/upload/query', files={'file': f})
            print(response.text)

    # def openimage(self):
    #     imgName, imgType = QFileDialog.getOpenFileName(self,
    #                                                    "选择查询图片",
    #                                                    "F:\实验室\Market-1501-v15.09.15\gt_bbox",
    #                                                    " *.jpg;;*.png;;*.jpeg;;*.bmp;;All Files (*)")
    #     print(imgName, imgType)
    #     response = requests.get(SERVER_URL + '/clear/query')
    #     print(response.text)
    #     self.query_path = imgName
    #     png = QtGui.QPixmap(imgName).scaled(self.querylabel.width(), self.querylabel.height())
    #     self.querylabel.setPixmap(png)
    #
    #     with open(self.query_path, 'rb') as f:  # 上传query图片
    #         response = requests.post(SERVER_URL + '/upload/query', files={'file': f})
    #         print(response.text)

    # 选择gallery文件夹
    def openfolder(self):
        self.gallery_path = QFileDialog.getExistingDirectory(self,
                                                             "选择待查询图片文件夹")
        response = requests.get(SERVER_URL + '/clear/gallery')
        print(response.text)
        # self.gallery_label.setText(self.gallery_path)
        for root, _, fnames in sorted(os.walk(self.gallery_path)):
            for fname in sorted(fnames):
                if has_file_allowed_extension(fname, IMG_EXTENSIONS):
                    path = os.path.join(root, fname)
                    with open(path, 'rb') as f:
                        response = requests.post(SERVER_URL + '/upload/gallery', files={'file': f})
                        print(response.text)
                if has_file_allowed_extension(fname, VIDEO_EXTENSIONS):
                    video_path = os.path.join(root, fname)
                    video_name = os.path.splitext(fname)[0]
                    cap = cv2.VideoCapture(video_path)
                    i = 0
                    ret, frame = cap.read()
                    while ret:
                        i += 1
                        frame_name = video_name + '_' + str(i) + '.jpg'
                        frame_path = os.path.join('./gallery/', frame_name)
                        cv2.imwrite(frame_path, frame)
                        with open(frame_path, 'rb') as f:
                            response = requests.post(SERVER_URL + '/upload/gallery', files={'file': f})
                            print(response.text)
                        ret, frame = cap.read()
                        if i >= 50:
                            break
                    cap.release()

        response = requests.get(SERVER_URL + '/' + self.model + '/gallery')
        self.is_gallery_uploaded = True
        print(response.text)
        # item = (path, class_to_idx[target])
        # images.append(path)

    def train(self):
        response = requests.get(SERVER_URL + '/train')
        print(response.text)

    # 开始检索
    def reid(self):
        if self.mode == 'image':
            # response = requests.get(SERVER_URL + '/reid')
            response = requests.get(SERVER_URL + '/' + self.model + '/reid')
            try:
                self.reid_rank = json.loads(response.text)
            except BaseException as e:
                print(e)
                return
            self.gallery_size = len(self.reid_rank['score'])
            self.page = 0
            self.is_retrieval_completed = True
            self.show_rank()
            self.queryattrlabel.setText(print_attr(self.reid_rank['qattr'], self.reid_rank['qattr_sc']))
        elif self.mode == 'attr':
            self.get_query_attr()
            with open('query_attr.pkl', 'rb') as f:
                response = requests.post(SERVER_URL + '/os_attr/', files={'file': f})
            try:
                self.reid_rank = json.loads(response.text)
            except BaseException as e:
                print(e)
                return
            self.gallery_size = len(self.reid_rank['score'])
            # self.is_retrieval_completed = True
            self.page = 0
            self.show_rank(ignore_check=True)

        # for i in range(10):
        #     label = getattr(self, 'rank' + str(i + 1 + 10*self.page))
        #     # label = self.rank1
        #     img_name = str(i)+'.jpg'
        #     response = requests.get(SERVER_URL + '/get_file/'+img_name)
        #     with open('./res/'+str(i)+'.jpg', 'wb') as f:
        #         for chunk in response.iter_content(100000):
        #             f.write(chunk)
        #
        #     png = QtGui.QPixmap('./res/'+img_name).scaled(label.width(), label.height())
        #     print(label.width(), label.height(),label.iconSize())
        #     # label.setIconSize(label.width(), label.height())
        #     # print(label.width(), label.height())
        #     icon = QtGui.QIcon(png)
        #     label.setIcon(icon)
        #     label.setIconSize(QtCore.QSize(label.width()-13, label.height()-9))
        #     print(label.width(), label.height(),label.iconSize())

    def show_rank(self, ignore_check=False):
        if not self.is_retrieval_completed and not ignore_check:
            return
        import re

        for i in range(10):
            label = getattr(self, 'rank' + str(i + 1))
            text_label = getattr(self, 'attr' + str(i + 1))
            # label = self.rank1
            rank = i + 10 * self.page
            outtext = ''
            if i + 10 * self.page < self.gallery_size:
                img_name = str(rank) + '.jpg'
                response = requests.get(SERVER_URL + '/get_file/' + img_name)
                with open('./res/' + str(rank) + '.jpg', 'wb') as f:
                    for chunk in response.iter_content(100000):
                        f.write(chunk)
                outtext = 'rank {:d}\nscore:{:.2f}\n'.format(rank, 100 * self.reid_rank['score'][rank])
                outtext += print_attr(self.reid_rank['gattr'][rank], self.reid_rank['gattr_sc'][rank])
                print('raw:' + self.reid_rank['raw_path'][rank])
                cropped = os.path.split(self.reid_rank['raw_path'][rank])[-1]
                # file_name = cropped.split('_')[0]
                pic_type = cropped.split('.')[-1]
                patt = re.compile(r'_([-\d]+).' + pic_type)  # 去掉box排序和文件类名
                file_name = patt.sub('', cropped)

                # 寻找同名文件
                for root, _, fnames in sorted(os.walk(self.gallery_path)):
                    for fname in sorted(fnames):
                        if os.path.splitext(fname)[0] == file_name:
                            fpath = os.path.join(self.gallery_path, fname)
                            self.res_ranks.append(fpath)
                            print('res: ' + fpath)
                            break
            else:
                img_name = ''
            text_label.setText(outtext)
            png = QtGui.QPixmap('./res/' + img_name).scaled(label.width(), label.height())
            # print(label.width(), label.height(),label.iconSize())
            # label.setIconSize(label.width(), label.height())
            # print(label.width(), label.height())
            icon = QtGui.QIcon(png)
            label.setIcon(icon)
            label.setIconSize(QtCore.QSize(label.width() - 13, label.height() - 9))
            # print(label.width(), label.height(),label.iconSize())

    # def filt_attr(self, attr):
    #     result = attr
    #     if self.comboBox_age.currentIndex() != 0:
    #         result = filter(lambda x: x[1][0] == self.comboBox_age.currentIndex()-1, result)
    #     return result

    def get_query_attr(self):
        attr_value = np.zeros(27)
        attr_mask = np.zeros(27)
        # 年龄
        if self.comboBox_age.currentIndex() != 0:
            attr_value[0] = self.comboBox_age.currentIndex() - 1
            attr_mask[0] = 1
        else:
            attr_mask[0] = 0

        # 性别
        if self.comboBox_sex.currentIndex() != 0:
            attr_value[26] = self.comboBox_sex.currentIndex() - 1
            attr_mask[26] = 1
        else:
            attr_mask[26] = 0

        # 帽子
        if self.comboBox_hat.currentIndex() != 0:
            attr_value[25] = self.comboBox_hat.currentIndex() - 1
            attr_mask[25] = 1
        else:
            attr_mask[25] = 0

        # 头发
        if self.comboBox_hair.currentIndex() != 0:
            attr_value[24] = self.comboBox_hair.currentIndex() - 1
            attr_mask[24] = 1
        else:
            attr_mask[24] = 0

        # 上衣
        if self.comboBox_up.currentIndex() != 0:
            attr_value[23] = self.comboBox_up.currentIndex() - 1
            attr_mask[23] = 1
        else:
            attr_mask[23] = 0

        if self.comboBox_upcolor.currentIndex() != 0:
            attr_value[13 - 1 + self.comboBox_upcolor.currentIndex()] = 1
            attr_mask[13 - 1 + self.comboBox_upcolor.currentIndex()] = 1
        else:
            attr_mask[13:21] = 0

        # 下身
        if self.comboBox_down.currentIndex() != 0:
            attr_value[21] = (self.comboBox_down.currentIndex() - 1) // 2
            attr_value[22] = (self.comboBox_down.currentIndex() - 1) % 2
            attr_mask[21:23] = 1
        else:
            attr_mask[21:23] = 0

        if self.comboBox_downcolor.currentIndex() != 0:
            attr_value[4 - 1 + self.comboBox_downcolor.currentIndex()] = 1
            attr_mask[4 - 1 + self.comboBox_downcolor.currentIndex()] = 1
        else:
            attr_mask[4:13] = 0

        # 背包
        if self.comboBox_bag.currentIndex() == 0:
            attr_mask[1:4] = 0
        elif self.comboBox_bag.currentIndex() == 4:
            attr_value[1:4] = 0
            attr_mask[1:4] = 1
        else:
            attr_value[1 - 1 + self.comboBox_bag.currentIndex()] = 1
            attr_mask[1 - 1 + self.comboBox_bag.currentIndex()] = 1

        print('value:', attr_value)
        print('mask:', attr_mask)
        with open('query_attr.pkl', 'wb') as f:
            pickle.dump({'value': attr_value, 'mask': attr_mask.astype(np.bool)}, f)
        return attr_value, attr_mask

    def show_attr_rank(self):
        pass

    def display(self, index):
        # print(self.objectName())
        if index + 10 * self.page < self.gallery_size:
            response = requests.get(SERVER_URL + '/box/' + str(index + 10 * self.page))
            # print(response.text)
            with open('./res/box.jpg', 'wb') as f:
                for chunk in response.iter_content(100000):
                    f.write(chunk)
            filename = self.res_ranks[index + 10 * self.page]
            if os.path.splitext(filename)[-1] == '.jpg' or os.path.splitext(filename)[-1] == '.png':
                print(filename)
                # png = QtGui.QPixmap(filename).scaled(self.displaylabel.width(), self.displaylabel.height())
                png = QtGui.QPixmap('./res/box.jpg').scaled(self.displaylabel.width(), self.displaylabel.height())
                self.displaylabel.setPixmap(png)
            elif os.path.splitext(filename)[-1] == '.mp4':
                self.cap = cv2.VideoCapture(filename)
                self.frameRate = self.cap.get(cv2.CAP_PROP_FPS)
                # 创建视频显示线程
                if not self.th.isAlive():
                    self.th.start()
        else:
            pass

    def play_video(self):
        success, frame = self.cap.read()
        while success:
            # RGB转BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            png = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            png = png.scaled(self.displaylabel.width(), self.displaylabel.height())
            self.displaylabel.setPixmap(QPixmap.fromImage(png))

            success, frame = self.cap.read()
            cv2.waitKey(int(1000 / self.frameRate))

    # 选中第n张图片
    def display0(self):
        self.display(0)

    def display1(self):
        self.display(1)

    def display2(self):
        self.display(2)

    def display3(self):
        self.display(3)

    def display4(self):
        self.display(4)

    def display5(self):
        self.display(5)

    def display6(self):
        self.display(6)

    def display7(self):
        self.display(7)

    def display8(self):
        self.display(8)

    def display9(self):
        self.display(9)

    # 翻页
    def pagedown(self):
        self.page += 1
        self.page = min(self.page, int((self.gallery_size - 1) / 10))
        self.show_rank()

    def pageup(self):
        self.page -= 1
        self.page = max(0, self.page)
        self.show_rank()


class CropLabel(QLabel):
    x0 = 0
    y0 = 0
    x1 = 0
    y1 = 0
    flag = False
    img = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.flag = True
            self.x0 = event.x()
            self.y0 = event.y()
        if event.button() == Qt.RightButton:
            self.flag = False
            if self.img is not None:
                self.img = None
                self.x0 = self.y0 = self.x1 = self.y1 = 0
                self.update()
            else:
                self.close()

    def mouseReleaseEvent(self, event):
        self.flag = False

    def mouseMoveEvent(self, event):
        if self.flag:
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()

    def mouseDoubleClickEvent(self, event):
        if self.img is not None:
            self.img.save('555.png')
            print('save img')

    def paintEvent(self, event):
        super().paintEvent(event)
        rect = QRect(self.x0, self.y0, abs(self.x1 - self.x0), abs(self.y1 - self.y0))
        painter = QPainter(self)
        painter.setPen(QPen(Qt.red, 1, Qt.SolidLine))
        painter.drawRect(rect)

        pqscreen = QGuiApplication.primaryScreen()
        if abs(self.x1 - self.x0) > 1 and abs(self.y1 - self.y0) > 1:
            self.img = pqscreen.grabWindow(self.winId(), self.x0, self.y0, abs(self.x1 - self.x0),
                                           abs(self.y1 - self.y0))
        else:
            self.img = None
            pass

    def requests(self):
        req = (self.img, self.x0, self.y0, self.x1, self.y1)
        return req


class QueryCode(QWidget, query.Ui_Form):
    def __init__(self):
        QWidget.__init__(self)
        query.Ui_Form.__init__(self)
        self.setupUi(self)
        self.query_path = ''
        self.lb = CropLabel(self)

    def show(self):
        super().show()
        imgName, imgType = QFileDialog.getOpenFileName(self,
                                                       "选择查询图片",
                                                       "./gallery",
                                                       " *.jpg;;*.png;;*.jpeg;;*.bmp;;All Files (*)")
        self.query_path = imgName
        png = QtGui.QPixmap(imgName)
        self.ratio = 1.
        if png.width() > 1280 or png.height() > 720:
            alpha = 1280 / png.width()
            beta = 720 / png.height()
            ratio = np.min([alpha, beta])
            h = int(png.height() * ratio)
            w = int(png.width() * ratio)
            png = png.scaled(w, h)
            self.ratio = ratio  # fix gt框不准的bug
        self.lb.setPixmap(png)
        self.lb.adjustSize()
        self.lb.setCursor(Qt.CrossCursor)
        self.lb.show()

    def openimage(self):
        imgName, imgType = QFileDialog.getOpenFileName(self,
                                                       "选择查询图片",
                                                       "./gallery",
                                                       " *.jpg;;*.png;;*.jpeg;;*.bmp;;All Files (*)")
        # print(imgName, imgType)
        # response = requests.get(SERVER_URL + '/clear/query')
        # print(response.text)
        self.query_path = imgName
        png = QtGui.QPixmap(imgName)
        if png.width() > 1280 or png.height() > 720:
            alpha = 1280 / png.width()
            beta = 720 / png.height()
            ratio = np.min([alpha, beta])
            h = int(png.height() * ratio)
            w = int(png.width() * ratio)
            png = png.scaled(w, h)
        self.lb.setPixmap(png)
        self.lb.adjustSize()
        self.lb.setCursor(Qt.CrossCursor)
        self.lb.show()

    def requests(self):
        return self.lb.requests()


# 将属性转换为字符串
def print_attr(attribute, score):
    text = []
    if attribute[0] == 0:
        text.append("年龄: 少年")
    elif attribute[0] == 1:
        text.append("年龄：青少年")
    elif attribute[0] == 2:
        text.append("年龄：成年人")
    else:
        text.append("年龄：老年人")
    if attribute[26] == 1:
        text.append("性别：女")
    else:
        text.append("性别：男")
    if attribute[25] == 1:
        text.append("是否戴帽子：是")
    else:
        text.append("是否戴帽子：否")
    if attribute[24] == 1:
        text.append("头发长度：长发")
    else:
        text.append("头发长度：短发")

    # a1 = attribute[13:21]
    a1 = np.array(score[13:21])
    color = ["黑色", "蓝色", "绿色", "灰色", "紫色", "红色", "白色", "黄色"]
    b1 = np.argmax(a1)
    if attribute[23] == 1:
        text.append("上身：" + color[b1] + "短袖")
    else:
        text.append("上身：" + color[b1] + "长袖")
    bags = ["背包", "挎包", "手提包"]
    a2 = attribute[1:4]
    a2.append(1)
    b2 = a2.index(1)
    if b2 == 3:
        text.append("包的类型：没有包")
    else:
        text.append("包的类型:" + bags[b2])
    color1 = ["黑色", "蓝色", "棕色", "灰色", "绿色", "粉红色", "紫色", "白色", "黄色"]
    # a3 = attribute[4:13]
    a3 = np.array(score[4:13])
    b3 = np.argmax(a3)
    # b3 = a3.index(1)
    if attribute[21] == 1:
        if attribute[22] == 1:
            text.append("下身：" + color1[b3] + "短裤")
        else:
            text.append("下身：" + color1[b3] + "长裤")
    else:
        if attribute[22] == 1:
            text.append("下身：" + color1[b3] + "短裙")
        else:
            text.append("下身：" + color1[b3] + "长裙")
    return '\n'.join(text)


def has_file_allowed_extension(filename, extensions):
    """Checks if a file is an allowed extension.

    Args:
        filename (string): path to a file

    Returns:
        bool: True if the filename ends with a known image extension
    """
    filename_lower = filename.lower()
    return any(filename_lower.endswith(ext) for ext in extensions)


class ModelZoo(QWidget, model_zoo.Ui_Dialog):
    def __init__(self):
        QWidget.__init__(self)

        self.model = 'DMRNet'
        self.setupUi(self)

    def select_model(self):
        if self.botton1.isChecked():
            self.model = 'DMRNet'
        elif self.botton2.isChecked():
            self.model = 'RDLR'
        elif self.botton3.isChecked():
            self.model = 'NAE'
        else:
            # raise NotImplementedError()
            self.model = 'DMRNet'
        return self.model


if __name__ == '__main__':
    app = QApplication(sys.argv)

    ui = MainCode()
    ui.show()
    ui.modelzoo_select()
    sys.exit(app.exec_())
