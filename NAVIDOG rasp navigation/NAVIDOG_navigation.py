from __future__ import division

import re
import sys
import os
import time
import paho.mqtt.client as mqtt
import pyaudio
import threading
import json
import math
import cv2 as cv
import numpy as np
import RPi.GPIO as gp
from soynlp.hangle import levenshtein
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from six.moves import queue

######################################################################################
RATE = 16000
CHUNK = int(RATE / 60)

language_code = 'ko-KR' 
client = speech.SpeechClient()
config = types.RecognitionConfig(
    encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code=language_code)
streaming_config = types.StreamingRecognitionConfig(
    config=config,
    interim_results=True)
######################################################################################

######################################################################################
# print(cv.ocl.haveOpenCL())
# cv.ocl.setUseOpenCL(True)
# print(cv.ocl.useOpenCL())

current_floor = 7
destination_floor = 0
end_floor = 7
destination_name = None
research = None

comand_name_recog = None
destination_name_temp = None
destination_floor_temp = 0

pose_check = 0
el_cnt = 0
current_floor_pub = 0
path_len = 0
elev_cnt = 0
elev_print = 0
elev_pub = 0
(pxs, pys, pxe, pye) = (0,0,0,0)
(csx_st,csy_st,csx_ed,csy_ed) = (0,0,0,0)
walker_num_diff = 0

get_size = cv.imread('map1.png',cv.IMREAD_COLOR)
HEIGHT, WIDTH,_ = get_size.shape
CELL_DISTANCE = 30
BLACK_STAND = 205.0
ELEVATOR_B_BOUNDARY = []
TOILET_BOUNDARY = []
DESTINATION = []

comand_list = ["목적지","현재위치","목적지정보","재설정","목적지탐색"]
map_info = [["남자화장실","여자화장실","101","102","103","104""105","106","107","108","110","131","132","133","134","135","136","137"],["남자화장실","여자화장실","201","202","203","204""205","206","207","231A","231B","232","233","234","235","236","237"],["남자화장실","여자화장실","301","302","303""304""305","306","307","308","309","310","331","332","333","334","335","336","337","339""340","341","342","343","344","345"],["남자화장실","여자화장실","401","402""403","404","405","406","407","408","409","410","411","431","432","433","434","435","436","437","439","440","441","442","443","445","446"],["남자화장실","여자화장실","501","502","503","504","505","506","507","508","509","510","511","512","513","514","515","516","517","518","519","520","531","532A","532B","533","534","535","536","537","539","540","541","542","543","544","545"],["남자화장실","여자화장실","601","602","603","604","605","606","607","608","609","610","611","612","613","614","615","616","617","618","619","631","632","633","634","635","636","637","639","640""641","642","643","644"],["남자화장실","여자화장실","반납","701","702","703","704","705","706","707","708","709","710","711","712","713","714","715","716","717","718","719","719-1","720","721"]]
destination_info = {"남자화장실":"화장실","여자화장실":"화장실","101":"정밀분석소","102":"3차원정밀측정실","103":"3차원역설계실","104":"3차원측정지원실","105":"공용장비교육장","106":"공용장비지원센터행정실","107":"정밀분석지원실","108":"북카페","110":"세미나실","131":"연구실","132":"주카페","133":"연구실","134":"푸드코트","135":"연구실","136":"연구실","137":"연구실","201":"휴게실","202":"강의실","203":"강의실","204":"강의실","205":"강의실","206":"강의실","207":"산학융합캠퍼스사업단","231A":"중회의실","231B":"강의실","232":"에스제이테크","233":"연구실","234":"에스제이테크","235":"경기산학융합본부","236":"에스제이테크","237":"연구실","301":"휴게실","302":"강의실","303":"강의실","304":"강의실","305":"강의실","306":"강의실","307":"강의실","308":"강의실","309":"세미나실","310":"강의실","331":"에이피텍","332":"한국수출입은행","333":"경기산학융합본부","334":"메디싱크","335":"리비전","336":"메디싱크","337":"지에스티","339":"정한인프라","340":"로보모터스","341":"정한인프라","342":"연구실","343":"유씨드","344":"메디싱크","345":"나인원전자","401":"산학협력정책연구소","402":"공용컴퓨터실","403":"SOC응용설계실","404":"강의실","405":"강의실","406":"강의실","407":"강의실","408":"강사대기실","409":"강의실","410":"기업인재대학교학팀","411":"강의실","431":"스타폴리머","432":"연구실","433":"스타폴리머","434":"아인텍","435":"카로그","436":"유현산업","437":"연구실","439":"연구실","440":"그린리소스","441":"루미스탈","442":"연구실","443":"환경과사람들","445":"디아이티","446":"유현산업","501":"휴게실","502":"전자파실","503":"교수연구실","504":"교수연구실","505":"임베디드시스템실","506":"교수연구실","507":"교수연구실","508":"교수연구실","509":"교수연구실","510":"교수연구실","511":"마이크로프로세서실","512":"교수연구실","513":"교수연구실","514":"교수연구실","515":"교수연구실","516":"교수연구실","517":"IT소프트웨어실","518":"세미나실","519":"학과사무실","520":"학과사무실","531":"연구실","532A":"조영테크","532B":"연구실","533":"연구실","534":"연구실","535":"연구실","536":"연구실","537":"조영테크","539":"대양이엔지","540":"연구실","541":"연구실","542":"연구실","543":"연구실","544":"연구실","545":"연구실","601":"휴게실","602":"종합설계실","603":"교수연구실","604":"교수연구실","605":"교수연구실","606":"교수연구실","607":"교수연구실","608":"교수연구실","609":"교수연구실","610":"교수연구실","611":"통신시스템설계실","612":"교수연구실","613":"교수연구실","614":"교수연구실","615":"교수연구실","616":"교수연구실","617":"모바일프로그래밍실","618":"세미나실","619":"신호저리실습실","631":"원컨덕터트레이딩","632":"새롬시스","633":"원컨덕터","634":"리암솔루ㅜ션","635":"연실","636":"리암솔루션","637":"아이두잇","639":"연구실","640":"연구실","641":"연구실","642":"알커미스","643":"연구실","644":"연구실","반납":"반납장소","701":"휴게실","702":"강의실","703":"모바일클라우드","704":"화합물반도체관전소자","705":"강의실","706":"강의실","707":"플라즈마라이트실용화","708":"강의실","709":"강의실","710":"비즈니스솔루션","711":"고주파부품및시스템","712":"유비쿼터스네트워크","713":"전자부품및시스템","714":"멀티시스템통신시스템","715":"차세대포토닉스","716":"디지털서비스융합기술","717":"스마트배터리","718":"멀티미디어시스템국제협력","719":"관산화물반도체","719-1":"WCSLAB","720":"기업연구관","721":"기계진단및자동화"}

#########################################-MAP SET-#########################################
map1 = cv.imread('map1.png', cv.IMREAD_COLOR)
map2 = cv.imread('map2.png', cv.IMREAD_COLOR)
map3 = cv.imread('map3.png', cv.IMREAD_COLOR)
map4 = cv.imread('map4.png', cv.IMREAD_COLOR)
map5 = cv.imread('map5.png', cv.IMREAD_COLOR)
map6 = cv.imread('map6.png', cv.IMREAD_COLOR)
map7 = cv.imread('map7.png', cv.IMREAD_COLOR)

############################-PRE SET-############################
map_sec1 = cv.imread('map1_sec.png',cv.IMREAD_COLOR)
map_sec2 = cv.imread('map2_sec.png',cv.IMREAD_COLOR)
map_sec3 = cv.imread('map3_sec.png',cv.IMREAD_COLOR)
map_sec4 = cv.imread('map4_sec.png',cv.IMREAD_COLOR)
map_sec5 = cv.imread('map5_sec.png',cv.IMREAD_COLOR)
map_sec6 = cv.imread('map6_sec.png',cv.IMREAD_COLOR)
map_sec7 = cv.imread('map7_sec.png',cv.IMREAD_COLOR)

############################-DISPLAY SET-############################
map_dp1 = cv.imread('map1_dp.png',cv.IMREAD_COLOR)
map_dp2 = cv.imread('map2_dp.png',cv.IMREAD_COLOR)
map_dp3 = cv.imread('map3_dp.png',cv.IMREAD_COLOR)
map_dp4 = cv.imread('map4_dp.png',cv.IMREAD_COLOR)
map_dp5 = cv.imread('map5_dp.png',cv.IMREAD_COLOR)
map_dp6 = cv.imread('map6_dp.png',cv.IMREAD_COLOR)
map_dp7 = cv.imread('map7_dp.png',cv.IMREAD_COLOR)

map_list = [map1,map2,map3,map4,map5,map6,map7]
NAV_MAP = [map_sec1,map_sec2,map_sec3,map_sec4,map_sec5,map_sec6,map_sec7]
DP_MAP = [map_dp1,map_dp2,map_dp3,map_dp4,map_dp5,map_dp6,map_dp7]
######################################################################################

######################################################################################
gp.setmode(gp.BCM)
switch_L_pin = 21
switch_R_pin = 13
buzz_pin = 12
vibe_L_pin = 26
vibe_R_pin = 20

vibe_L_duty_mem = 0
vibe_R_duty_mem = 0

gp.setup(switch_L_pin, gp.IN, pull_up_down = gp.PUD_UP)
gp.setwarnings(False)
gp.setup(switch_R_pin, gp.IN, pull_up_down = gp.PUD_UP)
gp.setwarnings(False)
gp.setup(buzz_pin, gp.OUT)
gp.setwarnings(False) 
gp.setup(vibe_L_pin, gp.OUT)
gp.setwarnings(False)
gp.setup(vibe_R_pin, gp.OUT)
gp.setwarnings(False)

vibe_L = gp.PWM(vibe_L_pin,100)
vibe_R = gp.PWM(vibe_R_pin,100)

vibe_L.start(0)
vibe_R.start(0)
######################################################################################

######################################################################################
def connect(client, userdata,flags,rc):
    if rc == 0:
        print("connection success")
    else:
        print("connection fail")
        client.subscribe('POSITION',1)
        client.subscribe('ELEVATOR1',1)
        client.subscribe('OBJECT1',1)
        client.subscribe('test',1)

def disconnect(client, userdata,flags,rc = 0):
    print(str(rc))

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

def POSITION_callback(client, userdata, msg):
    global x, y, deg
    msg_sub = str(msg.payload.decode("utf-8"))
    msg_parse = msg_sub.split('/')
    (x_1, y_1) = (round(float(msg_parse[1])), round(float(msg_parse[2])))
    (x,y,deg) = (x_1, y_1, round(float(msg_parse[3])))

    deg = deg_correction(deg)

def OBJECT_alert(left, right):
    if left is not None:
        vibe_L.ChangeDutyCycle(100)
        time.sleep(0.3)
        vibe_L.ChangeDutyCycle(0)
        time.sleep(0.3)
        vibe_L.ChangeDutyCycle(100)
        time.sleep(0.3)
        vibe_L.ChangeDutyCycle(left)

    elif right is not None:
        vibe_R.ChangeDutyCycle(100)
        time.sleep(0.3)
        vibe_R.ChangeDutyCycle(0)
        time.sleep(0.3)
        vibe_R.ChangeDutyCycle(100)
        time.sleep(0.3)
        vibe_R.ChangeDutyCycle(right)
    
    else:
        vibe_L.ChangeDutyCycle(100)
        vibe_R.ChangeDutyCycle(100)
        time.sleep(0.3)
        vibe_L.ChangeDutyCycle(0)
        vibe_R.ChangeDutyCycle(0)
        time.sleep(0.3)
        vibe_L.ChangeDutyCycle(100)
        vibe_R.ChangeDutyCycle(100)
        time.sleep(0.3)
        vibe_L.ChangeDutyCycle(left)
        vibe_R.ChangeDutyCycle(right)
        
def OBJECTT_callback(client, userdata, msg):
    global vibe_L_duty_mem, vibe_R_duty_mem
    msg_sub = str(msg.payload.decode("utf-8"))
    msg_sub = msg_sub.replace("{","")
    msg_sub = msg_sub.replace("}","")
    msg_sub = msg_sub.replace("'","")
    
    msg_parse = msg_sub.split(',')
    object_pos = [0,0,0]

    say_text = ''

    for name_pos in msg_parse:
        name_pos_parse = name_pos.split('/')

        object_name = "장애물이"

        if name_pos_parse[0] == 'person': object_name = "사람이,"
        if name_pos_parse[0] == 'bicycle': object_name = "자전거가,"
        if name_pos_parse[0] == 'car': object_name = "차가,"
        if name_pos_parse[0] == 'motorcycle': object_name = "오토바이가,"
        if name_pos_parse[0] == 'bench': object_name = "의자가,"
        if name_pos_parse[0] == 'umbrella': object_name = "우산이,"
        if name_pos_parse[0] == 'suitcase': object_name = "가방이,"
        if name_pos_parse[0] == 'bottle': object_name = "화분이,"
        if name_pos_parse[0] == 'chair': object_name = "의자가,"
        if name_pos_parse[0] == 'couch': object_name = "쇼파가,"
        if name_pos_parse[0] == 'potted plant': object_name = "화분이,"
        if name_pos_parse[0] == 'dining table': object_name = "책상이,"
        if name_pos_parse[0] == 'tv': object_name = "티비가,"
        if name_pos_parse[0] == 'laptop': object_name = "컴퓨터가,"
        if name_pos_parse[0] == 'vase': object_name = "화분이,"

        say_text = say_text + object_name


        if str(name_pos_parse[1]) == 'LEFT':
            say_text = say_text + '왼쪽에,'
            object_pos[0] = 1
        
        elif str(name_pos_parse[1]) == 'CENTER':
            say_text = say_text + '앞에,'
            object_pos[1] = 1

        else :
            say_text = say_text + '오른쪽에,'
            object_pos[2] = 1

    say_text = say_text + '있습니다,'

    if object_pos[0] == 0:
        OBJECT_alert(vibe_L_duty_mem, None)
        say_text = say_text + '왼쪽으로,피하세요'
    
    elif object_pos[1] == 0:
        OBJECT_alert(None, vibe_R_duty_mem)
        say_text = say_text + '오른쪽으로,피하세요'

    else:
        OBJECT_alert(vibe_L_duty_mem, vibe_R_duty_mem)
        say_text = say_text + '전방에,장애물이,많습니다.잠시기다리신뒤,천천히,이동해주세요'

    start_TTS(say_text)

def ELEVATOR_callback(client, userdata, msg):
    msg_sub = str(msg.payload.decode("utf-8"))

    # 0: both off
    # 1: down on
    # 2: up on

    if current_floor > destination_floor:
        if msg_sub == '0' or msg_sub == '2':
            start_TTS('아래 버튼을 누른후 엘리베이터가 도착하면 탑승하세요')
            return
        else :
            start_TTS('엘리베이터가 오고있습니다. 엘리베이터가 도착하면 탑승하세요')
            return

    else:
        if current_floor == end_floor:
            start_TTS('아래 버튼을 누른후 엘리베이터가 도착하면 탑승하세요')
            return

        if msg_sub == '0' or msg_sub == '1':
            start_TTS('위 버튼을 누른후 엘리베이터가 도착하면 탑승하세요')
            return
        else :
            start_TTS('엘리베이터가 오고있습니다. 엘리베이터가 도착하면 탑승하세요')
            return

_SERVER_IN = 'mqtt_broker_adress'
client_id = str(time.time())
client_mq = mqtt.Client(client_id = client_id)
client_mq.on_connect = connect
client_mq.on_disconnect = disconnect
client_mq.message_callback_add('POSITION',POSITION_callback)
client_mq.message_callback_add('OBJECT1',OBJECTT_callback)
client_mq.message_callback_add('ELEVATOR1',ELEVATOR_callback)

client_mq.connect(_SERVER_IN, 1883)
client_mq.loop_start()
######################################################################################

class MicrophoneStream(object):
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        self._buff = queue.Queue()
        
        self.closed = True


    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)

with open('map_object_default.json', 'r') as map_json:
    map_object = json.load(map_json)
    START_BOUNDARY = []
    START_BOUNDARY = map_object['START'].split(',')
    START_BOUNDARY = list(map(int, START_BOUNDARY))

    EVEN = map_object['ELEVATOR']['EVEN_r'].split(',')
    ODD = map_object['ELEVATOR']['ODD_r'].split(',')
    ELEVATOR_B_BOUNDARY.append(EVEN)
    ELEVATOR_B_BOUNDARY.append(ODD)
    EVEN = map_object['ELEVATOR']['EVEN_l'].split(',')
    ODD = map_object['ELEVATOR']['ODD_l'].split(',')
    ELEVATOR_B_BOUNDARY.append(EVEN)
    ELEVATOR_B_BOUNDARY.append(ODD)

    ELEVATOR_B_BOUNDARY[0] = list(map(int, ELEVATOR_B_BOUNDARY[0]))
    ELEVATOR_B_BOUNDARY[1] = list(map(int, ELEVATOR_B_BOUNDARY[1]))
    ELEVATOR_B_BOUNDARY[2] = list(map(int, ELEVATOR_B_BOUNDARY[2]))
    ELEVATOR_B_BOUNDARY[3] = list(map(int, ELEVATOR_B_BOUNDARY[3]))

    TOILET_BOUND1 = map_object['TOILET']['toilet_m_r'].split(',')
    TOILET_BOUND2 = map_object['TOILET']['toilet_r_r'].split(',')
    TOILET_BOUND3 = map_object['TOILET']['toilet_m_l'].split(',')
    TOILET_BOUND4 = map_object['TOILET']['toilet_r_l'].split(',')
    TOILET_BOUNDARY.append(TOILET_BOUND1)
    TOILET_BOUNDARY.append(TOILET_BOUND2)
    TOILET_BOUNDARY.append(TOILET_BOUND3)
    TOILET_BOUNDARY.append(TOILET_BOUND4)
    TOILET_BOUNDARY[0] = list(map(int, TOILET_BOUNDARY[0]))
    TOILET_BOUNDARY[1] = list(map(int, TOILET_BOUNDARY[1]))
    TOILET_BOUNDARY[2] = list(map(int, TOILET_BOUNDARY[2]))
    TOILET_BOUNDARY[3] = list(map(int, TOILET_BOUNDARY[3]))

    for cnt in range(1, 8):
        floor = str(cnt) + 'F'

        des = map_object[floor][0]
        if len(des) != 1:
            for key in des:
                if key != 'DESTINATION' and len(key.split('_')) == 1:
                    DESTINATION.append([floor, key, des[key]])

    if len(DESTINATION) != 0:
        for int_des in DESTINATION:
            int_des[2] = list(map(int, int_des[2].split(',')))

X_OFFSET = 705
y_OFFSET = 2345
x = 0
y = 0
deg = 0

def STT_result(responses,comand_case):
    global comand_name_recog,current_floor,destination_floor,destination_name,destination_name_temp,destination_floor_temp, research
    num_chars_printed = 0
    response_list = []
    stt_end = False
    response_list_len = 0
    response_list_len_temp = 0
    comand_match = 0
    
    for response in responses:
        
        if not response.results:
            continue

        result = response.results[0]
        result_st = result.stability
        
        if not result.alternatives:
            continue
        
        transcript = result.alternatives[0].transcript
        
        overwrite_chars = ' ' * (num_chars_printed - len(transcript))
    
        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + '\r')
            response_char = transcript + overwrite_chars
            response_char = response_char.replace(' ','')
            response_list.append(str(transcript + overwrite_chars))
            sys.stdout.flush()
            num_chars_printed = len(transcript)

            if result_st >= 0.8:
                stt_end = True
        
        if stt_end == True:
            recog_result = response_list[-1]
            print(recog_result)
            print("==========================================STT END==========================================")
            num_chars_printed = 0

            comand_name = None
            if comand_case == 1: ## 명령어 입력
                for comand in comand_list:
                    if comand == recog_result:
                        comand_name = comand
                        break
                
                if comand_name is not None:
                    if comand_name == '목적지':
                        print("--목적지--")
                        start_TTS("목적지를말씀해주세요")
                        start_STT(10)
                        return

                    if comand_name == '현재위치':
                        print("--현재위치--")
                        start_TTS("현재위치는"+str(current_floor)+"층입니다")
                        start_TTS(str(current_floor)+"에는")
                        for current_floor_room in map_info[current_floor-1]:
                            start_TTS(str(current_floor_room))
                        start_TTS("가있습니다")
                        return
                        
                    if comand_name == '목적지정보':
                        print("--목적지정보--")
                        if destination_name is not None:
                            start_TTS(str(destination_name)+"은"+str(destination_floor)+"층이며")
                            start_TTS(str(destination_info[str(destination_name)])+"입니다")
                            return

                        else:
                            start_TTS("목적지가설정되어있지않습니다목적지를설정해주세요")
                            return
                       
                    if comand_name == '재설정':
                        print("--재설정--")
                        start_TTS("목적지를재설정합니다")
                        research = "Research"
                        destination_name = None
                        return
                       
                    if comand_name == '목적지탐색':
                        print("--목적지탐색--")
                        start_TTS("원하시는층을말씀해주세요")
                        start_STT(20)
                        return

                    return

                else:
                    comand_distance = []
                    for comand in comand_list:
                        comand_distance.append(levenshtein(comand, recog_result))
                    comand_list_index = comand_distance.index(min(comand_distance))
                    comand_name_recog = comand_list[comand_list_index]
                    start_TTS(comand_name_recog + "말씀하셨나요?")
                    start_STT(2)
                    return
          
            if comand_case == 2: ## 명령어 입력 재확인
                if recog_result == '예' or recog_result == '네'or recog_result == '어'or recog_result == '응'or recog_result == '맞아요':
                    if comand_name_recog is not None:
                        
                        if comand_name_recog == '목적지':
                            print("--목적지--")
                            start_TTS("목적지를말씀해주세요")
                            start_STT(10)
                            return

                        if comand_name_recog == '현재위치':
                            print("--현재위치--")
                            start_TTS("현재위치는"+str(current_floor)+"층입니다")
                            start_TTS(str(current_floor)+"에는")
                            for current_floor_room in map_info[current_floor-1]:
                                start_TTS(str(current_floor_room))
                            start_TTS("가있습니다")
                            return
                            
                        if comand_name_recog == '목적지정보':
                            print("--목적지정보--")
                            if destination_name is not None:
                                start_TTS(str(destination_name)+"은"+str(destination_floor)+"층이며")
                                start_TTS(str(destination_info[str(destination_name)])+"입니다")
                                return

                            else:
                                start_TTS("목적지가설정되어있지않습니다목적지를설정해주세요")
                                return
                        
                        if comand_name_recog == '재설정':
                            print("--재설정--")
                            start_TTS("목적지를재설정합니다")
                            research = "Research"
                            destination_name = None
                            return
                        
                        if comand_name_recog == '목적지탐색':
                            print("--목적지탐색--")
                            start_TTS("원하시는층을말씀해주세요")
                            start_STT(20)
                            return
                        
                        comand_name_recog = None
                        return

                else:  
                    start_TTS("다시말씀해주세요")
                    start_STT(1)
                    return

            if comand_case == 3: ## 목적지 입력 재확인
                if recog_result == '예' or recog_result == '네'or recog_result == '어'or recog_result == '응':
                    destination_floor = destination_floor_temp
                    destination_name = destination_name_temp
                    start_TTS(str(destination_name)+"으로안내를시작합니다")
                    return
                
                else:  
                    start_TTS("목적지를말씀해주세요")
                    start_STT(10)
                    return

            if comand_case == 10: ## 목적지 입력
                
                for cnt in range(len(map_info)):
                    for floor_room in map_info[cnt]:
                        if recog_result == floor_room:
                            destination_name = recog_result
                            destination_floor = cnt + 1
                            start_TTS(str(destination_name)+"으로안내를시작합니다")
                            des_name_check = "check"
                            return

                comp_distance = 1000
                for cnt in range(len(map_info)):
                    for floor_room in map_info[cnt]:
                        comp_stt_room = levenshtein(recog_result,floor_room)
    
                        if comp_stt_room < comp_distance:
                            comp_distance = comp_stt_room
                            destination_floor_temp = cnt + 1
                            destination_name_temp = floor_room
                
                start_TTS(str(destination_name_temp)+"을말씀하셨나요")
                start_STT(3)
                return

            if comand_case == 20: ## 원하는층 입력
                map_cnt = -1
                if '일' in recog_result or '1' in recog_result:
                    start_TTS("일층에는")
                    map_cnt = 0
                if '이' in recog_result or '2' in recog_result:
                    start_TTS("이층에는")
                    map_cnt = 1
                if '삼' in recog_result or '3' in recog_result:
                    start_TTS("삼층에는")
                    map_cnt = 2
                if '사' in recog_result or '4' in recog_result:
                    start_TTS("사층에는")
                    map_cnt = 3
                if '오' in recog_result or '5' in recog_result:
                    start_TTS("오층에는")
                    map_cnt = 4
                if '육' in recog_result or '6' in recog_result:
                    start_TTS("육층에는")
                    map_cnt = 5
                if '칠' in recog_result or '7' in recog_result:
                    start_TTS("칠층에는")
                    map_cnt = 6
                
                if map_cnt != -1:
                    for floor_room in map_info[map_cnt]:
                            start_TTS(str(floor_room))
                    start_TTS("이있습니다")
                    return

                start_TTS("음성인식에실패했습니다")
            
            start_TTS("음성인식에실패했습니다")
            return

def start_TTS(text):
    print(text)
    tts_th = threading.Thread(target=tts, args=(text,))
    tts_th.daemon=True
    tts_th.start()

tts_running = 0
def tts(string):
    global tts_running
    while True:
        time.sleep(0.1)
        if tts_running == 0:
            break

    print("=========================================TTS START=========================================")
    tts_running = 1
    print(string)
    os.system("espeak -s 160 -p 95 -v ko+f3 "+string)
    print("=========================================TTS END=========================================")
    tts_running = 0

def start_STT(comand_case):
    print(comand_case)
    time.sleep(0.5)
    stt_th = threading.Thread(target=stt, args=(comand_case,))
    stt_th.daemon=True
    stt_th.start()

def stt(comand_case):
    while True:
        time.sleep(0.1)
        if tts_running == 0:
            break

    with MicrophoneStream(RATE, CHUNK) as stream:
        print("=========================================STT START=========================================")
        audio_generator = stream.generator()
        requests = (types.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)
        responses = client.streaming_recognize(streaming_config, requests)

        STT_result(responses,comand_case)

def clicked():
     while True:
        if not gp.input(switch_L_pin) or not gp.input(switch_R_pin):
            print("pushed")
            time.sleep(0.5)
            start_TTS("말씀하세요")
            start_STT(1)
        
def SHOWCURRENTPOS(current_map, current_pos):
        (cx,cy,cdeg) = current_pos
        arrow = cv.imread('tri.png',cv.IMREAD_COLOR)
        roi = current_map[round(cy-CELL_DISTANCE/2):round(cy+CELL_DISTANCE/2),round(cx-CELL_DISTANCE/2):round(cx+CELL_DISTANCE/2)]
        roi_h,roi_w,_ = roi.shape
        arrow = cv.resize(arrow, (roi_w, roi_h))
        h,w,_ = arrow.shape
        mat = cv.getRotationMatrix2D((w / 2, h / 2), cdeg, 1)
        arrow = cv.warpAffine(arrow, mat, (w, h))

        arrow_gray = cv.cvtColor(arrow, cv.COLOR_BGR2GRAY)
        _, mask = cv.threshold(arrow_gray, 10, 255, cv.THRESH_BINARY)
        mask_i = cv.bitwise_not(mask)

        map_bg = cv.bitwise_and(roi, roi, mask = mask_i)
        arrow_fg = cv.bitwise_and(arrow, arrow, mask=mask)

        dst = cv.add(map_bg, arrow_fg)
        current_map[round(cy-CELL_DISTANCE/2):round(cy+CELL_DISTANCE/2),round(cx-CELL_DISTANCE/2):round(cx+CELL_DISTANCE/2)] = dst

        width_left = cx-399
        width_right = cx+399

        height_up = cy-214
        height_down = cy+214

        if cx <= 399:
            width_left = 0
            width_right = 798

        if WIDTH - cx <= 399:
            width_left = WIDTH - 798
            width_right = WIDTH
            
        if cy <= 214:
            height_up = 0
            height_down = 428

        if HEIGHT - cy <= 214:
            height_up = HEIGHT - 428
            height_down = HEIGHT

        current_map_dp = current_map[height_up:height_down,width_left:width_right]
        return current_map_dp     

def main():
    global current_floor, destination_floor, research, X_OFFSET, y_OFFSET, x, y, deg,destination_name,research,pose_check,el_cnt,current_floor_pub,path_len,elev_cnt,\
        elev_print,elev_pub,pxs, pys, pxe, pye,csx_st,csy_st,csx_ed,csy_ed,walker_num_diff,HEIGHT, WIDTH,CELL_DISTANCE,BLACK_STAND,ELEVATOR_B_BOUNDARY,TOILET_BOUNDARY,DESTINATION,\
        vibe_L_duty_mem, vibe_R_duty_mem, vive_L, vive_R

    def heuristic(a, b):
        return (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2

    def astar(array, start, goal):
        neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        close_set = set()
        came_from = {}
        gscore = {start: 0}
        fscore = {start: heuristic(start, goal)}
        oheap = []

        heappush(oheap, (fscore[start], start))

        while oheap:

            current = heappop(oheap)[1]

            if current == goal:
                data = []
                while current in came_from:
                    data.append(current)
                    current = came_from[current]
                return data

            close_set.add(current)

            for i, j in neighbors:
                neighbor = current[0] + i, current[1] + j
                tentative_g_score = gscore[current] + heuristic(current, neighbor)
                if 0 <= neighbor[0] < array.shape[0]:
                    if 0 <= neighbor[1] < array.shape[1]:
                        if array[neighbor[0]][neighbor[1]] == 1:
                            continue
                    else:
                        # array bound y walls
                        continue
                else:
                    # array bound x walls
                    continue

                if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
                    continue

                if tentative_g_score < gscore.get(neighbor, 0) or neighbor not in [i[1] for i in oheap]:
                    came_from[neighbor] = current
                    gscore[neighbor] = tentative_g_score
                    fscore[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                    heappush(oheap, (fscore[neighbor], neighbor))

        return False

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

    def DEGCALC(deg):
        direction = None

        if 0<=deg<=22.5 or 337.5<deg<=360: direction = "앞으로"
        elif 22.5<deg<=67.5: direction = "왼쪽앞으로"
        elif 67.5<deg<=112.5: direction = "왼쪽으로"
        elif 112.5<deg<=157.5: direction = "왼쪽뒤로"
        elif 157.5<deg<=202.5: direction = "뒤로"
        elif 202.5<deg<=247.5: direction = "오른쪽뒤로"
        elif 247.5<deg<=292.5: direction = "오른쪽으로"
        elif 292.5<deg<=337.5: direction = "오른쪽앞으로"

        return direction

    def DEGCALCVIBE(deg_v):
        global vibe_L_duty_mem, vibe_R_duty_mem, vive_L, vive_R

        vibe_L.start(100)
        vibe_R.start(100)
      
        if deg_v == 0 or deg_v == 360:
            vibe_L.ChangeDutyCycle(0)
            vibe_L_duty_mem = 0
            vibe_R.ChangeDutyCycle(0)
            vibe_R_duty_mem = 0
            return

        if deg_v <= 180:
            vibe_R.ChangeDutyCycle(0)
            vibe_R_duty_mem = 0
            if int(deg_v/10) <= 9:
                vibe_L.ChangeDutyCycle((int(deg_v/10)+1)*10)
                vibe_L_duty_mem = (int(deg_v/10)+1)*10
            else:
                vibe_L.ChangeDutyCycle(100)
                vibe_L_duty_mem = 100
        
        else:
            vibe_L.ChangeDutyCycle(0)
            vibe_L_duty_mem = 0
            if int(deg_v/10) >= 27:
                vibe_R.ChangeDutyCycle((36 - int(deg_v/10))*10)
                vibe_R_duty_mem = (36 - int(deg_v/10))*10
            else:
                vibe_R.ChangeDutyCycle(100)
                vibe_R_duty_mem = 100

    def MAKESECTION(nav_map,cell,map_num):
        section_h = []
        section_w = []
        section_X = []
        he, wi, _ = nav_map.shape
        nav_map = cv.cvtColor(nav_map, cv.COLOR_RGB2HSV)

        if map_num == 1 or map_num == None:
            for cnt in range(int(he/cell)+2):
                h = cnt*cell
                if h > he: h = he
                section_h.append(h)
                if section_h.count(he) > 1:
                    section_h.remove(he)

            for cnt in range(int(wi/cell)+2):
                w = cnt * cell
                if w > wi: w = wi
                section_w.append(w)
                if section_w.count(wi) > 1:
                    section_w.remove(wi)

        if map_num is not None:
            he_st, wi_st, he_ed, wi_ed = 0, 0, 0, 0
            for black1 in range(int(he / cell) + 1):
                he_ed = (black1 + 1) * cell
                if he_ed > he: he_ed = he
                if he_ed != he_st:
                    for black2 in range(int(wi / cell) + 1):
                        wi_ed = (black2 + 1) * cell
                        if wi_ed > wi: wi_ed = wi
                        if wi_ed != wi_st:
                            recog_black = nav_map[he_st:he_ed, wi_st:wi_ed]
                            _, _, v = cv.split(recog_black)
                            if v[int((he_ed-he_st)/2)][int((wi_ed-wi_st)/2)] < BLACK_STAND:
                                section_X.append([wi_st, he_st, wi_ed, he_ed])
                        wi_st = wi_ed
                    he_st = he_ed
                    wi_st, wi_ed = 0, 0
        return (section_h, section_w, section_X)

    def FINDSECTION(section_h, section_w, section_X, x, y, deg, cell):
        current_section_x = 0
        current_section_y = 0
        warning_default = 5
        warn = []

        for section in section_w:
            if x - section <= cell:
                current_section_x = section
                break

        for section in section_h:
            if y - section <= cell:
                current_section_y = section
                break

        for section in section_X:
            [wi_st, he_st, wi_ed, he_ed] = section

            if (abs(x - wi_st)<warning_default)or(abs(x - wi_ed)<warning_default)or(abs(y - he_st)<warning_default) or (abs(y - he_ed)<warning_default) :
                if wi_st>=(current_section_x-cell) and wi_ed<=(current_section_x+(cell*2)) and  he_st>=(current_section_y-cell) and he_ed<=(current_section_y+(cell*2)):
                    section_x_center = (wi_st + cell / 2, he_st + cell / 2)

                    y1 = y - (he_st + cell / 2)
                    x1 = (wi_st + cell / 2) - x

                    deg1 = math.degrees(math.atan2(y1, x1)) - 90
                    if deg1 < 0: deg1 = deg1 + 360

                    if deg1 >= deg:
                        deg2 = deg1 - deg
                    else:
                        deg2 = 360 - (deg - deg1)

                    wall_deg = DEGCALC(deg2)
                    warn.append(wall_deg)

        if len(warn) >= 2:warn = list(set(warn))
        return (current_section_x,current_section_y,current_section_x+cell,current_section_y+cell,warn)

    def MAKEMAZE(section_x_list, section_h,section_w,cell):
        map_bi = []
        endset = [section_w[-2],section_h[-2],section_w[-1],section_h[-1]]
        comp_set = [0,0,0,0]
        for cnt0 in range(len(section_x_list)):
            section_x = section_x_list[cnt0]
            map_bi.append([])
            cnt = 0
            for cnt1 in range(len(section_h)):

                if cnt1 == len(section_h)-1: break
                map_bi[cnt0].append([])
                for cnt2 in range(len(section_w)):

                    if cnt2 == len(section_w)-1: break
                    comp_set = [section_w[cnt2],section_h[cnt1],section_w[cnt2+1],section_h[cnt1+1]]

                    if section_x[cnt] == comp_set:
                        map_bi[cnt0][cnt1].append(1)
                        cnt = cnt+1
                    else :
                        map_bi[cnt0][cnt1].append(0)

        return map_bi

    def FINDSECTIONBINARY(section_h, section_w, section):
        if len(section) == 5:
            (x_section, y_section, _, _, _) = section
        if len(section) == 4:
            (x_section,y_section,_,_) = section
        (h_bin,w_bin) = (0,0)
        for cnt1 in range(len(section_w)):
            if cnt1 == len(section_w) - 1:break
            if x_section == section_w[cnt1]:
                w_bin = cnt1
                break

        for cnt2 in range(len(section_h)):
            if cnt2 == len(section_h) - 1:break
            if y_section == section_h[cnt2]:
                h_bin = cnt2
                break

        return (h_bin,w_bin)

    def MAKEMAP(map,cell,cnt_m):
        he, wi, _ = map.shape
        nav_map = map.copy()

        he_st, wi_st, he_ed, wi_ed = 0, 0, 0, 0
        for black1 in range(int(he/cell)+1):
            he_ed = (black1+1)*cell
            if he_ed > he: he_ed = he
            if he_ed != he_st:
                for black2 in range(int(wi/cell)+1):
                    wi_ed = (black2+1)*cell
                    if wi_ed > wi: wi_ed = wi
                    if wi_ed != wi_st:
                        recog_black = nav_map[he_st:he_ed,wi_st:wi_ed]
                        if image_value_average(recog_black) < 205.0:
                            cv.rectangle(nav_map,(wi_st,he_st),(wi_ed,he_ed),(0,0,0),-1)
                    wi_st = wi_ed
                he_st = he_ed
                wi_st, wi_ed = 0, 0

        for cnt in range(int(wi / cell) + 1):
            wi_line = (cnt+1)*cell
            cv.line(nav_map,(wi_line,0),(wi_line,he),(255,0,0),1)

        for cnt in range(int(he / cell) + 1):
            he_line = (cnt + 1) * cell
            cv.line(nav_map, (0, he_line), (wi, he_line), (255, 0, 0), 1)

        (ox_st, oy_st, ox_ed, oy_ed, _) = ELEVATOR_B_BOUNDARY[1]
        (ex_st, ey_st, ex_ed, ey_ed, _) = ELEVATOR_B_BOUNDARY[0]
        cv.rectangle(nav_map, (ox_st, oy_st), (ox_ed, oy_ed), (255, 255, 100), -1)
        cv.rectangle(nav_map, (ex_st, ey_st), (ex_ed, ey_ed), (255, 255, 100), -1)
        cv.putText(nav_map, 'OB', (ox_st-2, oy_st + 7), cv.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        cv.putText(nav_map, 'EB', (ex_st-2, ey_st + 7), cv.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        (ox_st, oy_st, ox_ed, oy_ed, _) = ELEVATOR_B_BOUNDARY[3]
        (ex_st, ey_st, ex_ed, ey_ed, _) = ELEVATOR_B_BOUNDARY[2]
        cv.rectangle(nav_map, (ox_st, oy_st), (ox_ed, oy_ed), (255, 255, 100), -1)
        cv.rectangle(nav_map, (ex_st, ey_st), (ex_ed, ey_ed), (255, 255, 100), -1)
        cv.putText(nav_map, 'OB', (ox_st-2, oy_st + 7), cv.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        cv.putText(nav_map, 'EB', (ex_st-2, ey_st + 7), cv.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)

        (ox_st, oy_st, ox_ed, oy_ed, _) = TOILET_BOUNDARY[0]
        (ex_st, ey_st, ex_ed, ey_ed, _) = TOILET_BOUNDARY[1]
        cv.rectangle(nav_map, (ox_st, oy_st), (ox_ed, oy_ed), (255, 100, 100), -1)
        cv.rectangle(nav_map, (ex_st, ey_st), (ex_ed, ey_ed), (100, 100, 255), -1)
        cv.putText(nav_map, 'TM', (ox_st-2, oy_st + 7), cv.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        cv.putText(nav_map, 'TR', (ex_st-2, ey_st + 7), cv.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        (ox_st, oy_st, ox_ed, oy_ed, _) = TOILET_BOUNDARY[2]
        (ex_st, ey_st, ex_ed, ey_ed, _) = TOILET_BOUNDARY[3]
        cv.rectangle(nav_map, (ox_st, oy_st), (ox_ed, oy_ed), (255, 100, 100), -1)
        cv.rectangle(nav_map, (ex_st, ey_st), (ex_ed, ey_ed), (100, 100, 255), -1)
        cv.putText(nav_map, 'TM', (ox_st-2, oy_st + 7), cv.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        cv.putText(nav_map, 'TR', (ex_st-2, ey_st + 7), cv.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)

        if len(DESTINATION) != 0:
            for des in DESTINATION:
                if des[0] == str(cnt_m)+'F':
                    (dx_st,dy_st,dx_ed,dy_ed,_) = des[2]
                    cv.rectangle(nav_map, (dx_st, dy_st), (dx_ed, dy_ed), (0, 255, 0), -1)
                    cv.putText(nav_map, 'D',(dx_st,dy_st+7), cv.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
        return nav_map

    def MAKEPATHBINARY(map_bi, start, goal, section_h, section_w):
        (h_st,w_st) = FINDSECTIONBINARY(section_h,section_w,start)
        (h_gl,w_gl) = FINDSECTIONBINARY(section_h,section_w,goal)
        start_bin = (h_st,w_st)
        print(start_bin)
        goal_bin = (h_gl,w_gl)
        print(goal_bin)
        input_maze = map_bi

        input_maze[h_st][w_st] = 0
        input_maze[h_gl][w_gl] = 0

        path = astar(input_maze,start_bin,goal_bin)

        return path

    def BINTOSECPATH(map_list,map_bi_list,current_floor,destination_floor,st_bound,goal_name, section_h, section_w):
        (patha, pathb) = (None, None)
        (path_sec1,path_sec2) = ([],[])
        (goal_bound1,goal_bound2) = (None,None)
        (gx_st, gy_st, gx_ed, gy_ed, gd1, gd2) = (None, None, None, None, None, None)
        if current_floor == destination_floor:
            mapo = map_list[current_floor-1]
            map_c = mapo.copy()
            map_bi = np.array(map_bi_list[current_floor-1])

            if goal_name == 'toilet_m':
                if x > WIDTH/2:
                    (gx_st, gy_st, gx_ed, gy_ed, gd1) = TOILET_BOUNDARY[0]
                else :
                    (gx_st, gy_st, gx_ed, gy_ed, gd1) = TOILET_BOUNDARY[2]

            elif goal_name == 'toilet_r':
                if x > WIDTH/2:
                    (gx_st, gy_st, gx_ed, gy_ed, gd1) = TOILET_BOUNDARY[1]
                else :
                    (gx_st, gy_st, gx_ed, gy_ed, gd1) = TOILET_BOUNDARY[3]

            else :
                for des in DESTINATION:
                    if des[0] == str(current_floor) + 'F':
                        if des[1] == goal_name:
                            (gx_st, gy_st, gx_ed, gy_ed, gd1) = des[2]
                            break

            if gd1 == 0 or gd1 == 360:
                goal_bound1 = (gx_st, gy_st+CELL_DISTANCE, gx_ed, gy_ed+CELL_DISTANCE, gd1)
            elif gd1 == 90:
                goal_bound1 = (gx_st+CELL_DISTANCE, gy_st, gx_ed+CELL_DISTANCE, gy_ed, gd1)
            elif gd1 == 180:
                goal_bound1 = (gx_st, gy_st-CELL_DISTANCE, gx_ed, gy_ed-CELL_DISTANCE, gd1)
            elif gd1 == 270:
                goal_bound1 = (gx_st-CELL_DISTANCE, gy_st, gx_ed-CELL_DISTANCE, gy_ed, gd1)

            if goal_bound1 is not None:
                patha = MAKEPATHBINARY(map_bi,st_bound,goal_bound1,section_h,section_w)
                if(patha == False):
                    return (None,None,None,None,None,None)
                print(patha)
                for path_bi in patha:
                    (h,w) = path_bi
                    (x_st,y_st,x_ed,y_ed) = (section_w[w],section_h[h],section_w[w]+CELL_DISTANCE,section_h[h]+CELL_DISTANCE)
                    path_sec1.append([x_st,y_st,x_ed,y_ed])

            if len(path_sec1) != 0:
                for path_sec1_s in path_sec1:
                    (x_st,y_st,x_ed,y_ed) = path_sec1_s
                    cv.rectangle(map_sec1,(x_st,y_st),(x_ed,y_ed),(0,255,0),-1)
            path_sec1 = list(reversed(path_sec1))
            print("path1: ",path_sec1)
            return (path_sec1,None,map_c,None,gd1,None)

        else:
            map1o = map_list[current_floor - 1]
            map2o = map_list[destination_floor - 1]
            map_bi1 = np.array(map_bi_list[current_floor - 1])
            map_bi2 = np.array(map_bi_list[destination_floor - 1])

            map1 = map1o.copy()
            map2 = map2o.copy()

            if destination_floor%2 == 0:
                if x > WIDTH / 2:
                    (_, _, _, _, gd1) = ELEVATOR_B_BOUNDARY[0]
                    goal_bound1 = ELEVATOR_B_BOUNDARY[0]

                else:
                    (_, _, _, _, gd1) = ELEVATOR_B_BOUNDARY[2]
                    goal_bound1 = ELEVATOR_B_BOUNDARY[2]

            else :
                if x > WIDTH / 2:
                    (_, _, _, _, gd1) = ELEVATOR_B_BOUNDARY[1]
                    goal_bound1 = ELEVATOR_B_BOUNDARY[1]

                else:
                    (_, _, _, _, gd1) = ELEVATOR_B_BOUNDARY[3]
                    goal_bound1 = ELEVATOR_B_BOUNDARY[3]

                if goal_name == "RETURN":
                    (_, _, _, _, gd1) = ELEVATOR_B_BOUNDARY[1]
                    goal_bound1 = ELEVATOR_B_BOUNDARY[1]

            for des2 in DESTINATION:
                if des2[0] == str(destination_floor) + 'F':
                    if des2[1] == goal_name:
                        (gx_st, gy_st, gx_ed, gy_ed, gd2) = des2[2]
                        if gd2 == 0 or gd2 == 360:
                            goal_bound2 = (gx_st, gy_st + CELL_DISTANCE, gx_ed,gy_ed + CELL_DISTANCE, gd2)
                            break
                        elif gd2 == 90:
                            goal_bound2 = (gx_st + CELL_DISTANCE, gy_st, gx_ed + CELL_DISTANCE,gy_ed, gd2)
                            break
                        elif gd2 == 180:
                            goal_bound2 = (gx_st, gy_st - CELL_DISTANCE, gx_ed,gy_ed - CELL_DISTANCE, gd2)
                            break
                        elif gd2 == 270:
                            goal_bound2 = (gx_st - CELL_DISTANCE, gy_st, gx_ed - CELL_DISTANCE,gy_ed, gd2)
                            break


            if goal_bound1 is not None:
                patha = MAKEPATHBINARY(map_bi1, st_bound, goal_bound1, section_h, section_w)
                if (patha == False):
                    return (None, None, None, None, None, None)
                for path_bi in patha:
                    (h, w) = path_bi
                    (x_st, y_st, x_ed, y_ed) = (
                    section_w[w], section_h[h], section_w[w] + CELL_DISTANCE, section_h[h] + CELL_DISTANCE)
                    path_sec1.append([x_st, y_st, x_ed, y_ed])

            if goal_bound2 is not None:
                pathb = MAKEPATHBINARY(map_bi2, goal_bound1, goal_bound2, section_h, section_w)
                if (pathb == False):
                    return (None, None, None, None, None, None)
                for path_bi in pathb:
                    (h, w) = path_bi
                    (x_st, y_st, x_ed, y_ed) = (
                    section_w[w], section_h[h], section_w[w] + CELL_DISTANCE, section_h[h] + CELL_DISTANCE)
                    path_sec2.append([x_st, y_st, x_ed, y_ed])

            if len(path_sec1) != 0:
                for path_sec1_s in path_sec1:
                    (x_st, y_st, x_ed, y_ed) = path_sec1_s
                    cv.rectangle(map1, (x_st, y_st), (x_ed, y_ed), (0, 255, 0), -1)

            if len(path_sec2) != 0:
                for path_sec2_s in path_sec2:
                    (x_st, y_st, x_ed, y_ed) = path_sec2_s
                    cv.rectangle(map2, (x_st, y_st), (x_ed, y_ed), (0, 255, 0), -1)

            path_sec1 = list(reversed(path_sec1))
            path_sec2 = list(reversed(path_sec2))
            print("path1: ", path_sec1)
            print("path2: ", path_sec2)
            return (path_sec1, path_sec2, map1, map2,gd1,gd2)

    def NAVIGATION(map_list, section_x_list, section_h, section_w, current_floor_path, destination_floor_path,
                    cell,current_floor,destination_floor,nav_map_ch,des_deg1,des_deg2):
        global pxs, pys, pxe, pye,elev_print,elev_cnt,current_floor_pub,csx_st, csy_st, csx_ed, csy_ed,elev_pub, vibe_L_duty_mem, vibe_R_duty_mem
        el_cnt = 0
        start_map = map_list[0]
        goal_map = map_list[1]

        start_map_o = DP_MAP[current_floor -1]
        goal_map_o = DP_MAP[destination_floor -1]
        if current_floor_path is not None:
            start_map_dp = start_map_o.copy()
            for grid_1 in current_floor_path:
                (gx_st,gy_st,gx_ed,gy_ed) = grid_1
                cv.rectangle(start_map_dp,(gx_st,gy_st),(gx_ed,gy_ed),(0,255,0),-1)

        if destination_floor_path is not None:
            goal_map_dp = goal_map_o
            for grid_2 in destination_floor_path:
                (gx_st,gy_st,gx_ed,gy_ed) = grid_2
                cv.rectangle(goal_map_dp,(gx_st,gy_st),(gx_ed,gy_ed),(0,255,0),-1)
        
        section_x_start = section_x_list[int(current_floor)-1]
        section_x_goal = section_x_list[int(destination_floor)-1]
        next_path = 0
        deg_temp = None
        des_deg_temp = None
        warn_temp = []

        if destination_floor_path is None:
            client_mq.subscribe('POSITION', 1)
            x_input = x
            y_input = y
            deg_input = deg

            map_current_floor = start_map_dp.copy()
            map_dp_show = SHOWCURRENTPOS(map_current_floor,(x_input, y_input, deg_input))
            # map_dp_show = cv.flip(map_dp_show, -1)
            cv.imshow("map_show",map_dp_show)
            if cv.waitKey(25) & 0xFF == ord('q'):
                cv.destroyAllWindows()

            print('1 floor nav')
            time.sleep(2)
            if (x_input, y_input, deg_input) != (0, 0, 0): pose_check = 1

            if pose_check == 1:

                (csx_st,csy_st,csx_ed,csy_ed,cwarn) = FINDSECTION(section_h, section_w,section_x_start,x_input,y_input,deg_input,cell)

                while True:
                    client_mq.subscribe('POSITION', 1)
                    x_input = x
                    y_input = y
                    deg_input = deg
                    map_current_floor = start_map_dp.copy()
                    map_dp_show = SHOWCURRENTPOS(map_current_floor,(x_input, y_input, deg_input))
                    # map_dp_show = cv.flip(map_dp_show, -1)
                    cv.imshow("map_show",map_dp_show)
                    if cv.waitKey(25) & 0xFF == ord('q'):
                        cv.destroyAllWindows()
                    (csx_st, csy_st, csx_ed, csy_ed, cwarn) = FINDSECTION(section_h, section_w, section_x_start, x_input, y_input, deg_input,cell)

                    if [csx_st, csy_st, csx_ed, csy_ed] == [pxs, pys, pxe, pye]: next_path = next_path + 1
                    if [csx_st, csy_st, csx_ed, csy_ed] == current_floor_path[-1]:
                        deg1 = des_deg1
                        if deg1 >= deg_input:
                            deg2 = deg1 - deg_input
                        else:
                            deg2 = 360 - (deg_input - deg1)
                        next_path_deg = DEGCALC(deg2)
                        DEGCALCVIBE(deg2)
                        start_TTS(str(next_path_deg)+"가세요")

                        return ("Done", current_floor_path[-1], 1)

                    next_path_section = current_floor_path[next_path]
                    (pxs, pys, pxe, pye) = next_path_section
                    if current_floor == 2:
                        if ((csx_st, csy_st, csx_ed, csy_ed) == (1780,2160,1790,2170)) or((csx_st, csy_st, csx_ed, csy_ed) == (2750,2160,2760,2170))or((csx_st, csy_st, csx_ed, csy_ed) == (1760,2160,1770,2170)) or((csx_st, csy_st, csx_ed, csy_ed) == (2730,2160,2740,2170)):
                            cwarn.append("2FDOOR")

                    if ((csx_st - cell) <= pxs <= (csx_ed + cell)) and ((csy_st - cell) <=pye<= (csy_ed + cell)): nav_type = 1
                    else: nav_type = 2

                    if (warn_temp != cwarn) and (cwarn != []):
                        print('wall is close: ',cwarn)
                        speak_warn_direction = [0,0,0,0,0]
                        for speak_warn in cwarn:
                            if '위'in speak_warn : speak_warn_direction[0] = 1
                            if '왼'in speak_warn : speak_warn_direction[1] = 1
                            if '아래'in speak_warn : speak_warn_direction[2] = 1
                            if '오른'in speak_warn : speak_warn_direction[3] = 1
                            if '2FDOOR'in speak_warn : speak_warn_direction[4] = 1

                        if speak_warn_direction[0] == 1: start_TTS('앞에')
                        if speak_warn_direction[1] == 1: start_TTS('왼쪽에')
                        if speak_warn_direction[2] == 1: start_TTS('뒤에')
                        if speak_warn_direction[3] == 1: start_TTS('오른쪽에')
                        start_TTS("벽이있습니다조심하세요")

                        if speak_warn_direction[4] == 1: start_TTS('앞에문이있습니다조심하세요')
                    warn_temp = cwarn

                    if nav_type == 1:
                        y1 = y_input - (pys+cell/2)
                        x1 = (pxs+cell/2) - x_input

                        deg1 = math.degrees(math.atan2(y1,x1))-90
                        if deg1 < 0: deg1 = deg1 + 360

                        if deg1 >= deg_input: deg2 = deg1 - deg_input
                        else: deg2 = 360 - (deg_input - deg1)

                        next_path_deg = DEGCALC(deg2)
                        DEGCALCVIBE(deg2)
                        if next_path_deg != deg_temp:
                            print('next path: ',next_path_deg)
                            start_TTS(str(next_path_deg)+"가세요")
                        deg_temp = next_path_deg
                        des_section_center = (0,0)

                    if nav_type == 2:
                        print("Path_reset")
                        
                        return ("Path_reset", [csx_st, csy_st, csx_ed, csy_ed],1)

                    if research == "Research":
                        print("Research")
                        return ("Research", [csx_st, csy_st, csx_ed, csy_ed],1)


        else:
            print('2 floor nav')
            nav_two_floor = None
            nav_check = nav_map_ch
            client_mq.subscribe('POSITION', 1)

            x_input = x
            y_input = y
            deg_input = deg

            map_current_floor = start_map_dp.copy()
            map_dp_show = SHOWCURRENTPOS(map_current_floor,(x_input, y_input, deg_input))
            # map_dp_show = cv.flip(map_dp_show, -1)
            cv.imshow("map_show",map_dp_show)
            if cv.waitKey(25) & 0xFF == ord('q'):
                cv.destroyAllWindows()
            
            if (x_input, y_input, deg_input) != (0, 0, 0): pose_check = 1
            time.sleep(2)
            path_len = len(current_floor_path)
            while pose_check == 1:
                client_mq.subscribe('POSITION', 1)
                client_mq.subscribe('ELEVATOR1',1)
                x_input = x
                y_input = y
                deg_input = deg

                if len(current_floor_path) == 0:
                    nav_check = 2
                    path_len = len(destination_floor_path)
                    (csx_st, csy_st, csx_ed, csy_ed, cwarn) = FINDSECTION(section_h, section_w, section_x_start, x_input, y_input, deg_input,cell)

                if nav_check == 1:
                    map_current_floor = start_map_dp.copy()
                    map_dp_show = SHOWCURRENTPOS(map_current_floor,(x_input, y_input, deg_input))
                    # map_dp_show = cv.flip(map_dp_show, -1)
                    cv.imshow("map_show",map_dp_show)
                    if cv.waitKey(25) & 0xFF == ord('q'):
                        cv.destroyAllWindows()
                        
                    (csx_st, csy_st, csx_ed, csy_ed, cwarn) = FINDSECTION(section_h, section_w, section_x_start, x_input, y_input, deg_input,cell)
                    if current_floor == 2:
                        if ((csx_st, csy_st, csx_ed, csy_ed) == (1780,2160,1790,2170)) or((csx_st, csy_st, csx_ed, csy_ed) == (2750,2160,2760,2170))or((csx_st, csy_st, csx_ed, csy_ed) == (1760,2160,1770,2170)) or((csx_st, csy_st, csx_ed, csy_ed) == (2730,2160,2740,2170)):
                            cwarn.append("2FDOOR")
                    if (warn_temp != cwarn) and (cwarn != []):
                        print('wall is close: ',cwarn)
                        speak_warn_direction = [0,0,0,0,0]
                        for speak_warn in cwarn:
                            if '위'in speak_warn : speak_warn_direction[0] = 1
                            if '왼'in speak_warn : speak_warn_direction[1] = 1
                            if '아래'in speak_warn : speak_warn_direction[2] = 1
                            if '오른'in speak_warn : speak_warn_direction[3] = 1
                            if '2FDOOR'in speak_warn : speak_warn_direction[4] = 1

                        if speak_warn_direction[0] == 1: start_TTS('앞에')
                        if speak_warn_direction[1] == 1: start_TTS('왼쪽에')
                        if speak_warn_direction[2] == 1: start_TTS('뒤에')
                        if speak_warn_direction[3] == 1: start_TTS('오른쪽에')
                        start_TTS("벽이있습니다조심하세요")

                        if speak_warn_direction[4] == 1: start_TTS('앞에문이있습니다조심하세요')
                    warn_temp = cwarn

                if nav_check == 2:
                    map_current_floor = start_map_dp.copy()
                    map_dp_show = SHOWCURRENTPOS(map_current_floor,(x_input, y_input, deg_input))
                    # map_dp_show = cv.flip(map_dp_show, -1)
                    cv.imshow("map_show",map_dp_show)
                    if cv.waitKey(25) & 0xFF == ord('q'):
                        cv.destroyAllWindows()

                    if elev_pub == 0:
                        deg1 = 90
                        if deg1 >= deg_input:
                            deg2 = deg1 - deg_input
                        else:
                            deg2 = 360 - (deg_input - deg1)
                        next_path_deg = DEGCALC(deg2)
                        DEGCALCVIBE(deg2)
                        print(next_path_deg)
                        start_TTS("엘리베이터에,도착했습니다 " + str(next_path_deg)+"가세요")
                        client_mq.publish("ELEVATORFIND",'1',1)
                    elev_pub = 1
                    (x1,x2,y1,y2) = destination_floor_path[0]
                    if x_input < x1-CELL_DISTANCE :
                        if elev_pub == 1:
                            elev_pub = 2
                            elev_cnt = 1
                        if elev_print == 0: print("in elevator")
                        elev_print += 1
                    if elev_cnt == 1 and x_input > x1-CELL_DISTANCE:
                        nav_check = 3
                        elev_cnt = 0
                        elev_print = 0
                        elev_pub = 0
                        print("out elevator")

                    time.sleep(0.5)

                if nav_check == 3:
                    map_current_floor = goal_map_dp.copy()
                    map_dp_show = SHOWCURRENTPOS(map_current_floor,(x_input, y_input, deg_input))
                    # map_dp_show = cv.flip(map_dp_show, -1)
                    cv.imshow("map_show",map_dp_show)
                    if cv.waitKey(25) & 0xFF == ord('q'):
                        cv.destroyAllWindows()
                        
                    (csx_st, csy_st, csx_ed, csy_ed, cwarn) = FINDSECTION(section_h, section_w, section_x_goal, x_input, y_input, deg_input,cell)
                    if destination_floor == 2:
                        if ((csx_st, csy_st, csx_ed, csy_ed) == (1780,2160,1790,2170)) or((csx_st, csy_st, csx_ed, csy_ed) == (2750,2160,2760,2170))or((csx_st, csy_st, csx_ed, csy_ed) == (1760,2160,1770,2170)) or((csx_st, csy_st, csx_ed, csy_ed) == (2730,2160,2740,2170)):
                            cwarn.append("2FDOOR")
                    if (warn_temp != cwarn) and (cwarn != []):
                        print('wall is close: ',cwarn)
                        speak_warn_direction = [0,0,0,0,0]
                        for speak_warn in cwarn:
                            if '위'in speak_warn : speak_warn_direction[0] = 1
                            if '왼'in speak_warn : speak_warn_direction[1] = 1
                            if '아래'in speak_warn : speak_warn_direction[2] = 1
                            if '오른'in speak_warn : speak_warn_direction[3] = 1
                            if '2FDOOR'in speak_warn : speak_warn_direction[4] = 1

                        if speak_warn_direction[0] == 1: start_TTS('앞에')
                        if speak_warn_direction[1] == 1: start_TTS('왼쪽에')
                        if speak_warn_direction[2] == 1: start_TTS('뒤에')
                        if speak_warn_direction[3] == 1: start_TTS('오른쪽에')
                        start_TTS("벽이있습니다조심하세요")

                        if speak_warn_direction[4] == 1: start_TTS('앞에문이있습니다조심하세요')
                    warn_temp = cwarn

                if [csx_st, csy_st, csx_ed, csy_ed] == [pxs, pys, pxe, pye]:
                    next_path = next_path + 1
                if next_path >= path_len:
                    nav_check = nav_check + 1
                    next_path = 0
                    elevator_find = 0
                    path_len = len(destination_floor_path)
                    print(next_path)
                    print(len(current_floor_path))
                    print(nav_check)
                if nav_check == 4:
                    current_floor_pub = 0
                    elev_cnt = 0
                    elev_print = 0
                    deg1 = des_deg2
                    if deg1 >= deg_input:
                        deg2 = deg1 - deg_input
                    else:
                        deg2 = 360 - (deg_input - deg1)
                    next_path_deg = DEGCALC(deg2)
                    DEGCALCVIBE(deg2)
                    start_TTS(str(next_path_deg)+"가세요")
                    return ("Done", destination_floor_path[-1], 1)
                if nav_check == 1:next_path_section = current_floor_path[next_path]
                else: next_path_section = destination_floor_path[next_path]
                (pxs, pys, pxe, pye) = next_path_section
                if ((csx_st - cell) <= pxs <= (csx_ed + cell)) and ((csy_st - cell) <= pye <= (csy_ed + cell)): nav_type = 1
                elif(nav_check != 2): nav_type = 2

                if nav_type == 1:
                    y1 = y_input - (pys + cell / 2)
                    x1 = (pxs + cell / 2) - x_input

                    deg1 = math.degrees(math.atan2(y1, x1)) - 90
                    if deg1 < 0: deg1 = deg1 + 360

                    if deg1 >= deg_input:
                        deg2 = deg1 - deg_input
                    else:
                        deg2 = 360 - (deg_input - deg1)

                    next_path_deg = DEGCALC(deg2)
                    DEGCALCVIBE(deg2)
                    if next_path_deg != deg_temp and nav_check != 2:
                        print('next path: ',next_path_deg)
                        start_TTS(str(next_path_deg)+"가세요")
                    deg_temp = next_path_deg

                    des_section_center = (0, 0)


                if nav_type == 2 and nav_check != 2:
                    print("Path_reset")
                    elev_cnt = 0
                    elev_print = 0
                    return ["Path_reset", [csx_st, csy_st, csx_ed, csy_ed],nav_check]

                if research == "Research":
                    print("Research")
                    current_floor_pub = 0
                    elev_cnt = 0
                    elev_print = 0
                    return ["Research", [csx_st, csy_st, csx_ed, csy_ed],1]

        return ("none",[0,0,0,0],1)

    ############################-NEW SET-############################
    # NAV_MAP = []
    # cnt = 1
    # for map in map_list:
    #     NAV_MAP.append(MAKEMAP(map,CELL_DISTANCE,cnt))
    #     print(cnt)
    #     cnt = cnt + 1
    #
    # cnt_map = 1
    # for map_section in NAV_MAP:
    #     cv.imwrite('map'+str(cnt_map)+'_sec.png',map_section)
    #     cnt_map += 1
    #################################################################

    print("Map make complete")
   
    section_h = None
    section_w = None
    section_X_list = []
    with open('map_object_default.json', 'r') as map_json_r:
        map_object = json.load(map_json_r)
        if len(map_object['section_X_list']) != 0:
            (section_h, section_w, _) = MAKESECTION(NAV_MAP[1],CELL_DISTANCE,None)
            section_X_list = map_object['section_X_list'][0]

        else:
            for cnt in range(0,7):
                if cnt == 1:
                    (section_h, section_w, section_X) = MAKESECTION(NAV_MAP[cnt],CELL_DISTANCE,cnt)
                    
                else:
                    (_, _, section_X) = MAKESECTION(NAV_MAP[cnt],CELL_DISTANCE,cnt)

                section_X_list.append(section_X)
                print(cnt)
            
            map_object['section_X_list'].append(section_X_list)

            with open('map_object_default.json', 'w') as map_json_w:
                json.dump(map_object, map_json_w, ensure_ascii=False)

    print("Set object complete")
    NAV_MAP_BINARY = MAKEMAZE(section_X_list,section_h,section_w,CELL_DISTANCE)

    destination_section = None
    path1 = None
    path2 = None
    deg_deg1 = None
    des_deg2 = None
    arrive = 1
    nav_ch = 1
    destination_name = None
    map_with_path_list = None

    st_bound = START_BOUNDARY
    time.sleep(1)

    while True:
        
        client_mq.subscribe('POSITION',1)
        client_mq.subscribe('OBJECT1',1)
        client_mq.subscribe('ELEVATOR1',1)

        x_input = x
        y_input = y
        deg_input = deg

        map_dp = DP_MAP[current_floor-1]
        map_dp_cop = map_dp.copy()

        if x_input != 0 and y_input != 0:
            map_dp_show = SHOWCURRENTPOS(map_dp_cop,(x_input, y_input, deg_input))
            # map_dp_show = cv.flip(map_dp_show, -1)
            cv.imshow("map_show",map_dp_show)

            if cv.waitKey(25) & 0xFF == ord('q'):
                cv.destroyAllWindows()
                break

        print('wait input: ')
        print(current_floor,destination_floor)
        print((x,y,deg))
        (stx,sty,edx,edy,_) = FINDSECTION(section_h, section_w, section_X_list[1],x,y,deg,CELL_DISTANCE)
        st_bound = (stx,sty,edx,edy,deg)
        print(st_bound)
        arrive = 1
        time.sleep(2)
        if current_floor != 0 and destination_floor != 0 and destination_name != None:
            (path1,path2,map_show1,map_show2,deg_deg1,des_deg2) = \
                BINTOSECPATH(NAV_MAP,NAV_MAP_BINARY,current_floor,destination_floor,st_bound,destination_name,section_h,section_w)
            if (path1,path2,map_show1,map_show2,deg_deg1,des_deg2) == (None,None,None,None,None,None):
                destination_name = None
                research = None
                path1 = None
                path2 = None

            map_with_path_list = [map_show1,map_show2]

        if current_floor != 0 and destination_floor != 0 and path1 != None:
            print("Navigation Start")
            print(current_floor,destination_floor)
            print(destination_name)
            while arrive != 0:
                client_mq.subscribe('POSITION', 1)
                (stx, sty, edx, edy, _) = FINDSECTION(section_h, section_w, section_X_list[1], x, y, deg, CELL_DISTANCE)
                st_bound = (stx, sty, edx, edy, deg)
                net = NAVIGATION(map_with_path_list,section_X_list,section_h,section_w,path1,path2,CELL_DISTANCE,
                                    current_floor,destination_floor,nav_ch,deg_deg1,des_deg2)

                if net[0] == 'Path_reset':
                    st_bound = net[1]
                    nav_ch = net[2]
                    if nav_ch == 3: current_floor = destination_floor
                    print(st_bound)
                    (path1, path2, map_show1, map_show2,deg_deg1,des_deg2) \
                        = BINTOSECPATH(NAV_MAP, NAV_MAP_BINARY, current_floor, destination_floor, st_bound, destination_name, section_h, section_w)
                    if (path1, path2, map_show1, map_show2, deg_deg1, des_deg2) == (None, None, None, None, None, None):
                        destination_name = None
                        research = None
                        path1 = None
                        path2 = None
                        break
                    map_with_path_list = [map_show1, map_show2]

                if net[0] == 'Research' or net[0] == 'Done':
                    print("*******************Done*************************")
                    if net[0] == 'Done':
                        start_TTS("목적지에 도착했습니다")
                    arrive = 0
                    current_floor = destination_floor
                    destination_floor = 0
                    if(destination_name == 'RETURN'):
                        print("navigation end")
                        return
                    destination_name = None
                    research = None
                    path1 = None
                    path2 = None
                    st_bound = net[1]
                    print("current: "+str(st_bound))

if __name__ == "__main__":
    try:
        cv.namedWindow("map_show", cv.WND_PROP_FULLSCREEN)
        cv.setWindowProperty("map_show", cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
        speak_start = threading.Thread(target=clicked)
        navigation_start = threading.Thread(target=main)
        speak_start.start()
        navigation_start.start()
    except KeyboardInterrupt:
        vibe_L.start(0)
        vibe_R.start(0)
        vibe_L.stop()
        vibe_R.stop()


       



