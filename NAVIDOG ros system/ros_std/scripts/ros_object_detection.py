#!/usr/bin/env python3
import rospy
import os
import time
import threading
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
import sys
sys.path.append('your work space path/src/ros_std/scripts/object_detection')
import tensorflow as tf
import cv2 as cv
import paho.mqtt.client as mqtt
import math
from object_detection.utils import label_map_util
from object_detection.utils import object_detc_vis_utils as vis

_SERVER = 'mqtt_broker_adress'
DETECT_OBJECT = ["person","bicycle","car","motorcycle","bench","umbrella","suitcase","bottle","chair","couch","potted plant","dining table","tv","laptop","vase"]

blank = np.zeros((480,640,3),np.uint8)
height,width,_ = blank.shape

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

left_frame_his = None
object_bound = []
def init_OBD_graph():
	global left_frame_his, object_bound
	image_np = cv.imread(os.path.join('your work space path/src/ros_std/scripts','test_pic.jpg'),cv.IMREAD_COLOR)

	_PATH_MODEL = 'your work space path/src/ros_std/scripts/object_detection_model.pb'
	_PATH_LABEL = 'your work space path/src/ros_std/scripts/object_detection_label.pbtxt'

	NUM_CLASSES = 90
	detection_graph = tf.Graph()
	with detection_graph.as_default():
		od_graph_def =  tf.compat.v1.GraphDef()
		with tf.io.gfile.GFile(_PATH_MODEL, 'rb') as fid:
			serialized_graph = fid.read()
			od_graph_def.ParseFromString(serialized_graph)
			tf.import_graph_def(od_graph_def, name='')

	label_map = label_map_util.load_labelmap(_PATH_LABEL)
	categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
	category_index = label_map_util.create_category_index(categories)
	config = tf.ConfigProto()
	config.gpu_options.allow_growth = True

	with detection_graph.as_default():
		with tf.Session(graph=detection_graph, config = config) as sess:

			print("--------------------------------object_detection_set--------------------------------")
			if image_np is not None:
				print("test_set")
				image_np_expanded = np.expand_dims(image_np, axis=0)
				image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
				boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
				scores = detection_graph.get_tensor_by_name('detection_scores:0')
				classes = detection_graph.get_tensor_by_name('detection_classes:0')
				num_detections = detection_graph.get_tensor_by_name('num_detections:0')
				(boxes, scores, classes, num_detections) = sess.run([boxes, scores, classes, num_detections],feed_dict={image_tensor: image_np_expanded})
				print("--------------------------------object_detection_ready--------------------------------")

			while True:
				time.sleep(0.1)
				try:
					if left_frame_his is not None and len(object_bound) != 0:

						scan_bound = object_bound
						object_bound = []

						object_pub = None
						publish_pose_name=[]

						recog_frame = left_frame_his.copy()
						cam_frame_show = left_frame_his.copy()
						publish_pose_name = []

						for each_bound in scan_bound:
							(x_1,x_2) = each_bound
							object_position = POSITION_RECOGNIZE(x_1, x_2)
							cv.putText(cam_frame_show,object_position,(x_1,250),cv.FONT_HERSHEY_SIMPLEX,0.5,(0, 0, 255),1)
							cv.line(cam_frame_show,(x_1,240),(x_2,240),(0,0,255),2)

						image_np = recog_frame
						image_np_expanded = np.expand_dims(image_np, axis=0)
						image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
						boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
						scores = detection_graph.get_tensor_by_name('detection_scores:0')
						classes = detection_graph.get_tensor_by_name('detection_classes:0')
						num_detections = detection_graph.get_tensor_by_name('num_detections:0')
						(boxes, scores, classes, num_detections) = sess.run([boxes, scores, classes, num_detections],feed_dict={image_tensor: image_np_expanded})

						image_show, category_name, bound_box, detection_score = vis.visualize_boxes_and_labels_on_image_array(
							image_np,
							np.squeeze(boxes),
							np.squeeze(classes).astype(np.int32),
							np.squeeze(scores),
							category_index,
							use_normalized_coordinates=True,
							line_thickness=1)

						cv.imshow("name", image_show)
						if cv.waitKey(25) & 0xFF == ord('q'):
							cv.destroyAllWindows()

						if bound_box[0] != 0 and bound_box[0] != (0,0,0,0) :
							
							for bound_cnt in range(len(bound_box)):
								(x_left, x_right, _, _) = bound_box[bound_cnt]
								bound_center  = (x_left+x_left)/2

								if len(scan_bound) != 0:
									for each_bound in scan_bound:
										(x_1, x_2) = each_bound
										if (((x_1-20) <= bound_center) and (bound_center <= (x_2+20))):
											object_name = category_name[bound_cnt]
											object_position = POSITION_RECOGNIZE(x_1, x_2)

											if object_name in DETECT_OBJECT:
												object_pub = str(object_name) + "/" + str(object_position)
												publish_pose_name.append(object_pub)
									
											else : 
												object_pub = "object" + "/" + str(object_position)
												publish_pose_name.append(object_pub)
									
											scan_bound.remove((x_1, x_2))
											break
							
							if len(scan_bound) != 0:
								for each_bound in scan_bound:
									(x_1, x_2) = each_bound
									object_position = POSITION_RECOGNIZE(x_1, x_2)
									object_pub = "object" + "/" + str(object_position)
									publish_pose_name.append(object_pub)

						
						elif len(scan_bound) != 0:
							for each_bound in scan_bound:
								(x_1, x_2) = each_bound
								object_position = POSITION_RECOGNIZE(x_1, x_2)
								object_pub = "object" + "/" + str(object_position)
								publish_pose_name.append(object_pub)

						if len(publish_pose_name) != 0:
							publish_pose_name = set(publish_pose_name)
							print(str(publish_pose_name))
							
							client.publish('OBJECT1', str(publish_pose_name),1)

						cv.imshow("object", cam_frame_show)
						if cv.waitKey(25) & 0xFF == ord('q'):
							cv.destroyAllWindows()

				except KeyboardInterrupt:
					return

left_frame = None
def cam_callback(data):
	global left_frame
	get_frame = CvBridge().imgmsg_to_cv2(data, "bgr8")
	if get_frame is not None:
		left_frame = get_frame

def get_x(point_deg, point_range):
	standard_x = 330
	mult_y = 160
	distance_y = round(mult_y * point_range)
	point_rad = point_deg * ((math.pi)/180)
	X = distance_y*math.tan(-point_rad)+standard_x

	return round(X)

center_temp = 0

def POSITION_RECOGNIZE(Xl,Xr):
    global center_temp

    object_center = (Xl+Xr)/2

    center_diff = abs(object_center - center_temp)

    center_temp = object_center


    if ((Xl<(width/3)) and (Xr>(width*2/3))):
        return "IGNORE"

    if (center_diff <= 35):
        return "IGNORE"

    if (width/3) <= object_center <= (width*4/9):
        return "LEFT"
    elif (width*4/9) < object_center <= (width*5/9):
        return "CENTER"
    elif (width*5/9) < object_center <= (width*2/3):
        return "RIGHT"
    else :
        return "IGNORE"
						
center_pointX = 320
center_pointY = 0
def OBJECT_callback(data):
	global object_bound, left_frame, left_frame_his
	msg_sub = str(data.data)
	msg_parse = msg_sub.split('|')
	x_bound = []
	if left_frame is not None:

		for PointCloud in msg_parse:
			object_range = PointCloud.split('/')
			if len(object_range) != 1:
				leftDEG = int(object_range[3])
				leftRNG = float(object_range[4])
				rightDEG = int(object_range[5])
				rightRNG = float(object_range[6])

				x_1 = get_x(leftDEG,leftRNG)
				x_2 = get_x(rightDEG,rightRNG)

				object_position = POSITION_RECOGNIZE(x_1, x_2)
				if object_position != "IGNORE":
					x_bound.append((x_1,x_2))

		if len(x_bound) != 0:
			object_bound = x_bound
			left_frame_his = left_frame
				
if __name__ == '__main__':
	try:
		init_mqtt()
		rospy.init_node("ros_object_detection",anonymous=True)
		rospy.Subscriber("/stereo/left/image_rect",Image,cam_callback)
		rospy.Subscriber("OBJECT", String, OBJECT_callback)
		object_detection = threading.Thread(target=init_OBD_graph)
		object_detection.start()
		object_detection.join()
		rospy.spin()
	except rospy.ROSInterruptException:

		pass
		
