#!/usr/bin/env python3
#coding:utf-8

__author__ = 'xmxoxo<xmxoxo@qq.com>'

import warnings
warnings.filterwarnings("ignore")

import argparse
import os
import sys
import time
import logging
import traceback
import cv2
import random

from flask import Flask, request, render_template, jsonify, abort, make_response
from flask import url_for, Response, json, session, send_from_directory
# 版本号
gblVersion = '1.0.2'

parser = argparse.ArgumentParser(description='多路摄像头服务端')
parser.add_argument('--ip', type=str, default="0.0.0.0", help='IP')
parser.add_argument('--port', type=int, default=80,help='port,default:80')
args = parser.parse_args()

#-----------------------------------------

#根据时间自动生成文件名
def autoFileName (pre = '', ext = ''):
    ti = time.time()
    et = str(ti)[-7:-4]
    filename = ('%s%s%s' % (pre, time.strftime('%Y%m%d%H%M%S',time.localtime(ti)) + et  , ext))
    return filename

# 摄像头
class VideoCamera(object):
    def __init__(self, index=0):
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        self.video = cv2.VideoCapture(index)
        # If you decide to use video.mp4, you must have this file in the folder
        # as the main.py.
        # self.video = cv2.VideoCapture('video.mp4')
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):
        success, image = self.video.read()
        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
        if success:
            ret, jpeg = cv2.imencode('.jpg', image)
            return jpeg.tobytes()
        else:
            return None

    def cap(self, path='./', imagefile='', delay=1):
        #time.sleep(0.5)
        #success, frame = self.video.read()
        #print('success:', success)
        #time.sleep(delay)
        success, frame = self.video.read()
        print('success:', success)
        if not success:
            return ""
        if imagefile=="":
            imagefile = autoFileName('cap_', '.jpg')
        filename = os.path.join(path,imagefile)
        cv2.imwrite(filename, frame)
        return filename



#相机推流
def gen(camera):
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

#-----------------------------------------

# Flask 服务端
def HttpServer (args):

    # 参数处理
    ip = args.ip
    port = args.port

    logging.info( ('多路摄像头服务端 v' + gblVersion ).center(40, '-') )

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)
    work_path = './static/work/'

    @app.route('/favicon.ico')
    def favicon():
        return app.send_static_file('images/favicon.ico')

    @app.route('/')
    def index():
        version = gblVersion
        text_title = "多路摄像头监控"
        return render_template('index.html', **locals())
    
    @app.route('/cap', methods=['POST'])
    def cap():
        res = {}
        txt_id = request.values.get("id")
        print("txt_id: %s" % txt_id)
        # 生成临时工作目录
        '''
        tmp_folder = autoFileName()
        path = os.path.join(work_path, tmp_folder + '/')
        if not os.path.exists(path):
            os.mkdir(path)
        '''
        index = int(txt_id)
        camera = VideoCamera(index)
        cap = camera.cap(path=work_path, imagefile=autoFileName('cap_', '.jpg'))
        print('cap:%s' % cap)
        del camera

        if cap_0:
            res['status'] = 'OK'
        else:
            res['status'] = 'Error'
        return jsonify(res)
  
    
    #相机推流
    @app.route('/video_feed', methods=['GET'])
    def video_feed():
        index = request.values.get("i")
        print("index:", index)
        if not index:
            index = 0
        else:
            index = int(index)
        camera = VideoCamera(index)
        return Response(gen(camera), mimetype='multipart/x-mixed-replace; boundary=frame')
 
    logging.info('正在启动服务，请稍候...')
    app.run(
        host = args.ip,
        port = args.port,
        debug = True 
    )

if __name__ == '__main__':
    #################################################################################################
    # 指定日志
    logging.basicConfig(level = logging.DEBUG,
                format='[%(asctime)s] %(filename)s [line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename= os.path.join('./', 'server.log'),
                filemode='w'
                )
    #################################################################################################
    # 定义一个StreamHandler，将 INFO 级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象#
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(filename)s [line:%(lineno)d] %(levelname)s %(message)s')
    #formatter = logging.Formatter('[%(asctime)s]%(levelname)s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    #################################################################################################

    HttpServer(args)
