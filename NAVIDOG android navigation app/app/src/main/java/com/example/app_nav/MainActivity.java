package com.example.app_nav;


import androidx.appcompat.app.AppCompatActivity;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.constraintlayout.widget.Constraints;
import androidx.core.app.ActivityCompat;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.icu.text.SimpleDateFormat;
import android.icu.util.Calendar;
import android.media.Image;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.speech.RecognizerIntent;
import android.speech.tts.TextToSpeech;
import android.telephony.TelephonyManager;
import android.util.Log;
import android.view.View;
import android.view.ViewDebug;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import android.graphics.Matrix;
import android.content.pm.PackageManager;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.widget.Button;

import org.eclipse.paho.android.service.MqttAndroidClient;
import org.eclipse.paho.client.mqttv3.IMqttActionListener;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.IMqttToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;

import org.opencv.android.BaseLoaderCallback;
import org.opencv.android.LoaderCallbackInterface;
import org.opencv.android.OpenCVLoader;
import org.opencv.android.Utils;
import org.opencv.core.Mat;
import org.opencv.imgproc.Imgproc;

import java.lang.reflect.Array;
import java.nio.file.Watchable;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Locale;
import java.util.UUID;
import java.util.regex.Pattern;

import android.provider.Settings.Secure;

import static android.speech.tts.TextToSpeech.ERROR;


public class MainActivity extends AppCompatActivity {


    TextToSpeech tts;
    private static final int PERMISSION = 1;
    private static final String TODO = "Null";
    public static MqttAndroidClient client;
    String SERVER = "3.23.235.70";
    public static int WALKER_NUM = 0;
    SCREEN_CHANGE_TH screen_main_th;
    TOPIC_SUB topic_sub;
    private final static String TAG = MainActivity.class.getClass().getSimpleName();
    private boolean isOpenCvLoaded = false;
    public static String[] path1 = new String[]{};
    public static String[] path2 = new String[]{};
    public static String[] wall = new String[]{};
    public static String[] object_position = new String[]{};
    public static String next_path = "";
    public static String wait = "";
    public static String repose = "";
    public static float x = 0;
    public static float y = 0;
    public static int deg = 0;
    public static int rotate = 0;
    public static int button_stat = -1;
    public String get_id = "Null";

    public String PATH1 = "PATHA";
    public String PATH2 = "PATHB";
    public String POSITION = "POSITION_NAV";
    public String WALL = "WALL";
    public String ELEVATOR = "ELEVATOR";
    public String NEXT_PATH = "NEXT_PATH";
    public String OBJECT_POSITION = "OBJECT_POSITION";
    public String NAVIGATION = "NAVIGATION";
    public String WAIT = "WAIT";
    public String REPOSITION = "REPOSITION";


    @Override
    public void onCreate(Bundle savedInstanceState) {

        if (Build.VERSION.SDK_INT >= 23) {
            // 퍼미션 체크
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.INTERNET,
                    Manifest.permission.RECORD_AUDIO, Manifest.permission.READ_PHONE_STATE}, PERMISSION);
        }
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Calendar cal = Calendar.getInstance();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy / MM / dd / HH:mm:ss");
        String datestr = sdf.format(cal.getTime());
        System.out.println(datestr);

        while (true){
            get_id = getDeviceId(MainActivity.this);
            System.out.println(get_id);
            if (!(get_id.equals("Null"))){
                break;
            }
        }


        SharedPreferences road_num = getSharedPreferences("walker_num", 0);
        WALKER_NUM = road_num.getInt("WN", 0);
        if (WALKER_NUM != 0){
            if (Build.VERSION.SDK_INT >= 23) {
                // 퍼미션 체크
                ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.INTERNET,
                        Manifest.permission.RECORD_AUDIO, Manifest.permission.READ_PHONE_STATE}, PERMISSION);
            }
        }

        tts = new TextToSpeech(this, new TextToSpeech.OnInitListener() {
            @Override
            public void onInit(int status) {
                if(status != ERROR) {
                    tts.setLanguage(Locale.KOREAN);
                }
            }
        });
        //////////////////////////////////////////////
//        WALKER_NUM = 0;
        /////////////////////////////////////////////
        final TextView start_state = (TextView) findViewById(R.id.start_state);
        client = new MqttAndroidClient(this.getApplicationContext(), "tcp://" + SERVER + ":1883",datestr);
        screen_main_th = new SCREEN_CHANGE_TH();
        screen_main_th.start();
        start_state.setText("서버 접속중...");
        try {
            IMqttToken token = client.connect();
            token.setActionCallback(new IMqttActionListener() {
                @Override
                public void onSuccess(IMqttToken asyncActionToken) {
//                    Toast.makeText(MainActivity.this, "connected", Toast.LENGTH_LONG).show();
                    start_state.setText("보행기에 접속중...");
                    System.out.println("connect");
                    String message = get_id;
                    try {
                        client.publish("REQUEST_WALKER", message.getBytes(), 2, false);
                    } catch (MqttException e) {
                        e.printStackTrace();
                    }

                    RESPOND_WALKER();
//                    PATH1(PATH1);
//                    PATH2(PATH2);
//                    POSITION(POSITION);
//                    NEXT_PATH(NEXT_PATH);
//                    WALL_WARN(WALL);
//                    OBJECT_WARN(OBJECT_POSITION);
//                    ELEVATOR(ELEVATOR);
                    if(WALKER_NUM != 0){

                        PATH1 = PATH1 + Integer.toString(WALKER_NUM);
                        PATH2 = PATH2 + Integer.toString(WALKER_NUM);
                        POSITION = POSITION + Integer.toString(WALKER_NUM);
                        NEXT_PATH = NEXT_PATH + Integer.toString(WALKER_NUM);
                        WALL = WALL + Integer.toString(WALKER_NUM);
                        OBJECT_POSITION = OBJECT_POSITION + Integer.toString(WALKER_NUM);
                        ELEVATOR = ELEVATOR + Integer.toString(WALKER_NUM);
//                        NAVIGATION = NAVIGATION + Integer.toString(WALKER_NUM);
                        WAIT = WAIT + Integer.toString(WALKER_NUM);
                        REPOSITION = REPOSITION + Integer.toString(WALKER_NUM);
                        topic_sub = new TOPIC_SUB();
                        topic_sub.start();
                        String walker_num = "보행기" + Integer.toString(WALKER_NUM) + " 연결완료";
                        if (!(tts.isSpeaking())) {
                            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                                tts.speak("보행기에 연결되었습니다",TextToSpeech.QUEUE_FLUSH,null,null);
                            } else {
                                tts.speak("보행기에 연결되었습니다", TextToSpeech.QUEUE_FLUSH, null);
                            }

                        }

                        rotate = 1;
                        screen_main_th.interrupt();
                        Intent screen_change = new Intent(getApplicationContext(), Map.class);
                        startActivity(screen_change);
                    }

                }

                @Override
                public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
//                    Toast.makeText(MainActivity.this, "not connected", Toast.LENGTH_LONG).show();
                    start_state.setText("서버 접속 실패");
                    System.out.println("not connect");
                }
            });
        } catch (MqttException e) {
            e.printStackTrace();
        }

        client.setCallback(new MqttCallback() {
            @Override
            public void connectionLost(Throwable cause) {

            }

            @Override
            public void messageArrived(String topic, MqttMessage message) throws Exception {
                System.out.println(topic);
                if ((topic.equals("RESPOND_WALKER")) && (WALKER_NUM == 0)) {
                    String sum_msg = new String(message.getPayload());
                    System.out.println(sum_msg);
                    String[] walker_app = sum_msg.split("/");
                    System.out.println(walker_app[1]);
                    if(walker_app[1].equals(get_id)) {
                        WALKER_NUM = Integer.parseInt(walker_app[0]);
                        SharedPreferences save_num = getSharedPreferences("walker_num", 0);
                        @SuppressLint("CommitPrefEdits") SharedPreferences.Editor editor = save_num.edit();
                        editor.putInt("WN", WALKER_NUM);
                        editor.commit();
                        PATH1 = PATH1 + Integer.toString(WALKER_NUM);
                        PATH2 = PATH2 + Integer.toString(WALKER_NUM);
                        POSITION = POSITION + Integer.toString(WALKER_NUM);
                        NEXT_PATH = NEXT_PATH + Integer.toString(WALKER_NUM);
                        WALL = WALL + Integer.toString(WALKER_NUM);
                        OBJECT_POSITION = OBJECT_POSITION + Integer.toString(WALKER_NUM);
                        ELEVATOR = ELEVATOR + Integer.toString(WALKER_NUM);
                        NAVIGATION = NAVIGATION + Integer.toString(WALKER_NUM);
                        WAIT = WAIT + Integer.toString(WALKER_NUM);
                        REPOSITION = REPOSITION + Integer.toString(WALKER_NUM);
                        topic_sub = new TOPIC_SUB();
                        topic_sub.start();



                    }
                }

                if ((topic.equals(NAVIGATION)) && (WALKER_NUM != 0)) {
                    int sum_msg = Integer.parseInt(new String(message.getPayload()));
                    if(sum_msg == 1){
                        String walker_num = "보행기" + Integer.toString(WALKER_NUM) + " 연결완료";
                        start_state.setText(walker_num);
                        rotate = 1;
                        if (!(tts.isSpeaking())) {
                            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                                tts.speak("보행기에 연결되었습니다",TextToSpeech.QUEUE_FLUSH,null,null);
                            } else {
                                tts.speak("보행기에 연결되었습니다", TextToSpeech.QUEUE_FLUSH, null);
                            }

                        }
                        screen_main_th.interrupt();
                        Intent screen_change = new Intent(getApplicationContext(), Map.class);
                        startActivity(screen_change);
                    }
                }

                if ((topic.equals(WAIT)) && (WALKER_NUM != 0)) {
                    wait = new String(message.getPayload());
                }

                if ((topic.equals(REPOSITION)) && (WALKER_NUM != 0)) {
                    repose = new String(message.getPayload());
                }

                if ((topic.equals(PATH1)) && (WALKER_NUM != 0)) {
                    System.out.println("_________________________________________________________________________");
                    String path1_list = new String(message.getPayload());
                    String A = path1_list.replace("[", "");
                    String B = A.replace("]", "");
                    String C = B.replace(" ", "");
                    String[] D = B.split(Pattern.quote(","));
                    path1 = D;

                }

                if ((topic.equals(PATH2)) && (WALKER_NUM != 0)) {
                    String path1_list = new String(message.getPayload());
                    String A = path1_list.replace("[", "");
                    String B = A.replace("]", "");
                    String C = B.replace(" ", "");
                    String[] D = B.split(Pattern.quote(","));
                    path2 = D;

                }

                if ((topic.equals(POSITION)) && (WALKER_NUM != 0)) {
                    String current_pos = new String(message.getPayload());

                    String[] posxydeg = current_pos.split(Pattern.quote("/"));
                    x = Float.parseFloat(posxydeg[1]);
                    y = Float.parseFloat(posxydeg[2]);
                    //deg = Integer.parseInt(posxydeg[2]);

                }

                if ((topic.equals(ELEVATOR)) && (WALKER_NUM != 0)) {
                    String elev_msg = new String(message.getPayload());

                    String[] elev_arr = elev_msg.split(Pattern.quote("/"));
//                    String A = elev_msg.replace("[", "");
//                    String B = A.replace("]", "");
//                    String[] elev_arr = B.split(Pattern.quote(","));
//                    System.out.println(Arrays.toString(elev_arr));
                    button_stat = Integer.parseInt(elev_arr[0]);

                }

                if ((topic.equals(WALL)) && (WALKER_NUM != 0)) {
                    String msg = new String(message.getPayload());
                    String A = msg.replace("[", "");
                    String B = A.replace("]", "");
                    wall = B.split(Pattern.quote(","));
                }

                if ((topic.equals(NEXT_PATH)) && (WALKER_NUM != 0)) {
                    next_path = new String(message.getPayload());
                }

                if ((topic.equals(OBJECT_POSITION)) && (WALKER_NUM != 0)) {
                    String msg = new String(message.getPayload());

                    String A = msg.replace("[", "");
                    String B = A.replace("]", "");
                    object_position = B.split(Pattern.quote(","));

                    //System.out.println(Arrays.toString(object_position));
                }

                System.out.println(topic);


            }

            @Override
            public void deliveryComplete(IMqttDeliveryToken token) {
            }
        });

        Button test_button = (Button) findViewById(R.id.test_button);
        test_button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                System.out.println("TEST START");
                Intent screen_change = new Intent(getApplicationContext(), Map.class);
//                screen_change.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
                startActivity(screen_change);
            }
        });


//        path1 = new int[][]{{240, 600, 270, 630}, {270, 570, 300, 600}, {270, 540, 300, 570}, {270, 510, 300, 540}, {270, 480, 300, 510}, {270, 450, 300, 480}, {270, 420, 300, 450}, {270, 390, 300, 420}, {300, 360, 330, 390}, {330, 330, 360, 360}, {360, 300, 390, 330}, {390, 270, 420, 300}, {420, 270, 450, 300}, {450, 270, 480, 300}, {480, 270, 510, 300}, {510, 270, 540, 300}, {540, 270, 570, 300}};

    }

    private BaseLoaderCallback mLoaderCallback = new BaseLoaderCallback(this) {
        @Override
        public void onManagerConnected(int status) {
            switch (status) {
                case LoaderCallbackInterface.SUCCESS:
                    Log.i(TAG, "OpenCV loaded successfully");
                    break;
                default:
                    super.onManagerConnected(status);
                    break;
            }
        }
    };

    @Override
    public void onResume() {
        super.onResume();
        if (!OpenCVLoader.initDebug()) {
            Log.d(TAG, "Internal OpenCV library not found. Using OpenCV Manager for initialization");
            OpenCVLoader.initAsync(OpenCVLoader.OPENCV_VERSION, this, mLoaderCallback);
        } else {
            Log.d(TAG, "OpenCV library found inside package. Using it!");
            mLoaderCallback.onManagerConnected(LoaderCallbackInterface.SUCCESS);
            isOpenCvLoaded = true;
        }
    }

    private long time = 0;

    @Override
    public void onBackPressed() {
        if (System.currentTimeMillis() - time >= 2000) {
            time = System.currentTimeMillis();
            Toast.makeText(getApplicationContext(), "뒤로 버튼을 한번 더 누르면 종료합니다.", Toast.LENGTH_SHORT).show();
        } else if (System.currentTimeMillis() - time < 2000) {
            ActivityCompat.finishAffinity(this);
        }
    }

    private void RESPOND_WALKER() {
        try {
            client.subscribe("RESPOND_WALKER", 2);
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    private void POSITION(String pos) {
        try {
            client.subscribe(pos, 1);
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    private void PATH1(String pa1) {
        try {
            client.subscribe(pa1, 1);
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    private void PATH2(String pa2) {
        try {
            client.subscribe(pa2, 1);
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    private void NEXT_PATH(String np) {
        try {
            client.subscribe(np, 1);
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    private void WALL_WARN(String ww) {
        try {
            client.subscribe(ww, 1);
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    private void OBJECT_WARN(String ow) {
        try {
            client.subscribe(ow, 1);
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    private void ELEVATOR(String el) {
        try {
            client.subscribe(el, 2);
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    private void NAVIGATION(String nav) {
        try {
            client.subscribe(nav, 2);
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    private void WAIT(String des) {
        try {
            client.subscribe(des, 1);
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }

    private void REPOSITION(String rep) {
        try {
            client.subscribe(rep, 2);
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }
    @SuppressLint("HardwareIds")
    public String getDeviceId(Context context) {

        String deviceId;

        if (android.os.Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            deviceId = Settings.Secure.getString(
                    context.getContentResolver(),
                    Settings.Secure.ANDROID_ID);
        } else {
            final TelephonyManager mTelephony = (TelephonyManager) context.getSystemService(Context.TELEPHONY_SERVICE);
            if (ActivityCompat.checkSelfPermission(this, Manifest.permission.READ_PHONE_STATE) != PackageManager.PERMISSION_GRANTED) {
                // TODO: Consider calling
                //    ActivityCompat#requestPermissions
                // here to request the missing permissions, and then overriding
                //   public void onRequestPermissionsResult(int requestCode, String[] permissions,
                //                                          int[] grantResults)
                // to handle the case where the user grants the permission. See the documentation
                // for ActivityCompat#requestPermissions for more details.
                return TODO;
            }
            assert mTelephony != null;
            if (mTelephony.getDeviceId() != null) {
                deviceId = mTelephony.getDeviceId();
            } else {
                deviceId = Settings.Secure.getString(
                        context.getContentResolver(),
                        Settings.Secure.ANDROID_ID);
            }
        }

        return deviceId;
    }


    private class SCREEN_CHANGE_TH extends Thread {
        public void run(){
            ImageView start_screen = (ImageView)findViewById(R.id.start_screen);
            while(rotate == 0) {
                start_screen.setImageResource(R.drawable.app_start_1);
                try {
                    Thread.sleep(100);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                start_screen.setImageResource(R.drawable.app_start_2);
                try {
                    Thread.sleep(100);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                start_screen.setImageResource(R.drawable.app_start_3);
                try {
                    Thread.sleep(100);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                start_screen.setImageResource(R.drawable.app_start_4);
                try {
                    Thread.sleep(100);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                start_screen.setImageResource(R.drawable.app_start_5);
                try {
                    Thread.sleep(100);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                start_screen.setImageResource(R.drawable.app_start_6);
                try {
                    Thread.sleep(100);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                start_screen.setImageResource(R.drawable.app_start_7);
                try {
                    Thread.sleep(100);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
                start_screen.setImageResource(R.drawable.app_start_0);
                try {
                    Thread.sleep(100);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }

            }
        }
    }

    private class TOPIC_SUB extends Thread {
        public void run(){
            while(true){
                POSITION(POSITION);

                PATH1(PATH1);

                PATH2(PATH2);

                NEXT_PATH(NEXT_PATH);

                WALL_WARN(WALL);

                OBJECT_WARN(OBJECT_POSITION);

                ELEVATOR(ELEVATOR);

                NAVIGATION(NAVIGATION);

                WAIT(WAIT);

                REPOSITION(REPOSITION);

                try {
                    Thread.sleep(500);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        }
    }



}

