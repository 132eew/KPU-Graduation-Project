#!/usr/bin/env python3
import cv2 as cv
import rospy
import numpy as np
import os
import time
import paho.mqtt.client as mqtt
import threading
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from button_recognition.msg import recognition
from button_recognition.msg import recog_result
from button_recognition.srv import *
from ocr_rcnn_lib.button_recognition import ButtonRecognizer

_SERVER = 'mqtt_broker_adress'

image_input_flag = 1
class RecognitionService:
	def __init__(self, model):
		self.model = model
		assert isinstance(self.model, ButtonRecognizer)

	def perform_recognition(self, request):
		global image_input_flag
		image_input_flag = 0
		print("image_input_flag: " + str(image_input_flag))
		image_np = request

		if image_np.shape != (640, 480):
			image_np = cv.resize(image_np, dsize=(640, 480), interpolation=cv.INTER_AREA)

		recognitions = self.model.predict(image_np)
		
		button_bound = []
		for item in recognitions:
			
			if item[1] > 0.99:
				button_bound.append((int(item[0][1] * image_np.shape[1]), int(item[0][0] * image_np.shape[0]), int(item[0][3] * image_np.shape[1]), int(item[0][2] * image_np.shape[0])))

			if len(button_bound) == 2:
				break

		if len(button_bound) == 2:
			return button_bound

		else:
			image_input_flag = 1
			return 'RE' 
					
def histogram_equalization(image):
		image_hsv = cv.cvtColor(image,cv.COLOR_RGB2HSV)
		h,s,v = cv.split(image_hsv)
		eq_v = cv.equalizeHist(v)
		eq_image = cv.merge([h,s,eq_v])
		image_rt = cv.cvtColor(eq_image,cv.COLOR_HSV2RGB)
		return image_rt

def adjust_gamma(image, gamma=1.0):
		invGamma = 1.0 / gamma
		table = np.array([((i / 255.0) ** invGamma) * 255
		for i in np.arange(0, 256)]).astype("uint8")
		return cv.LUT(image, table)

def image_value_average(image):

	button_h, button_w = image.shape

	button_left = int(button_w/3)
	button_right = int(button_w*(2/3))
	button_top = int(button_h/3)
	button_down = int(button_h*(2/3))

	button_center = image[button_top:button_down, button_left:button_right]

	w = len(button_center[0])
	h = len(button_center)
	div_sum = w*h
	avg_first = []
	for cnt in range(h): avg_first.append(sum(button_center[cnt]))

	image_value_avg = sum(avg_first)/div_sum

	return [image_value_avg, button_center]

def IMAGE_BINARY(image):

		image_resize = cv.resize(image, dsize=(200, 200), interpolation=cv.INTER_AREA)
		image_his = histogram_equalization(image_resize)
		cv.imshow('his', image_his)
		image_gray = cv.cvtColor(image_his, cv.COLOR_BGR2GRAY)
		cv.imshow('gray', image_gray)
		image_blur = cv.GaussianBlur(image_gray, (11,11), 0)
		cv.imshow('blur', image_blur)
		image_threshold = cv.threshold(image_blur,200,255,cv.THRESH_BINARY)[1]
		cv.imshow('bin', image_threshold)
		if cv.waitKey(25) & 0xFF == ord('q'):
			cv.destroyAllWindows()

		return image_threshold

def BUTTONRECOGNIZED(image, btu_box, btd_box):
		(btu_left,btu_top,btu_right,btu_bottom) = btu_box
		(btd_left, btd_top, btd_right, btd_bottom) = btd_box
		if image.shape != (640, 480):
			image = cv.resize(image, dsize=(640, 480), interpolation=cv.INTER_AREA)

		image_copy = image.copy()
		button_up = image_copy[round(btu_top):round(btu_bottom),round(btu_left):round(btu_right)]
		button_down = image_copy[round(btd_top):round(btd_bottom),round(btd_left):round(btd_right)]
		print("get")
		
		button_up_binary = IMAGE_BINARY(button_up)
		button_down_binary = IMAGE_BINARY(button_down)

		up_on_off = image_value_average(button_up_binary)
		down_on_off = image_value_average(button_down_binary)

		up_on_off_value = up_on_off[0]
		up_on_off_image = up_on_off[1]
		
		down_on_off_value = down_on_off[0]
		down_on_off_image = down_on_off[1]

		print("up" + str(down_on_off_value))
		print("down" + str(up_on_off_value))

		cv.imshow('image', image)
		cv.imshow('down', button_down)
		cv.imshow('up', button_up)
		cv.imshow('down_b', button_down_binary)
		cv.imshow('up_b', button_up_binary)
		cv.imshow('down_b_center', down_on_off_image)
		cv.imshow('up_b_center', up_on_off_image)

		
		if cv.waitKey(25) & 0xFF == ord('q'):
			cv.destroyAllWindows()
		
		return [up_on_off_value,down_on_off_value]


elev_find = 0
def elevator_callback(client, userdata, msg):
	global elev_find
	msg_sub = str(msg.payload.decode("utf-8"))
	print("get from rpi" + msg_sub)
	if msg_sub != '0':
		elev_find = int(msg_sub)

def connect(client, userdata,flags,rc):
	if rc == 0:
		print("connection success")
	else:
		print("connection fail")
	client.subscribe('ELEVATORFIND',1)

def disconnect(client, userdata,flags,rc = 0):
	print(str(rc))

client = None
def init_mqtt():
	global client
	client = mqtt.Client()
	client.on_connect = connect
	client.on_disconnect = disconnect
	client.message_callback_add('ELEVATORFIND',elevator_callback)
	client.connect(_SERVER, 1883)
	client.loop_start()

recognizer = None
def init_BD():
	global recognizer
	model = ButtonRecognizer(use_optimized=True)
	recognizer = RecognitionService(model)


	test_frame = cv.imread(os.path.join("your work space path/src/button_recognition/scripts","button.PNG"), cv.IMREAD_COLOR)
	
	elev_button_bound = recognizer.perform_recognition(test_frame)
	
	if elev_button_bound != 'RE':
		button_recog(elev_button_bound, test_frame)

timer = 0
def button_recog(button_bound, frame):
	global image_input_flag, timer, elev_find
	
	(_,bound_top1,_,_) = button_bound[0]
	(_,bound_top2,_,_) = button_bound[1]

	bound_up = None
	bound_down = None

	if bound_top1 > bound_top2:
		bound_up = button_bound[1]
		bound_down = button_bound[0]
	else: 
		bound_up = button_bound[0]
		bound_down = button_bound[1]

	(up, down) = BUTTONRECOGNIZED(frame, bound_up, bound_down)

	result = 0
	image_input_flag = 1
	print("image_input_flag: " + str(image_input_flag))

	if abs(up - down) <= 50 : result = 3
	elif up > down : result = 1
	else : result = 2

	timer += 1

	print("1 : up, 2 : down, 3 : all on/off, result : " + str(result))

	if timer == 3:
		client.publish("ELEVATOR1",str(result),1)
		timer = 0
		elev_find = 0

input_frame = None
def cam_callback(data):
	global elev_find, image_input_flag, input_frame

	elev_find = 1
	
	left_frame = None
	if elev_find != 0:
		left_frame = CvBridge().imgmsg_to_cv2(data, "bgr8")
		input_frame = left_frame

def start_button_recogniger():
	global input_frame, image_input_flag

	while True:
		try:
			elev_button_bound = 'RE'
			if input_frame is not None:
				cv.imshow('input_image',input_frame)
				if cv.waitKey(25) & 0xFF == ord('q'):
					cv.destroyAllWindows()
			if input_frame is not None and image_input_flag == 1:
				elev_button_bound = recognizer.perform_recognition(input_frame)
			if elev_button_bound != 'RE':
				button_recog(elev_button_bound, input_frame)

		except KeyboardInterrupt:
			return
	


if __name__ == '__main__':
	try:
		rospy.init_node('button_recognition_server', anonymous=True)
		init_BD()
		init_mqtt()
		rospy.Subscriber("/stereo/left/image_rect",Image,cam_callback)
		start_BD = threading.Thread(target = start_button_recogniger)
		start_BD.start()
		rospy.spin()
	except KeyboardInterrupt:
		recognizer.model.clear_session()