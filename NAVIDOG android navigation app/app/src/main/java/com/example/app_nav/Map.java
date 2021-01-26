package com.example.app_nav;

import android.annotation.SuppressLint;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.graphics.PointF;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.view.View;
import android.speech.*;
import android.widget.TextView;
import android.widget.Toast;
import android.os.Build;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import android.hardware.*;

import com.davemorrissey.labs.subscaleview.ImageSource;
import com.davemorrissey.labs.subscaleview.SubsamplingScaleImageView;

import org.eclipse.paho.client.mqttv3.MqttException;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;
import org.opencv.android.Utils;
import org.opencv.core.Mat;
import org.opencv.core.Point;
import org.opencv.core.Scalar;
import org.opencv.imgproc.Imgproc;

import  org.json.simple.*;

import static android.speech.tts.TextToSpeech.ERROR;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Locale;
import java.util.Timer;
import java.util.TimerTask;

public class Map extends AppCompatActivity{

    private static final int REQUEST_CODE_SPEECH_INPUT = 4000;
    Intent stt_i;
    SpeechRecognizer stt;
    TextToSpeech tts;
    TextView textView;
    MAP_PATH_SHOW map_path_show;
    CURRNET_POS_SHOW currnet_pos_show;
    CHECK_TOPIC check_topic;

    public String input_string = "NULL";
    public int stt_case_flag = 0;
//    public int

    public int walker_current_floor = 0;
    public static Timer timer = new Timer();
    private PinView pin;

    public String[] path1_s = new String[] {};
    public String[] path2_s = new String[] {};
    public String[] wall_s = new String[] {};
    public String[] object_position_s = new String[] {};
    public String next_path_s = "";
    public int x_s = 0;
    public int y_s = 0;
    public float x_x = 0.0f;
    public float y_x = 0.0f;
    public int deg_s = 0;
    public int elevator_set_s = 0;
    public int button_stat_s = -1;
    public int current_floor_set_s = 0;
    public int elev_cnt = 0;

    public int current_floor = 0;
    public int goal_floor = 0;

    public int floor_cnt = 7;
    public int find_floor_miss = 100;
    public String destination_name = "NULL";
    public int repeat_cheak = 0;
    public int first_input = 0;
    public int destination_list_check = 0;
    public int Check_command = 0;
    public int stt_ready = 1;

    public int right_check = 0;
    public int center_check = 0;
    public int left_check = 0;

    public JSONArray destination_array;
    public String map_info = "{\"1F\":[\"남자화장실\",\"여자화장실\",\"101\",\"102\",\"103\",\"104\"\"105\",\"106\",\"107\",\"108\",\"110\",\"131\",\"132\",\"133\",\"134\",\"135\",\"136\",\"137\"],\"2F\":[\"남자화장실\",\"여자화장실\",\"201\",\"202\",\"203\",\"204\"\"205\",\"206\",\"207\",\"231A\",\"231B\",\"232\",\"233\",\"234\",\"235\",\"236\",\"237\"],\"3F\":[\"남자화장실\",\"여자화장실\",\"301\",\"302\",\"303\"\"304\"\"305\",\"306\",\"307\",\"308\",\"309\",\"310\",\"331\",\"332\",\"333\",\"334\",\"335\",\"336\",\"337\",\"339\"\"340\",\"341\",\"342\",\"343\",\"344\",\"345\"],\"4F\":[\"남자화장실\",\"여자화장실\",\"401\",\"402\"\"403\",\"404\",\"405\",\"406\",\"407\",\"408\",\"409\",\"410\",\"411\",\"431\",\"432\",\"433\",\"434\",\"435\",\"436\",\"437\",\"439\",\"440\",\"441\",\"442\",\"443\",\"445\",\"446\"],\"5F\":[\"남자화장실\",\"여자화장실\",\"501\",\"502\",\"503\",\"504\",\"505\",\"506\",\"507\",\"508\",\"509\",\"510\",\"511\",\"512\",\"513\",\"514\",\"515\",\"516\",\"517\",\"518\",\"519\",\"520\",\"531\",\"532A\",\"532B\",\"533\",\"534\",\"535\",\"536\",\"537\",\"539\",\"540\",\"541\",\"542\",\"543\",\"544\",\"545\"],\"6F\":[\"남자화장실\",\"여자화장실\",\"601\",\"602\",\"603\",\"604\",\"605\",\"606\",\"607\",\"608\",\"609\",\"610\",\"611\",\"612\",\"613\",\"614\",\"615\",\"616\",\"617\",\"618\",\"619\",\"631\",\"632\",\"633\",\"634\",\"635\",\"636\",\"637\",\"639\",\"640\"\"641\",\"642\",\"643\",\"644\"],\"7F\":[\"남자화장실\",\"여자화장실\",\"반납\",\"701\",\"702\",\"703\",\"704\",\"705\",\"706\",\"707\",\"708\",\"709\",\"710\",\"711\",\"712\",\"713\",\"714\",\"715\",\"716\",\"717\",\"718\",\"719\",\"719-1\",\"720\",\"721\"]}";
    public String destination_info = "{\"남자화장실\":[\"화장실\"],\"여자화장실\":[\"화장실\"],\"101\":[\"정밀분석소\"],\"102\":[\"3차원정밀측정실\"],\"103\":[\"3차원역설계실\"],\"104\":[\"3차원측정지원실\"],\"105\":[\"공용장비교육장\"],\"106\":[\"공용장비지원센터행정실\"],\"107\":[\"정밀분석지원실\"],\"108\":[\"북카페\"],\"110\":[\"세미나실\"],\"131\":[\"연구실\"],\"132\":[\"주카페\"],\"133\":[\"연구실\"],\"134\":[\"푸드코트\"],\"135\":[\"연구실\"],\"136\":[\"연구실\"],\"137\":[\"연구실\"],\"201\":[\"휴게실\"],\"202\":[\"강의실\"],\"203\":[\"강의실\"],\"204\":[\"강의실\"],\"205\":[\"강의실\"],\"206\":[\"강의실\"],\"207\":[\"산학융합캠퍼스사업단\"],\"231A\":[\"중회의실\"],\"231B\":[\"강의실\"],\"232\":[\"에스제이테크\"],\"233\":[\"연구실\"],\"234\":[\"에스제이테크\"],\"235\":[\"경기산학융합본부\"],\"236\":[\"에스제이테크\"],\"237\":[\"연구실\"],\"301\":[\"휴게실\"],\"302\":[\"강의실\"],\"303\":[\"강의실\"],\"304\":[\"강의실\"],\"305\":[\"강의실\"],\"306\":[\"강의실\"],\"307\":[\"강의실\"],\"308\":[\"강의실\"],\"309\":[\"세미나실\"],\"310\":[\"강의실\"],\"331\":[\"에이피텍\"],\"332\":[\"한국수출입은행\"],\"333\":[\"경기산학융합본부\"],\"334\":[\"메디싱크\"],\"335\":[\"리비전\"],\"336\":[\"메디싱크\"],\"337\":[\"지에스티\"],\"339\":[\"정한인프라\"],\"340\":[\"로보모터스\"],\"341\":[\"정한인프라\"],\"342\":[\"연구실\"],\"343\":[\"유씨드\"],\"344\":[\"메디싱크\"],\"345\":[\"나인원전자\"],\"401\":[\"산학협력정책연구소\"],\"402\":[\"공용컴퓨터실\"],\"403\":[\"SOC응용설계실\"],\"404\":[\"강의실\"],\"405\":[\"강의실\"],\"406\":[\"강의실\"],\"407\":[\"강의실\"],\"408\":[\"강사대기실\"],\"409\":[\"강의실\"],\"410\":[\"기업인재대학교학팀\"],\"411\":[\"강의실\"],\"431\":[\"스타폴리머\"],\"432\":[\"연구실\"],\"433\":[\"스타폴리머\"],\"434\":[\"아인텍\"],\"435\":[\"카로그\"],\"436\":[\"유현산업\"],\"437\":[\"연구실\"],\"439\":[\"연구실\"],\"440\":[\"그린리소스\"],\"441\":[\"루미스탈\"],\"442\":[\"연구실\"],\"443\":[\"환경과사람들\"],\"445\":[\"디아이티\"],\"446\":[\"유현산업\"],\"501\":[\"휴게실\"],\"502\":[\"전자파실\"],\"503\":[\"교수연구실\"],\"504\":[\"교수연구실\"],\"505\":[\"임베디드시스템실\"],\"506\":[\"교수연구실\"],\"507\":[\"교수연구실\"],\"508\":[\"교수연구실\"],\"509\":[\"교수연구실\"],\"510\":[\"교수연구실\"],\"511\":[\"마이크로프로세서실\"],\"512\":[\"교수연구실\"],\"513\":[\"교수연구실\"],\"514\":[\"교수연구실\"],\"515\":[\"교수연구실\"],\"516\":[\"교수연구실\"],\"517\":[\"IT소프트웨어실\"],\"518\":[\"세미나실\"],\"519\":[\"학과사무실\"],\"520\":[\"학과사무실\"],\"531\":[\"연구실\"],\"532A\":[\"조영테크\"],\"532B\":[\"연구실\"],\"533\":[\"연구실\"],\"534\":[\"연구실\"],\"535\":[\"연구실\"],\"536\":[\"연구실\"],\"537\":[\"조영테크\"],\"539\":[\"대양이엔지\"],\"540\":[\"연구실\"],\"541\":[\"연구실\"],\"542\":[\"연구실\"],\"543\":[\"연구실\"],\"544\":[\"연구실\"],\"545\":[\"연구실\"],\"601\":[\"휴게실\"],\"602\":[\"종합설계실\"],\"603\":[\"교수연구실\"],\"604\":[\"교수연구실\"],\"605\":[\"교수연구실\"],\"606\":[\"교수연구실\"],\"607\":[\"교수연구실\"],\"608\":[\"교수연구실\"],\"609\":[\"교수연구실\"],\"610\":[\"교수연구실\"],\"611\":[\"통신시스템설계실\"],\"612\":[\"교수연구실\"],\"613\":[\"교수연구실\"],\"614\":[\"교수연구실\"],\"615\":[\"교수연구실\"],\"616\":[\"교수연구실\"],\"617\":[\"모바일프로그래밍실\"],\"618\":[\"세미나실\"],\"619\":[\"신호저리실습실\"],\"631\":[\"원컨덕터트레이딩\"],\"632\":[\"새롬시스\"],\"633\":[\"원컨덕터\"],\"634\":[\"리암솔루ㅜ션\"],\"635\":[\"연실\"],\"636\":[\"리암솔루션\"],\"637\":[\"아이두잇\"],\"639\":[\"연구실\"],\"640\":[\"연구실\"],\"641\":[\"연구실\"],\"642\":[\"알커미스\"],\"643\":[\"연구실\"],\"644\":[\"연구실\"],\"반납\":[\"반납장소\"],\"701\":[\"휴게실\"],\"702\":[\"강의실\"],\"703\":[\"모바일클라우드\"],\"704\":[\"화합물반도체관전소자\"],\"705\":[\"강의실\"],\"706\":[\"강의실\"],\"707\":[\"플라즈마라이트실용화\"],\"708\":[\"강의실\"],\"709\":[\"강의실\"],\"710\":[\"비즈니스솔루션\"],\"711\":[\"고주파부품및시스템\"],\"712\":[\"유비쿼터스네트워크\"],\"713\":[\"전자부품및시스템\"],\"714\":[\"멀티시스템통신시스템\"],\"715\":[\"차세대포토닉스\"],\"716\":[\"디지털서비스융합기술\"],\"717\":[\"스마트배터리\"],\"718\":[\"멀티미디어시스템국제협력\"],\"719\":[\"관산화물반도체\"],\"719-1\":[\"WCSLAB\"],\"720\":[\"기업연구관\"],\"721\":[\"기계진단및자동화\"]}";
    public String des_check_floor = "Null";
    public String[] object_name_list = new String[] {"PERSON","OBJECT","BICYCLE","CAR","MOTORCYCLE","BENCH","UMBRELLA","SUITCASE","BOTTLE","CHAIR","COUCH","POTTED PLANT","DINING TABLE","TV","LAPTOP","VASE"};
    public String[] object_name_kor_list = new String[] {"사람이","장애물이","자전거가","차가","오토바이가","벤치가","우산이","서류가방이","물병이","의자가","쇼파가","나무가","책상이","티비가","노트북이","화분이"};

    @Override
    protected void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        setContentView(R.layout.map_main);
        //FrameLayout touch_stt = (FrameLayout) findViewById(R.id.map_screen);
        textView = (TextView)findViewById(R.id.stt_text);
        pin = findViewById(R.id.floorplan_view);

        SharedPreferences get_cf = getSharedPreferences("walker_cf",MODE_PRIVATE);
        int current_map = get_cf.getInt("CF",0);
        //map_select(current_map);
        //test
        if(current_map == 0){
            current_floor = 7;
        }
        else{
            current_floor = current_map;
        }

//        System.out.println("현재층 onCreate");
//        System.out.println(current_floor);
        map_select(current_map);

        stt_i=new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        stt_i.putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE,getPackageName());
        stt_i.putExtra(RecognizerIntent.EXTRA_LANGUAGE,"ko-KR");
        stt_i.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS,true);

        tts = new TextToSpeech(this, new TextToSpeech.OnInitListener() {
            @Override
            public void onInit(int status) {
                if(status != ERROR) {
                    tts.setLanguage(Locale.KOREAN);
                }
            }
        });

        pin.setOnLongClickListener(new View.OnLongClickListener() {
            @Override
            public boolean onLongClick(View v) {
                System.out.println("Touched");
                stt_case_flag = 0;
                input_string = "NULL";
                find_floor_miss = 100;
                repeat_cheak = 0;
                first_input = 0;
                destination_list_check = 0;
                Check_command = 0;

                NAVIDOG_SPEAKPROCESS(stt_case_flag);
                //STT_START();
                return true;
            }
        });
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        check_topic = new CHECK_TOPIC();
        check_topic.start();

    }

    public RecognitionListener listener = new RecognitionListener() {
        @Override
        public void onReadyForSpeech(Bundle params) {

            Toast.makeText(getApplicationContext(), "음성인식을 시작합니다.", Toast.LENGTH_SHORT).show();
            Timer stt_ready_timer = new Timer();
            TimerTask stt_ready_check = new TimerTask() {
                @Override
                public void run() {
                    stt_ready = 1;
                    System.out.println("stt ready");

                }
            };

            stt_ready_timer.schedule(stt_ready_check,REQUEST_CODE_SPEECH_INPUT+1000);
        }

        @Override
        public void onBeginningOfSpeech() {
        }

        @Override
        public void onRmsChanged(float rmsdB) {
        }

        @Override
        public void onBufferReceived(byte[] buffer) {
        }

        @Override
        public void onEndOfSpeech() {
        }

        @Override
        public void onError(int error) {
            String message;

            switch (error) {
                case SpeechRecognizer.ERROR_AUDIO:
                    message = "오디오 에러";
                    break;
                case SpeechRecognizer.ERROR_CLIENT:
                    message = "클라이언트 에러";
                    break;
                case SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS:
                    message = "퍼미션 없음";
                    break;
                case SpeechRecognizer.ERROR_NETWORK:
                    message = "네트워크 에러";
                    break;
                case SpeechRecognizer.ERROR_NETWORK_TIMEOUT:
                    message = "네트웍 타임아웃";
                    break;
                case SpeechRecognizer.ERROR_NO_MATCH:
                    message = "찾을 수 없음";
                    break;
                case SpeechRecognizer.ERROR_RECOGNIZER_BUSY:
                    message = "RECOGNIZER가 바쁨";
                    break;
                case SpeechRecognizer.ERROR_SERVER:
                    message = "서버가 이상함";
                    break;
                case SpeechRecognizer.ERROR_SPEECH_TIMEOUT:
                    message = "말하는 시간초과";
                    break;
                default:
                    message = "알 수 없는 오류임";
                    break;
            }
            Toast.makeText(getApplicationContext(), "에러가 발생하였습니다. : " + message, Toast.LENGTH_SHORT).show();
            TTS_START("음성인식에 실패했습니다.");
        }

        @Override
        public void onResults(Bundle results) {
            stt_ready = 0;
            ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
            input_string = matches.get(0);
            input_string = input_string.replace(" ","");
            System.out.println(input_string);
            textView.setText(input_string);

            stt.destroy();

            if(first_input == 1){
                stt_case_flag = 1;
                first_input = 0;
                NAVIDOG_SPEAKPROCESS(stt_case_flag);
                return;
            }

            if(repeat_cheak == 1){
                if (input_string.equals("예") || input_string.equals("네") || input_string.equals("어") || input_string.equals("응")) {

                    switch (Check_command){
                        case 0:
                            input_string = "목적지";
                            break;
                        case 1:
                            input_string = "현재위치";
                            break;
                        case 2:
                            input_string = "목적지정보";
                            break;
                        case 3:
                            input_string = "재설정";
                            break;
                        case 4:
                            input_string = "목적지탐색";
                            break;
                    }

                    stt_case_flag = 1;
                    Check_command = 0;
                    repeat_cheak = 0;
                    NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    return;
                }
                else{
                    System.out.println("처음부터 반복");
                    stt_case_flag = 0;
                    first_input = 0;
                    NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    return;
                }
            }

            if(destination_list_check == 1){
                try {
                    JSONParser jsonParser = new JSONParser();
                    JSONObject jsonObject = (JSONObject) jsonParser.parse(map_info);
                    for(int floor = 1;floor <= floor_cnt;floor++){

                        destination_array = (JSONArray) jsonObject.get(Integer.toString(floor) + 'F');
                        assert destination_array != null;
                        for(Object destination:destination_array){
                            String destination_str = destination.toString();
                            System.out.println(destination_str);
                            if(destination_str.equals(input_string)){
                                stt_case_flag = 2;
                                destination_name = input_string;
                                goal_floor = floor;
                                if((current_floor == 1)&&(goal_floor == 1)) {
                                    if (x_s > 1775) {
                                        if ((destination_name.equals("131")) || (destination_name.equals("132")) || (destination_name.equals("133")) || (destination_name.equals("134")) || (destination_name.equals("135")) || (destination_name.equals("136")) || (destination_name.equals("137"))) {
                                            TTS_START("야외 이동입니다");
                                            TTS_START("네비독은 야외이동을 지원하지 않습니다");
                                            TTS_START("2층 경유해 이동해 주세요");
                                            stt_case_flag = 0;
                                            input_string = "NULL";
                                            find_floor_miss = 100;
                                            repeat_cheak = 0;
                                            first_input = 0;
                                            destination_list_check = 0;
                                            Check_command = 0;
                                            return;
                                        }
                                    }else {
                                        if ((destination_name.equals("101")) || (destination_name.equals("102")) || (destination_name.equals("103")) || (destination_name.equals("104")) || (destination_name.equals("105")) || (destination_name.equals("106")) || (destination_name.equals("107")) || (destination_name.equals("108")) || (destination_name.equals("110"))) {
                                            TTS_START("야외 이동입니다");
                                            TTS_START("네비독은 야외이동을 지원하지 않습니다");
                                            TTS_START("2층 경유해 이동해 주세요");
                                            stt_case_flag = 0;
                                            input_string = "NULL";
                                            find_floor_miss = 100;
                                            repeat_cheak = 0;
                                            first_input = 0;
                                            destination_list_check = 0;
                                            Check_command = 0;
                                            return;
                                        }
                                    }

                                }
                                System.out.println(destination_name);
                                System.out.println(current_floor);
                                System.out.println(goal_floor);
                                NAVIDOG_SPEAKPROCESS(stt_case_flag);
                                return;
                            }
                        }
                    }

                    for (int floor_miss = 1;floor_miss <= floor_cnt;floor_miss++) {
                        destination_array = (JSONArray) jsonObject.get(Integer.toString(floor_miss) + 'F');
                        assert destination_array != null;
                        for(Object destination:destination_array){
                            String destination_str = destination.toString();
                            int floor_miss_distance = Check_input.levenshteinDistance(destination_str, input_string);
                            if(floor_miss_distance <= find_floor_miss){
                                find_floor_miss = floor_miss_distance;
                                goal_floor = floor_miss;
                                destination_name = destination.toString();
                            }
                        }

                        if((current_floor == 1)&&(goal_floor == 1)) {
                            if (x_s > 1775) {
                                System.out.println("qweqweqwe" + x_s);
                                if ((destination_name.equals("131")) || (destination_name.equals("132")) || (destination_name.equals("133")) || (destination_name.equals("134")) || (destination_name.equals("135")) || (destination_name.equals("136")) || (destination_name.equals("137"))) {
                                    TTS_START("야외 이동입니다 네비독은 야외이동을 지원하지 않습니다 2층 경유해 이동해 주세요");
                                    stt_case_flag = 0;
                                    input_string = "NULL";
                                    find_floor_miss = 100;
                                    repeat_cheak = 0;
                                    first_input = 0;
                                    destination_list_check = 0;
                                    Check_command = 0;
                                    return;
                                }
                            }
                            else {
                                    System.out.println("qweqweqwe" + x_s);
                                    if ((destination_name.equals("101")) || (destination_name.equals("102")) || (destination_name.equals("103")) || (destination_name.equals("104")) || (destination_name.equals("105")) || (destination_name.equals("106")) || (destination_name.equals("107")) || (destination_name.equals("108")) || (destination_name.equals("110"))) {
                                        TTS_START("야외 이동입니다 네비독은 야외이동을 지원하지 않습니다 2층 경유해 이동해 주세요");
                                        stt_case_flag = 0;
                                        input_string = "NULL";
                                        find_floor_miss = 100;
                                        repeat_cheak = 0;
                                        first_input = 0;
                                        destination_list_check = 0;
                                        Check_command = 0;
                                        return;
                                    }
                                }
                            }


                        stt_case_flag = 2;
                        destination_list_check = 2;
                        System.out.println(destination_name);
                        System.out.println(current_floor);
                        System.out.println(goal_floor);
                        NAVIDOG_SPEAKPROCESS(stt_case_flag);
                        return;
                    }

                } catch (ParseException e) {
                    e.printStackTrace();
                }
            }

            if(destination_list_check == 3){
                if (input_string.equals("예") || input_string.equals("네") || input_string.equals("어") || input_string.equals("응")) {
                    stt_case_flag = 2;
                    destination_list_check = 1;
                    NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    return;
                }
                else{
                    destination_list_check = 0;
                    stt_case_flag = 1;
                    input_string = "목적지";
                    NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    return;
                }
            }

            if(destination_list_check == 4){
                if((input_string.contains("1"))||(input_string.contains("일"))){
                    des_check_floor = "1F";
                    stt_case_flag = 6;
                    NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    return;
                }
                else if((input_string.contains("2"))||(input_string.contains("이"))){
                    des_check_floor = "2F";
                    stt_case_flag = 6;
                    NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    return;
                }
                else if((input_string.contains("3"))||(input_string.contains("삼"))){
                    des_check_floor = "3F";
                    stt_case_flag = 6;
                    NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    return;
                }
                else if((input_string.contains("4"))||(input_string.contains("사"))){
                    des_check_floor = "4F";
                    stt_case_flag = 6;
                    NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    return;
                }
                else if((input_string.contains("5"))||(input_string.contains("오"))){
                    des_check_floor = "5F";
                    stt_case_flag = 6;
                    NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    return;
                }
                else if((input_string.contains("6"))||(input_string.contains("육"))){
                    des_check_floor = "6F";
                    stt_case_flag = 6;
                    NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    return;
                }
                else if((input_string.contains("7"))||(input_string.contains("칠"))){
                    des_check_floor = "7F";
                    stt_case_flag = 6;
                    NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    return;
                }
                else{
                    TTS_START("음성인식에 실패했습니다.");
                    input_string = "Null";
                    des_check_floor = "Null";
                    stt_case_flag = 0;
                    first_input = 0;
                    return;
                }
            }

        }

        @Override
        public void onPartialResults(Bundle partialResults) {
            ArrayList<String> data = partialResults.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
            ArrayList<String> unstableData = partialResults.getStringArrayList("android.speech.extra.UNSTABLE_TEXT");
            String mResult = data.get(0) + unstableData.get(0);
        }

        @Override
        public void onEvent(int eventType, Bundle params) {}

    };

    private long time= 0;
    @Override
    public void onBackPressed() {
        if(System.currentTimeMillis()-time>=2000){
            time=System.currentTimeMillis();
            Toast.makeText(getApplicationContext(),"뒤로 버튼을 한번 더 누르면 종료합니다.",Toast.LENGTH_SHORT).show();
        }else if(System.currentTimeMillis()-time<2000) {
            ActivityCompat.finishAffinity(this);
        }
    }

    public int cnt = 0;
    public void STT_START() {
        while (true) {
            if (!(tts.isSpeaking()) && (stt_ready == 1)) {
                tts.stop();
                stt = SpeechRecognizer.createSpeechRecognizer(this);
                stt.setRecognitionListener(listener);
                stt.startListening(stt_i);
                cnt += 1;
                System.out.println(cnt);
                break;
            }
        }
    }

    public void TTS_START(String tts_string) {
        wait_TTS();
        while (true) {
            if (!(tts.isSpeaking())) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                    tts.speak(tts_string,TextToSpeech.QUEUE_FLUSH,null,null);
                } else {
                    tts.speak(tts_string, TextToSpeech.QUEUE_FLUSH, null);
                }
                break;
            }
        }
        wait_TTS();
    }

    @Override
    protected void onStop() {
        super.onStop();
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }
    }

    public void wait_TTS() {
        while (true) {
            if (!(tts.isSpeaking())) {
                return;
            }
        }
    }

    //목적지: 목적지 검색
    //현재위치: 현재층, 현재층 목적지 리스트
    //목적지 정보: 목적지 층, 목적지 정보
    //재설정 : stt_case_flag=0, NAVIDOG_SPEAKPROSESS(stt_case_flag)

//    String[] command_list = {"목적지","현재위치","목적지정보","재설정"};
    String[] command_list = {"목적지","현재위치","목적지정보","재설정","목적지탐색"};

    public EditDistance Check_input = new EditDistance();
    public int[] distnace_array = new int[command_list.length];

    public void sleep(int sleep_time){
        try {
            Thread.sleep(sleep_time); //1초 대기
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    public String wall_warn_temp = "";
    public String object_name = "";
    public int[] object_pos = {0,0,0};
    private int NAVIDOG_SPEAKPROCESS(int case_flag){

        if(case_flag == 0) {

            TTS_START("말씀하세요");
            STT_START();
            first_input = 1;
            return 0;
        }

        if(case_flag == 1) {
            if (!input_string.equals("NULL")) {
                int function_sel = 9;
                for (int cnt = 0; cnt < command_list.length; cnt++) {
                    if (input_string.equals(command_list[cnt])) {
                        function_sel = cnt;
                        break;
                    }
                }

                switch (function_sel) {
                    case 0:
                        TTS_START("목적지를 말씀해 주세요");
                        destination_list_check = 1;
                        STT_START();
                        return 0;

                    case 1:
                        System.out.println("currnt_position");
                        TTS_START("현재위치는" + Integer.toString(current_floor) + "층 입니다.");
                        TTS_START("현재층에는");

                        try {
                            JSONParser jsonParser = new JSONParser();
                            JSONObject jsonObject = (JSONObject) jsonParser.parse(map_info);
                            destination_array = (JSONArray) jsonObject.get(Integer.toString(current_floor) + 'F');
                            assert destination_array != null;
                            System.out.println(destination_array);
                        } catch (ParseException e) {
                            e.printStackTrace();
                        }
                        for(Object destination:destination_array){
                            String destination_str = destination.toString();
                            System.out.println(destination_str);
                            TTS_START(destination_str);

                        }

                        TTS_START("가 있습니다.");

                        return 0;
                    case 2:
                        if(destination_name.equals("NULL")){
                            TTS_START("목적지가 설정되있지 않습니다. 목적지를 설정해 주세요");
                            return 0;
                        }
                        TTS_START("목적지는" + destination_name +"입니다.");

                        TTS_START(destination_name + "은" + Integer.toString(goal_floor)+"층 이며");

                        try {
                            System.out.println("try");
                            JSONParser jsonParser = new JSONParser();
                            JSONObject jsonObject = (JSONObject) jsonParser.parse(destination_info);
                            destination_array = (JSONArray) jsonObject.get(destination_name);
                            System.out.println(destination_name);
                            System.out.println(destination_array);
                            assert destination_array != null;
                            System.out.println(destination_array);
                        } catch (ParseException e) {
                            e.printStackTrace();
                        }

                        TTS_START((String) destination_array.get(0) + "입니다.");

                        return 0;
                    case 3:
                        destination_name = "NULL";
                        stt_case_flag = 1;
                        input_string = "목적지";
                        find_floor_miss = 100;
                        repeat_cheak = 0;
                        first_input = 0;
                        destination_list_check = 0;
                        Check_command = 0;
                        TTS_START("목적지를 재설정 합니다");
                        String message = "Research";
                        try {
                            MainActivity.client.publish("VOICE"+Integer.toString(MainActivity.WALKER_NUM), message.getBytes(), 0, false);
                        } catch (MqttException e) {
                            e.printStackTrace();
                        }
                        while (true) {
                            if (!(tts.isSpeaking())) {
                                NAVIDOG_SPEAKPROCESS(stt_case_flag);
                                break;
                            }
                        }
                        break;

                    case 4:
                        TTS_START("원하시는 층을 말씀해 주세요");
                        STT_START();
                        destination_list_check = 4;
                        break;
                    case 9:
                        int Check_distance = 0;
                        System.out.println("idontunderstand");
                        repeat_cheak = 1;
                        for (int cnt = 0; cnt < command_list.length; cnt++) {
                            Check_distance = Check_input.levenshteinDistance(command_list[cnt], input_string);
                            distnace_array[cnt] = Check_distance;
                        }
                        break;
                }

                if (repeat_cheak == 1) {
                    int min = distnace_array[0];

                    for (int cnt = 0; cnt < distnace_array.length; cnt++) {
                        if (min > distnace_array[cnt]) {
                            min = distnace_array[cnt];
                            Check_command = cnt;
                        }
                    }
                    System.out.println("\n");
                    System.out.println("repeat");
                    TTS_START(command_list[Check_command] + "를 말하셨나요?");
                    STT_START();
                    return 0;
                }
            }
        }

        if(case_flag == 2){
            switch (destination_list_check){
                case 1:
                    String message = Integer.toString(current_floor) + '/' + Integer.toString(goal_floor);
                    if((destination_name.equals("남자화장실"))||(destination_name.equals("여자화장실"))){
                        message = Integer.toString(current_floor) + '/' + Integer.toString(current_floor);
                        goal_floor = current_floor;
                    }
                    try {
                        MainActivity.client.publish("FLOOR"+Integer.toString(MainActivity.WALKER_NUM), message.getBytes(), 1, false);
                    } catch (MqttException e) {
                        e.printStackTrace();
                    }
                    message = destination_name;
                    //////////////////////////////////////////////////
                    if(message.equals("남자화장실")){
                        message = "toilet_m";
                    }
                    if(message.equals("여자화장실")){
                        message = "toilet_r";
                    }
                    if(message.equals("반납")){
                        message = "RETURN";
                    }
                    ////////////////////////////////////////////////
                    try {
                        MainActivity.client.publish("VOICE"+Integer.toString(MainActivity.WALKER_NUM), message.getBytes(), 1, false);
                    } catch (MqttException e) {
                        e.printStackTrace();
                    }
                    TTS_START(destination_name+"으로 안내하겠습니다.");
                    destination_list_check = 0;
                    return 0;

                case 2:
                    TTS_START(destination_name+"를 말하셨나요?");
                    STT_START();
                    destination_list_check = 3;
                    break;
            }
        }

        if(case_flag == 3){
            String path_nav = "";
            if(!(next_path_s.equals(""))){

                switch(next_path_s){
                    case "U":
                        path_nav = "앞으로";
                        break;
                    case "UL":
                        path_nav = "왼쪽 앞으로";
                        break;
                    case "L":
                        path_nav = "왼쪽으로";
                        break;
                    case "DL":
                        path_nav = "왼쪽 뒤로";
                        break;
                    case "D":
                        path_nav = "뒤로";
                        break;
                    case "DR":
                        path_nav = "오른쪽 뒤로";
                        break;
                    case "R":
                        path_nav = "오른쪽으로";
                        break;
                    case "UR":
                        path_nav = "오른쪽 앞으로";
                        break;

                }
                TTS_START(path_nav + "가세요.");

                path_nav = "";
                next_path_s = "";

            }

            String wall_warn = "";
            if(wall_s.length != 0){
                if(Arrays.toString(wall_s).contains("\'U\'")){
                    wall_warn = "앞에";
                }
                else if(Arrays.toString(wall_s).contains("\'L\'")){
                    wall_warn = "왼쪽에";
                }
                else if(Arrays.toString(wall_s).contains("\'D\'")){
                    wall_warn = "뒤에";
                }
                else if(Arrays.toString(wall_s).contains("\'R\'")){
                    wall_warn = "오른쪽에";
                }
                if(!(wall_warn.equals(wall_warn_temp))) {
                    TTS_START(wall_warn + " 벽이 있습니다. 조심하세요");
                }
                if(Arrays.toString(wall_s).contains("\'2FDOOR\'")) {
                    TTS_START("전방에 문이 있습니다.");
                }
                wall_warn_temp = wall_warn;
                wall_warn = "";
                wall_s = new String[]{};
            }
            return 0;
        }

        if(case_flag == 4){
            if(object_position_s.length != 0){
                for(String name_pos:object_position_s){
                    for(int cnt1=0;cnt1<object_name_list.length;cnt1++){
                        if(name_pos.contains(object_name_list[cnt1])){
                            object_name = object_name_kor_list[cnt1];
                            TTS_START(object_name);
                            if((name_pos.contains("RIGHT"))&&(right_check == 0)){
                                TTS_START("오른쪽에");
                                object_pos[2] = 1;
                                right_check = 1;
                            }
                            else if((name_pos.contains("CENTER"))&&(center_check == 0)){
                                TTS_START("앞에");
                                object_pos[1] = 1;
                                center_check = 1;
                            }
                            if((name_pos.contains("LEFT"))&&(left_check == 0)){
                                TTS_START("왼쪽에");
                                object_pos[0] = 1;
                                left_check = 1;
                            }
                            break;
                        }
                    }
                }
                TTS_START("있습니다.");
                for(int cnt2 = 0; cnt2 < object_pos.length;cnt2++){
                    if(object_pos[cnt2] == 0){
                        switch (cnt2){
                            case 0:
                                TTS_START("왼쪽으로 피하세요");
                                break;
                            case 1:
                                TTS_START("정면으로 피하세요");
                                break;
                            case 2:
                                TTS_START("오른쪽으로 피하세요");
                                break;
                        }
                        object_pos = new int[]{0, 0, 0};
                        object_position_s = new String[] {};
                        object_name = "";
                        right_check = 0;
                        center_check = 0;
                        left_check = 0;
                        return 0;
                    }
                }

                TTS_START("전방에 장애물이 많습니다. 잠시 기다리신후 천천히 이동하세요.");
                object_pos = new int[]{0, 0, 0};
                object_position_s = new String[] {};
                object_name = "";
                return 0;
            }
        }

        if(case_flag == 5){

            if(button_stat_s == 3){
                TTS_START("아래버튼을 누른뒤 엘리베이터가 도착하면 탑승하세요.");
                return 0;
            }
            System.out.println(elevator_set_s);
            System.out.println(button_stat_s);
            if(elevator_set_s == 1){

                if((elev_cnt == 0)&&(button_stat_s == 0)){
                    TTS_START("위버튼을 누른뒤 엘리베이터가 도착하면 탑승하세요.");
                    elev_cnt = 10;
                    return 0;
                }

                if((elev_cnt == 0)&&(button_stat_s == 2)){
                    TTS_START("엘리베이터가 아래층으로 갑니다. 잠시 기다려 주세요.");
                    elev_cnt = 1;
                    return 0;
                }

                if((elev_cnt == 0)&&(button_stat_s == 1)){
                    TTS_START("엘리베이터가 오고있습니다. 도착하면 탑승해 주세요");
                    return 0;
                }

                if((elev_cnt == 1)&&(button_stat_s == 0)){
                    TTS_START("위버튼을 누른뒤 엘리베이터가 도착하면 탑승하세요.");
                    elev_cnt = 10;
                    return 0;
                }

                if((elev_cnt == 10)&&(button_stat_s == 1)){
                    TTS_START("위버튼을 눌렀습니다.");
                    elev_cnt = 0;
                    return 0;
                }

                if((elev_cnt == 10)&&(button_stat_s == 2)){
                    TTS_START("아래 버튼을 눌렀습니다. 아래버튼을 한번 더 누르고 위버튼을 다시 눌러 주세요.");
                    return 0;
                }

            }

            if(elevator_set_s == 2){

                if((elev_cnt == 0)&&(button_stat_s == 0)){
                    TTS_START("아래버튼을 누른뒤 엘리베이터가 도착하면 탑승하세요.");
                    elev_cnt = 10;
                    return 0;
                }

                if((elev_cnt == 0)&&(button_stat_s == 1)){
                    TTS_START("엘리베이터가 위층으로 갑니다. 잠시 기다려 주세요.");
                    elev_cnt = 1;
                    return 0;
                }

                if((elev_cnt == 0)&&(button_stat_s == 2)){
                    TTS_START("엘리베이터가 오고있습니다. 도착하면 탑승해 주세요");
                    return 0;
                }

                if((elev_cnt == 1)&&(button_stat_s == 0)){
                    TTS_START("아래버튼을 누른뒤 엘리베이터가 도착하면 탑승하세요.");
                    elev_cnt = 10;
                    return 0;
                }

                if((elev_cnt == 10)&&(button_stat_s == 2)){
                    TTS_START("아래버튼을 눌렀습니다.");
                    elev_cnt = 0;
                    return 0;
                }

                if((elev_cnt == 10)&&(button_stat_s == 1)){
                    TTS_START("위 버튼을 눌렀습니다. 위버튼을 한번 더 누르고 아래버튼을 다시 눌러 주세요.");
                    return 0;
                }

            }
        }

        if(case_flag == 6){
            TTS_START(des_check_floor + "에는");

            try{
            JSONParser jsonParser = new JSONParser();
            JSONObject jsonObject = (JSONObject) jsonParser.parse(map_info);
            destination_array = (JSONArray) jsonObject.get(des_check_floor);
            assert destination_array != null;
            System.out.println(destination_array);
            } catch (ParseException e) {
                e.printStackTrace();
            }
            for(Object destination:destination_array){
                String destination_str = destination.toString();

                try{
                    JSONParser jsonParser = new JSONParser();
                    JSONObject jsonObject = (JSONObject) jsonParser.parse(destination_info);
                    destination_array = (JSONArray) jsonObject.get(destination_str);
                    assert destination_array != null;
                    System.out.println(destination_array);
                } catch (ParseException e) {
                    e.printStackTrace();
                }
                System.out.println(destination_str);
                TTS_START(destination_str);
                TTS_START((String)destination_array.get(0));
            }
            TTS_START("가 있습니다.");
            repeat_cheak = 0;
            first_input = 0;
            destination_list_check = 0;
            Check_command = 0;
            des_check_floor = "Null";
        }
        return 0;
    }


    public int path1_end_xst;
    public int path1_end_yst;
    public int path1_end_xed;
    public int path1_end_yed;
    public int path2_end_xst;
    public int path2_end_yst;
    public int path2_end_xed;
    public int path2_end_yed;
    public int temp = 0;
    public int path1_done = 0;
    public int path2_done = 0;
    private class CHECK_TOPIC extends Thread{

        public void run(){
            while (true){

                if((MainActivity.path1.length != 1)&&(MainActivity.path1.length != 0)) {
                    path1_done = 0;
                    path1_s = MainActivity.path1;
                    System.out.println(Arrays.toString(path1_s));
                    String A = path1_s[path1_s.length - 4].replace(" ","");
                    String B = path1_s[path1_s.length - 3].replace(" ","");
                    String C = path1_s[path1_s.length - 2].replace(" ","");
                    String D = path1_s[path1_s.length - 1].replace(" ","");
                    path1_end_xst = Integer.parseInt(A);
                    path1_end_yst = Integer.parseInt(B);
                    path1_end_xed = Integer.parseInt(C);
                    path1_end_yed = Integer.parseInt(D);
                    map_path_show = new MAP_PATH_SHOW();
                    map_path_show.start();
                    MainActivity.path1 = new String[]{};
                }

                if((MainActivity.path2.length != 1)&&(MainActivity.path2.length != 0)){
                    path2_done = 0;
                    path2_s = MainActivity.path2;
                    System.out.println(Arrays.toString(path2_s));
                    String A = path2_s[path2_s.length - 4].replace(" ","");
                    String B = path2_s[path2_s.length - 3].replace(" ","");
                    String C = path2_s[path2_s.length - 2].replace(" ","");
                    String D = path2_s[path2_s.length - 1].replace(" ","");
                    path2_end_xst = Integer.parseInt(A);
                    path2_end_yst = Integer.parseInt(B);
                    path2_end_xed = Integer.parseInt(C);
                    path2_end_yed = Integer.parseInt(D);
                    System.out.println("path2 on");
                    MainActivity.path2 = new String[]{};
                }

                if(MainActivity.wall.length != 0){
                    wall_s = MainActivity.wall;
                    System.out.println(Arrays.toString(wall_s));
                    stt_case_flag = 3;
                    NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    MainActivity.wall = new String[]{};
                }

                if(!MainActivity.next_path.equals("")){
                    next_path_s = MainActivity.next_path;
                    System.out.println(next_path_s);
                    stt_case_flag = 3;
                    NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    MainActivity.next_path = "";
                }

                if(MainActivity.object_position.length != 0){
                    object_position_s = MainActivity.object_position;
                    System.out.println(Arrays.toString(object_position_s));
                    stt_case_flag = 4;
                    NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    MainActivity.object_position = new String[]{};
                }

                if(MainActivity.button_stat != -1){
                    if(current_floor < goal_floor ){elevator_set_s = 1;}
                    else{elevator_set_s = 2;}
                    button_stat_s = MainActivity.button_stat;
                    System.out.println(elevator_set_s);
                    System.out.println(button_stat_s);
                    if(elevator_set_s != 0){
                        stt_case_flag = 5;
                        System.out.println(button_stat_s);
                        NAVIDOG_SPEAKPROCESS(stt_case_flag);
                    }
                    MainActivity.button_stat = -1;
                }

                if((MainActivity.x != 0)||(MainActivity.y != 0)){

//                    x_s = Math.round(MainActivity.x + 705);
//                    y_s = Math.round(MainActivity.y + 2345);
                    x_s = Math.round(MainActivity.x);
                    y_s = Math.round(MainActivity.y);

                    if (pin.isReady()) {

                        currnet_pos_show = new CURRNET_POS_SHOW();
                        currnet_pos_show.start();
                    }

                }

                if((MainActivity.wait.equals("1"))){
                    TTS_START("위치 조정중 입니다. 잠시 기다리신후 다시 이동해 주세요.");
                    MainActivity.wait = "0";
                }

                if((MainActivity.repose.equals("1"))){
                    TTS_START("경로탐색에 실패했습니다. 벽에서 멀어지신뒤 다시 목적지를 입력해 주세요.");
                    MainActivity.repose = "0";
                }

            }
        }
    }

    private class MAP_PATH_SHOW extends Thread {
        public void run() {
            System.out.println("yea");
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
//                    if((path1_s.length != 0)&&(current_floor != 0)){
                    if((path1_s.length != 0)){

//                        System.out.println("현재층 path1");
//                        System.out.println(current_floor);

                        Bitmap map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map5);
                        int origin_size_width = map_f.getWidth();
                        int origin_size_height = map_f.getHeight();
                        System.out.println(origin_size_width);
                        System.out.println(origin_size_height);

                        switch (current_floor){
                            case 1:
                                map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map1);
                                break;
                            case 2:
                                map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map2);
                                break;
                            case 3:
                                map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map3);
                                break;
                            case 4:
                                map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map4);
                                break;
                            case 5:
                                map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map5);
                                break;
                            case 6:
                                map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map6);
                                break;
                            case 7:
                                map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map7);
                                break;
                        }
                        Bitmap resizedBitmap = getResizedBitmap(map_f,3550,2561);

                        Mat map_f_mat = new Mat();
                        Utils.bitmapToMat(resizedBitmap, map_f_mat);

                        int cnt = 0;
                        int topx = 0;
                        int topy = 0;
                        int botx = 0;
                        int boty = 0;
                        for(String ing:path1_s){
                            ing = ing.replace(" ","");
                            //for(int ing:test_path){
                            switch(cnt){
                                case 0:
                                    topx = Integer.parseInt(ing);
                                    break;
                                case 1:
                                    topy = Integer.parseInt(ing);
                                    break;
                                case 2:
                                    botx = Integer.parseInt(ing);
                                    break;
                                case 3:
                                    boty =  Integer.parseInt(ing);
                                    break;
                            }
                            cnt++;
                            if(cnt == 4){
                                Imgproc.rectangle(map_f_mat,new Point(topx,topy), new Point(botx, boty), new Scalar(0,255,0,255),-1);
                                cnt = 0;
                            }

                        }
                        Utils.matToBitmap(map_f_mat, resizedBitmap);
                        resizedBitmap = getResizedBitmap(resizedBitmap,2310, 2307);
                        pin.setImage(ImageSource.bitmap(resizedBitmap));
//                        path1_s = new String[] {};
                    }

                    if((path2_s.length != 0)&&(path1_s.length == 0)) {
//                        System.out.println("현재층 path2");
//                        System.out.println(current_floor);
                        Bitmap map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map5);
                        int origin_size_width = map_f.getWidth();
                        int origin_size_height = map_f.getHeight();

                        switch (current_floor) {
                            case 1:
                                map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map1);
                                break;
                            case 2:
                                map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map2);
                                break;
                            case 3:
                                map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map3);
                                break;
                            case 4:
                                map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map4);
                                break;
                            case 5:
                                map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map5);
                                break;
                            case 6:
                                map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map6);
                                break;
                            case 7:
                                map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map7);
                                break;
                        }

                        Bitmap resizedBitmap = getResizedBitmap(map_f, 3550, 2561);

                        Mat map_f_mat = new Mat();
                        Utils.bitmapToMat(resizedBitmap, map_f_mat);

                        int cnt = 0;
                        int topx = 0;
                        int topy = 0;
                        int botx = 0;
                        int boty = 0;
                        for (String ing : path2_s) {
                            ing = ing.replace(" ", "");
                            //for(int ing:test_path){
                            switch (cnt) {
                                case 0:
                                    topx = Integer.parseInt(ing);
                                    break;
                                case 1:
                                    topy = Integer.parseInt(ing);
                                    break;
                                case 2:
                                    botx = Integer.parseInt(ing);
                                    break;
                                case 3:
                                    boty = Integer.parseInt(ing);
                                    break;
                            }
                            cnt++;
                            if (cnt == 4) {
                                Imgproc.rectangle(map_f_mat, new Point(topx, topy), new Point(botx, boty), new Scalar(0, 255, 0, 255), -1);
                                cnt = 0;
                            }

                        }
                        Utils.matToBitmap(map_f_mat, resizedBitmap);
                        resizedBitmap = getResizedBitmap(resizedBitmap, 2310, 2307);
                        pin.setImage(ImageSource.bitmap(resizedBitmap));
                    }
                }
            });
        }
    }


    public PointF point;
    private class CURRNET_POS_SHOW extends Thread {
        public void run(){
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    point = new PointF(x_s*0.6507f, y_s*0.90081f);
                    if((path2_s.length  >1)){
                        if ((x_s > path1_end_xst)&&(x_s<path1_end_xed)&&(y_s > path1_end_yst)&&(y_s<path1_end_yed)){
                            current_floor = goal_floor;
                            SharedPreferences save_cf = getSharedPreferences("walker_cf", MODE_PRIVATE);
                            @SuppressLint("CommitPrefEdits") SharedPreferences.Editor editor = save_cf.edit();
                            editor.putInt("CF", current_floor);
                            editor.commit();
                            //map_select(current_floor);
                            if(path1_done == 0) {
                                if(!(destination_name.equals("반납"))) {
                                    TTS_START("엘레베이터에 도착했습니다. 엘레베이터 버튼을 인식하기 위해 천천히");
                                    path1_s = new String[]{};
                                    map_path_show = new MAP_PATH_SHOW();
                                    map_path_show.start();
                                }
                            }
                            path1_done = 1;
                        }

                        if ((x_s > path2_end_xst)&&(x_s<path2_end_xed)&&(y_s > path2_end_yst)&&(y_s<path2_end_yed)){
                            if(path2_done == 0) {
                                TTS_START("목적지에 도착했습니다.");

                                if(destination_name.equals("반납")){
                                    SharedPreferences leave_cf = getSharedPreferences("walker_cf", MODE_PRIVATE);
                                    @SuppressLint("CommitPrefEdits") SharedPreferences.Editor editor_c = leave_cf.edit();
                                    editor_c.putInt("CF", 0);
                                    editor_c.commit();
                                    SharedPreferences leave_num = getSharedPreferences("walker_num", 0);
                                    @SuppressLint("CommitPrefEdits") SharedPreferences.Editor editor_w = leave_num.edit();
                                    editor_w.putInt("WN", 0);
                                    editor_w.commit();
                                    String free = Integer.toString(MainActivity.WALKER_NUM);
                                    try {
                                        MainActivity.client.publish("FREE_DEVICE",free.getBytes(),1,false);
                                    } catch (MqttException e) {
                                        e.printStackTrace();
                                    }
                                    TTS_START("보행기를 반납하기위해 천천히");

                                }
                            }
                            path2_done = 1;
                        }

                    }
                    else {
                        if ((x_s > path1_end_xst)&&(x_s<path1_end_xed)&&(y_s > path1_end_yst)&&(y_s<path1_end_yed)){
                            if(path1_done == 0) {
                                TTS_START("목적지에 도착했습니다.");
                                if(destination_name.equals("반납")){
                                    SharedPreferences leave_cf = getSharedPreferences("walker_cf", MODE_PRIVATE);
                                    @SuppressLint("CommitPrefEdits") SharedPreferences.Editor editor_c = leave_cf.edit();
                                    editor_c.putInt("CF", 0);
                                    editor_c.commit();
                                    SharedPreferences leave_num = getSharedPreferences("walker_num", 0);
                                    @SuppressLint("CommitPrefEdits") SharedPreferences.Editor editor_w = leave_num.edit();
                                    editor_w.putInt("WN", 0);
                                    editor_w.commit();
                                    String free = Integer.toString(MainActivity.WALKER_NUM);
                                    try {
                                        MainActivity.client.publish("FREE_DEVICE",free.getBytes(),1,false);
                                    } catch (MqttException e) {
                                        e.printStackTrace();
                                    }
                                    TTS_START("보행기를 반납하기위해 천천히");
                                }
                            }
                            path1_done = 1;
                        }
                    }
//                    Random random = new Random();
//                    float maxScale = pin.getMaxScale();
//                    float minScale = pin.getMinScale();
                    pin.setPin(point);
                    SubsamplingScaleImageView.AnimationBuilder animationBuilder = pin.animateScaleAndCenter(7F, point);
                    assert animationBuilder != null;
                    animationBuilder.withDuration(750).start();
//                    System.out.println("hey");
                    MainActivity.deg = 0;
                    MainActivity.y = 0;
                    MainActivity.x = 0;

                }
            });
        }
    }

    private void map_select(final int map_number){
        runOnUiThread(new Runnable() {
            @Override
            public void run(){
                Bitmap map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map1);
                switch (map_number){
                    case 0:
                        map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map7);
                        break;
                    case 1:
                        map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map1);
                        break;
                    case 2:
                        map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map2);
                        break;
                    case 3:
                        map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map3);
                        break;
                    case 4:
                        map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map4);
                        break;
                    case 5:
                        map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map5);
                        break;
                    case 6:
                        map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map6);
                        break;
                    case 7:
                        map_f = BitmapFactory.decodeResource(getApplicationContext().getResources(), R.drawable.map7);
                        break;
                }
                Bitmap resizedBitmap = getResizedBitmap(map_f, 3550, 2561);
                resizedBitmap = getResizedBitmap(resizedBitmap, 2310, 2307);
                pin.setImage(ImageSource.bitmap(resizedBitmap));
            }
        });
    }

    public Bitmap getResizedBitmap(Bitmap bm, int newWidth, int newHeight) {
        int width = bm.getWidth();
        int height = bm.getHeight();
        float scaleWidth = ((float) newWidth) / width;
        float scaleHeight = ((float) newHeight) / height;
        // CREATE A MATRIX FOR THE MANIPULATION
        Matrix matrix = new Matrix();
        // RESIZE THE BIT MAP
        matrix.postScale(scaleWidth, scaleHeight);

        // "RECREATE" THE NEW BITMAP
        Bitmap resizedBitmap = Bitmap.createBitmap(
                bm, 0, 0, width, height, matrix, false);
        bm.recycle();
        return resizedBitmap;
    }
}


