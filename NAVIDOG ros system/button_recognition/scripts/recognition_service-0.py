#!/usr/bin/env python3
import cv2 as cv
import rospy
import numpy as np
import paho.mqtt.client as mqtt
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from button_recognition.msg import recognition
from button_recognition.msg import recog_result
from button_recognition.srv import *
from ocr_rcnn_lib.button_recognition import ButtonRecognizer

_SERVER = '192.168.137.21'

class RecognitionService:
	def __init__(self, model):
		self.model = model
		assert isinstance(self.model, ButtonRecognizer)

	def perform_recognition(self, request):
		image_np = request

		if image_np.shape != (480, 640):
			image_np = cv.resize(image_np, dsize=(640, 480), interpolation=cv.INTER_AREA)

		recognitions = self.model.predict(image_np)

		button_bound = [0,0]
		
		for item in recognitions:
			print(item)
			if item[2] == 'up' or item[2] == ')':
				if item[1] > 0.95:
					print("up")
					button_bound[0] = (int(item[0][1] * image_np.shape[1]), int(item[0][0] * image_np.shape[0]), int(item[0][3] * image_np.shape[1]), int(item[0][2] * image_np.shape[0]))
			
			if item[2] == 'down' or item[2] == '?':
				if item[1] > 0.95:
					print("down")
					button_bound[1] = (int(item[0][1] * image_np.shape[1]),int(item[0][0] * image_np.shape[0]),int(item[0][3] * image_np.shape[1]),int(item[0][2] * image_np.shape[0]))

		if 0 not in button_bound:
			return button_bound

		else:
			return 'RE' 

			# sample.y_min = int(item[0][0] * image_np.shape[0])
			# sample.x_min = int(item[0][1] * image_np.shape[1])
			# sample.y_max = int(item[0][2] * image_np.shape[0])
			# sample.x_max = int(item[0][3] * image_np.shape[1])
			# sample.score = item[1]
			# sample.text = item[2]
					
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
		image_hsv = cv.cvtColor(image, cv.COLOR_RGB2HSV)
		_, _, v = cv.split(image_hsv)
		value_range = len(v)
		w = len(v[0])
		h = len(v)
		div_sum = w*h
		avg_first = []
		for cnt in range(value_range): avg_first.append(sum(v[cnt]))
		image_value_avg = sum(avg_first)/div_sum
		return image_value_avg

def IMAGE_BINARY(image):
		lower_red = (0, 100, 100)
		upper_red = (200, 255, 255)
		image = cv.resize(image,(100,100))
		image = histogram_equalization(image)
		img_hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
		img_mask = cv.inRange(img_hsv, lower_red, upper_red)
		img_result = cv.bitwise_and(image, image, mask=img_mask)
		img_result = cv.cvtColor(img_result,cv.COLOR_HSV2BGR)
		img_gray = cv.cvtColor(img_result, cv.COLOR_BGR2GRAY)
		_, img_binary = cv.threshold(img_gray, 125, 255, cv.THRESH_BINARY_INV | cv.THRESH_OTSU)
		image_return = cv.cvtColor(img_binary,cv.COLOR_GRAY2BGR)
		return image_return

def BUTTONRECOGNIZE(image, btu_box, btd_box):
		(btu_left,btu_right,btu_top,btu_bottom) = btu_box
		(btd_left, btd_right, btd_top, btd_bottom) = btd_box

		print((btu_left,btu_right,btu_top,btu_bottom))
		print((btd_left, btd_right, btd_top, btd_bottom))
		image_copy = image.copy()
		button_up = image_copy[round(btu_top):round(btu_bottom),round(btu_left):round(btu_right)]
		button_down = image_copy[round(btd_top):round(btd_bottom),round(btd_left):round(btd_right)]

	

		button_up_binary = IMAGE_BINARY(button_up)
		button_down_binary = IMAGE_BINARY(button_down)
		up_on_off = image_value_average(button_up_binary)

		cv.imshow('image', image)
		cv.imshow('down', button_down)
		cv.imshow('up', button_up)
		cv.imshow('down_b', button_down_binary)
		cv.imshow('up_b', button_up_binary)

		if cv.waitKey(25) & 0xFF == ord('q'):
			cv.destroyAllWindows()

		print("up" + str(up_on_off))
		down_on_off = image_value_average(button_down_binary)
		print("down" + str(down_on_off))
		return [up_on_off,down_on_off]
		#if up_on_off - down_on_off >= 10: return 2 #down
		#elif up_on_off - down_on_off <= -10: return 1 #up
		#else : return 0 #none

elev_find = 0
def elevator_callback(client, userdata, msg):
	global elev_find
	msg_sub = str(msg.payload.decode("utf-8"))
	if msg_sub == '1':
		elev_find = 1

def connect(client, userdata,flags,rc):
	if rc == 0:
		print("connection success")
	else:
		print("connection fail")
	client.subscribe('ELEVFIND1',1)

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

def button_recog(button_bound, frame):
	(up, down) = BUTTONRECOGNIZE(frame, button_bound[0],button_bound[1])

	result = 0
	if abs(up - down) <= 10 : result = 3
	elif up > down : result = 1
	else : result = 2

	print("1 : up, 2 : down, 3 : all on/off, result : " + str(result))

	# client.publish("ELEVATOR",str(result),1)

left_frame_his = None
def cam_callback(data):
	global left_frame_his, elev_find
	elev_button_bound = None
	elev_find = 1
	if elev_find == 1:
		left_frame = CvBridge().imgmsg_to_cv2(data, "bgr8")
		if left_frame is not None:
			left_frame_his = histogram_equalization(left_frame)
			elev_button_bound = recognizer.perform_recognition(left_frame_his)
	elev_find = 0

	if elev_button_bound != 'RE' and elev_button_bound != None:
		button_recog(elev_button_bound, left_frame_his)

if __name__ == '__main__':
	try:
		rospy.init_node('button_recognition_server', anonymous=True)
		init_BD()
		# init_mqtt()
		rospy.Subscriber("/stereo/left/image_rect",Image,cam_callback)
		rospy.spin()
	except KeyboardInterrupt:
		recognizer.model.clear_session()