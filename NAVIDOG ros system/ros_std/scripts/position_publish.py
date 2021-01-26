#!/usr/bin/env python3

import math
import time
import rospy
import threading
import cv2 as cv
import numpy as np
from std_msgs.msg import String
from sensor_msgs.msg import Imu
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, Transform
from rtabmap_ros.msg import OdomInfo
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
import paho.mqtt.client as mqtt
from squaternion import Quaternion
from cv_bridge import CvBridge

_SERVER = 'mqtt_broker_adress'
_GroundZeroDeg = 0.0
	
def connect(client, userdata,flags,rc):
	if rc == 0:
		print("connection success")
	else:
		print("connection fail")

def disconnect(client, userdata,flags,rc = 0):
	print(str(rc))

client = None
def init_mqtt():
	global client
	client = mqtt.Client()
	client.on_connect = connect
	client.on_disconnect = disconnect
	client.connect(_SERVER, 1883)
	client.loop_start()

def deg_correction(deg):
	if deg < 0:
		while True :
			deg  += 360
			if deg > 0: break
		
	if deg > 360:
		while True:
			deg -= 360
			if deg < 360 : break

	return deg

def ground_deg_correction(deg):
	ground_deg = deg - _GroundZeroDeg

	if ground_deg < 0:
		ground_deg += 360

	return ground_deg

def rad_correction(rad):
	if rad < 0:
		while True :
			rad  += 2*math.pi
			if rad > 0: break
		
	if rad > 2*math.pi:
		while True:
			rad -= 2*math.pi
			if rad < 2*math.pi : break
	
	return rad

def rad_center(rad1, rad2):
	
	avg_rad = (rad1+rad2)/2
	if ((rad1 < (math.pi/2)) and (rad2 > ((math.pi/2)*3))) or ((rad2 < (math.pi/2)) and (rad1 > ((math.pi/2)*3))):
		avg_rad = avg_rad + (math.pi/2)
	
	return avg_rad

acc_sensitivity = 4
imu_yaw = None
imu_move = None
def imu_callback(data):
	global imu_yaw, imu_move
	acc_x = data.linear_acceleration.x
	acc_y = data.linear_acceleration.y
	acc_z = data.linear_acceleration.z

	qua_z = data.orientation.z
	qua_w = data.orientation.w

	qua = Quaternion(qua_w,qua_z,0,0)

	eul = qua.to_euler(degrees=True)
	yaw = eul[0]

	yaw = round(deg_correction(yaw))
	
	moved = 0

	if round(abs(acc_x*10),2) > acc_sensitivity or round(abs(acc_y*10),2) > acc_sensitivity or round(abs(acc_z*10),2) > acc_sensitivity:
		moved = 1

	imu_yaw = yaw
	imu_move = moved

visodom_check = 1
def camError_callback(error_check):
	global visodom_check
	check_1 = error_check.guessVelocity.translation.x
	check_2 = error_check.guessVelocity.translation.y
	check_3 = error_check.guessVelocity.translation.z
	check_4 = error_check.guessVelocity.rotation.x
	check_5 = error_check.guessVelocity.rotation.y
	check_6 = error_check.guessVelocity.rotation.z
	check_7 = error_check.guessVelocity.rotation.w
	if(check_1 == 0.0) and (check_2 == 0.0) and (check_3 == 0.0) and (check_4 == 0.0) and (check_5 == 0.0) and (check_6 == 0.0) and (check_7 == 0.0):
		visodom_check = 0
	else:
		visodom_check = 1

odom_mult = 10
visodom_x = 0
visodom_y = 0
visodom_deg_get = 0
visodom_temp_x = 0
visodom_temp_y = 0
visodom_save_x = 0
visodom_save_y = 0
visodom_mult_x = 0
visodom_mult_y = 0
def visodom_callback(visodomP):
	global visodom_x, visodom_y, visodom_deg_get, visodom_temp_x, visodom_temp_y, visodom_save_x, visodom_save_y, visodom_mult_x, visodom_mult_y

	visodom_move = imu_move
	visodom_move = 1
	if visodom_move == 1:
		visodom_z = visodomP.pose.pose.orientation.z
		visodom_w = visodomP.pose.pose.orientation.w
		qua = Quaternion(visodom_w,visodom_z,0,0)

		eul = qua.to_euler(degrees=True)
		visodom_deg_get = eul[0]

		visodom_deg_get = round(deg_correction(visodom_deg_get))

		if visodom_check == 1:
			visodom_x = visodomP.pose.pose.position.x + visodom_save_x
			visodom_y = visodomP.pose.pose.position.y + visodom_save_y

			if (abs(visodom_x - visodom_temp_x) >= 1) or (abs(visodom_y - visodom_temp_y) >= 1):
				visodom_save_x = visodom_temp_x - visodomP.pose.pose.position.x
				visodom_save_y = visodom_temp_y - visodomP.pose.pose.position.y
				visodom_x = visodom_temp_x
				visodom_y = visodom_temp_y
			
			visodom_temp_x = visodom_x
			visodom_temp_y = visodom_y
			
		visodom_mult_x = (round(visodom_x,2) * odom_mult)
		visodom_mult_y = (round(visodom_y,2) * odom_mult)

visodom_temp_calc_x = 0
visodom_temp_calc_y = 0
visodom_temp_current_x = 0
visodom_temp_current_y = 0
scanodom_save_x = 0
scanodom_save_y = 0
scanodom_temp_x = 0
scanodom_temp_y = 0
scanodom_temp_calc_x = 0
scanodom_temp_calc_y = 0
scanodom_temp_current_x = 0
scanodom_temp_current_y = 0

visodom_que = []
scanodom_que = []

scanodom_zero_deg_check = 0
scanodom_zero_deg = 0
def scanodom_callback(scanodomP):
	global scanodom_save_x, scanodom_save_y, scanodom_temp_x, scanodom_temp_y, visodom_temp_calc_x, visodom_temp_calc_y, visodom_temp_current_x, visodom_temp_current_y, scanodom_temp_calc_x, scanodom_temp_calc_y,\
		scanodom_temp_current_x, scanodom_temp_current_y, visodom_save_x, visodom_save_y, visodom_que,scanodom_que, scanodom_zero_deg_check, scanodom_zero_deg

	scanodom_move = imu_move
	scanodom_move = 1

	if scanodom_move == 1:
		scanodom_z = scanodomP.pose.pose.orientation.z
		scanodom_w = scanodomP.pose.pose.orientation.w
		qua = Quaternion(scanodom_w,scanodom_z,0,0)

		eul = qua.to_euler(degrees=True)
		scanodom_deg = eul[0]

		scanodom_deg = round(deg_correction(scanodom_deg))

		if scanodom_zero_deg_check == 0:
			scanodom_zero_deg =  scanodom_deg
			scanodom_zero_deg_check = 1
			
		visodom_deg = visodom_deg_get

		imu_deg = imu_yaw
		imu_rad = imu_deg * (math.pi/180)

		scanodom_x = scanodomP.pose.pose.position.x + scanodom_save_x
		scanodom_y = scanodomP.pose.pose.position.y + scanodom_save_y

		if (abs(scanodom_x - scanodom_temp_x) >= 1) or (abs(scanodom_y - scanodom_temp_y) >= 1):
			scanodom_save_x = scanodom_temp_x - scanodomP.pose.pose.position.x
			scanodom_save_y = scanodom_temp_y - scanodomP.pose.pose.position.y
			scanodom_x = scanodom_temp_x
			scanodom_y = scanodom_temp_y
		
		scanodom_temp_x = scanodom_x
		scanodom_temp_y = scanodom_y
			
		scanodom_calc_x = (round(scanodom_x,2) * odom_mult)
		scanodom_calc_y = (round(scanodom_y,2) * odom_mult)

		visodom_calc_x = visodom_mult_x
		visodom_calc_y = visodom_mult_y
	
		visodom_deg_diff = 0

		visodom_deg_diff = imu_deg - visodom_deg
		visodom_rad_diff = (visodom_deg_diff)*(math.pi/180)

		visodom_current_x = (math.cos(visodom_rad_diff)*(visodom_calc_x - visodom_temp_calc_x) - math.sin(visodom_rad_diff)*(visodom_calc_y - visodom_temp_calc_y))
		visodom_current_y = (math.sin(visodom_rad_diff)*(visodom_calc_x - visodom_temp_calc_x) + math.cos(visodom_rad_diff)*(visodom_calc_y - visodom_temp_calc_y))

		visodom_coord_rad = math.atan2(visodom_current_y, visodom_current_x)
		visodom_coord_rad = rad_correction(visodom_coord_rad)
		visodom_coord_rad_diff = abs(imu_rad - visodom_coord_rad)

		visodom_correct = 0

		scanodom_deg_diff = 0
		scanodom_deg_diff = imu_deg - scanodom_deg
		scanodom_rad_diff = (scanodom_deg_diff)*(0.017)
		scanodom_current_x = (math.cos(scanodom_rad_diff)*(scanodom_calc_x - scanodom_temp_calc_x) - math.sin(scanodom_rad_diff)*(scanodom_calc_y - scanodom_temp_calc_y))
		scanodom_current_y = (math.sin(scanodom_rad_diff)*(scanodom_calc_x - scanodom_temp_calc_x) + math.cos(scanodom_rad_diff)*(scanodom_calc_y - scanodom_temp_calc_y))
		scanodom_coord_rad = math.atan2(scanodom_current_y, scanodom_current_x)
		scanodom_coord_rad = rad_correction(scanodom_coord_rad)

		scanodom_coord_rad_diff = abs(imu_rad - scanodom_coord_rad)

		scanodom_correct = 0
		if scanodom_coord_rad_diff >= (math.pi * 0.085):
			scanodom_rad_diff = 0
			scanodom_correct = 1

			scanodom_rad_diff = rad_correction(scanodom_rad_diff)
			scanodom_coord_rad_diff = imu_rad - scanodom_coord_rad

			scanodom_current_x_r = scanodom_current_x
			scanodom_current_y_r = scanodom_current_y

			scanodom_current_x = (math.cos(scanodom_rad_diff)*(scanodom_current_x_r) - math.sin(scanodom_rad_diff)*(scanodom_current_y_r))
			scanodom_current_y = (math.sin(scanodom_rad_diff)*(scanodom_current_x_r) + math.cos(scanodom_rad_diff)*(scanodom_current_y_r))

		visodom_current_x = visodom_current_x + visodom_temp_current_x
		visodom_current_y = visodom_current_y + visodom_temp_current_y
		
		scanodom_current_x = scanodom_current_x + scanodom_temp_current_x
		scanodom_current_y = scanodom_current_y + scanodom_temp_current_y
		

		visodom_que.append((visodom_current_x,visodom_current_y))
		scanodom_que.append((scanodom_current_x,scanodom_current_y))
		
		if len(visodom_que) == 2:
			(visodom_x_1, visodom_y_1) = visodom_que[0]
			(visodom_x_2, visodom_y_2) = visodom_que[1]

			(scanodom_x_1, scanodom_y_1) = scanodom_que[0]
			(scanodom_x_2, scanodom_y_2) = scanodom_que[1]
			
			visodom_distance = math.sqrt(math.pow(visodom_x_2-visodom_x_1,2) + math.pow(visodom_y_2-visodom_y_1,2))
			scanodom_distance = math.sqrt(math.pow(scanodom_x_2-scanodom_x_1,2) + math.pow(scanodom_y_2-scanodom_y_2,2))

			if abs(visodom_distance - scanodom_distance) >= 0.5:
				visodom_correct = 1
				visodom_x_plus = scanodom_x_2 - scanodom_x_1
				visodom_y_plus = scanodom_y_2 - scanodom_y_1

				visodom_current_x = visodom_current_x + visodom_x_plus
				visodom_current_y = visodom_current_y + visodom_y_plus

			visodom_que[0] = (visodom_current_x,visodom_current_y)
			visodom_que.pop()

			scanodom_que[0] = scanodom_que[1]
			scanodom_que.pop()

		visodom_temp_current_x = visodom_current_x
		visodom_temp_current_y = visodom_current_y
		visodom_temp_calc_x = visodom_calc_x
		visodom_temp_calc_y = visodom_calc_y

		scanodom_temp_current_x = scanodom_current_x
		scanodom_temp_current_y = scanodom_current_y
		scanodom_temp_calc_x = scanodom_calc_x
		scanodom_temp_calc_y = scanodom_calc_y

		if visodom_check == 1:
			pub_msg = '/' + str(visodom_current_x) + '/' + str(visodom_current_y) + '/' + str(imu_deg)
			client.publish('POSITION', pub_msg, 1)
			
if __name__=='__main__':
	try:
		init_mqtt()
		rospy.init_node("position_publish",anonymous=True)
		rospy.Subscriber('imu/data',Imu, imu_callback)
		rospy.Subscriber("/rtabmap/odom_info",OdomInfo,camError_callback)
		rospy.Subscriber("/stereo_odometry",Odometry,visodom_callback)
		rospy.Subscriber("/slamware_ros_sdk_server_node/odom", Odometry, scanodom_callback) 
		rospy.spin()
		
	except KeyboardInterrupt: pass