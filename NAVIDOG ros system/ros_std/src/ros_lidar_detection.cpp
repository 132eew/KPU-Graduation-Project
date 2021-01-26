#include "ros/ros.h"
#include <stdio.h>
#include <math.h>
#include <cstdio>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <list>
#include <tf/transform_datatypes.h>
#include <std_msgs/String.h>
#include "geometry_msgs/PoseWithCovarianceStamped.h"
#include "sensor_msgs/LaserScan.h"

#define PI 3.14159265358979323846
#define RAD2DEG(x) ((x)*180./3.14159265358979323846)
using namespace std;

int cnt = 1;
int pin = 0;
list<int> obj_deg;
list<float> obj_rng;
string pub = "o";
void scan_callback(const sensor_msgs::LaserScan::ConstPtr& scan)
{
    	int count = scan->scan_time / scan->time_increment;
    	string obj("");
    	obj.reserve(128);

    	for(int i = 0; i < count; i++) {
        	float degree = RAD2DEG(scan->angle_min + scan->angle_increment * i);

		    if((degree >= -60)&&(degree <= 60)){
			    if(((scan->ranges[i]) > 3)&&((scan->ranges[i]) < 4)){//////////set-distanse//////////////
                    if(cnt==1){
                        obj_deg.push_back(degree);
                        obj_rng.push_back(scan->ranges[i]);
                        pin = 1;
                    }
			    }
		    }
    	}
	    cnt++;
    	if((cnt == 2)&&(pin==1)){

            ROS_INFO("SEARCH END");
			
	        cnt = 1;
	        pin = 0;
            int cut_st = 0;
            int cut_ed = 0;
            double temp = 0;
            int object_individual_index = 0;
            string object_individual("");
            string object_individual_topic("");
	        int obj_deg_arr[obj_deg.size()];
	        float obj_rng_arr[obj_rng.size()];
	        float object_len_left = 0;
	        float object_len_right = 0;
	        int object_deg_left = 0;
	        int object_deg_right = 0;
	        int st = 0;
	        for(int const &put_deg: obj_deg){
                obj_deg_arr[st++] = put_deg;
            } 
	        st = 0;
	        for(float const &put_rng: obj_rng){
                obj_rng_arr[st++] = put_rng;
            }
            st = 0;
            for(st=0;st<(sizeof(obj_deg_arr)/sizeof(*obj_deg_arr))-1;st++){
                int comp_deg = abs(obj_deg_arr[st+1]-obj_deg_arr[st]);
                float comp_rng = fabs(obj_rng_arr[st+1]-obj_rng_arr[st]);

                if((comp_deg>2.2)||(comp_rng>0.15)){//////////////////////deg//////range//left 15cm, back 15cm
                    cut_ed = st;

                    if((cut_st == 0)&&(comp_deg<=2.2)){
                        object_len_left = obj_rng_arr[cut_st];
                        object_len_right = obj_rng_arr[cut_ed];
                        object_deg_left = obj_deg_arr[cut_st];
                        object_deg_right = obj_deg_arr[cut_ed];
                    }
                    else{
                        object_len_left = obj_rng_arr[cut_st+1];
                        object_len_right = obj_rng_arr[cut_ed];
                        object_deg_left = obj_deg_arr[cut_st+1];
                        object_deg_right = obj_deg_arr[cut_ed];
                    }
                    
                    if((cut_ed - cut_st)>=4){///////////////////////////////////////////
                        int nearest_index = cut_st + 1;
                        temp = obj_rng_arr[nearest_index];

                        for(nearest_index;nearest_index<=cut_ed;nearest_index++){
                            if(obj_rng_arr[nearest_index]<=temp){
                                temp = obj_rng_arr[nearest_index];
                                object_individual_index = nearest_index;
                            }
                        }

                        object_individual_topic.reserve(128);
                        sprintf(&object_individual_topic[0],"/%d/%.4f/%d/%.4f/%d/%.4f|",obj_deg_arr[object_individual_index],\
                        obj_rng_arr[object_individual_index],object_deg_left,object_len_left,object_deg_right,object_len_right);
                        object_individual.append(object_individual_topic.c_str());

                    }cut_st = cut_ed;
                }
            }
            int remain = cut_st+1;
            int last = (sizeof(obj_deg_arr)/sizeof(*obj_deg_arr))-1;

            if((last-remain)>=4){/////////////////////////////////////////////////
                cut_st = remain;
                for(st=remain;st<last;st++){
                    int comp_deg = abs(obj_deg_arr[st+1]-obj_deg_arr[st]);
                    float comp_rng = fabs(obj_rng_arr[st+1]-obj_rng_arr[st]);

                    if((comp_deg>2.2)||(comp_rng>0.15)){//////////////////////deg//////rangea//left 15cm, back 15cm
                        cut_ed = st;

                            object_len_left = obj_rng_arr[cut_st+1];
                            object_len_right = obj_rng_arr[cut_ed];
                            object_deg_left = obj_deg_arr[cut_st+1];
                            object_deg_right = obj_deg_arr[cut_ed];
                        
                        if((cut_ed - cut_st)>=3){
                            int nearest_index = cut_st + 1;
                            temp = obj_rng_arr[nearest_index];

                            for(nearest_index;nearest_index<=cut_ed;nearest_index++){
                                if(obj_rng_arr[nearest_index]<=temp){
                                    temp = obj_rng_arr[nearest_index];
                                    object_individual_index = nearest_index;
                                }
                            }
                            object_individual_topic.reserve(128);
                            sprintf(&object_individual_topic[0],"/%d/%.4f/%d/%.4f/%d/%.4f|",obj_deg_arr[object_individual_index],\
                            obj_rng_arr[object_individual_index],object_deg_left,object_len_left,object_deg_right,object_len_right);
                            object_individual.append(object_individual_topic.c_str());
                
                        }
               
                    }
                }
            }
			if (object_individual.size() != 0){
				pub = object_individual.c_str();
			}
			
	        obj_rng.clear();
    	    obj_deg.clear();
    	}
    	if(cnt>2){
    	    cnt = 0;
    	    obj_rng.clear();
    	    obj_deg.clear();
    	} 
}


int main(int argc, char **argv){

	ros::init(argc, argv, "ros_ridar_detection");
	ros::NodeHandle nh;
    ros::Publisher object_pub = nh.advertise<std_msgs::String>("OBJECT", 1000);
    ros::Subscriber object_sub = nh.subscribe("/slamware_ros_sdk_server_node/scan", 1, scan_callback);
    ros::Rate loop_rate(1);
    ros::spinOnce();
    ROS_INFO("SCAN DETECTION START");
	while (ros::ok())
	{
		if(pub.size() != 1){
			std_msgs::String object_pub_string;
			object_pub_string.data = pub;
			ROS_INFO("%s", object_pub_string.data.c_str());
			object_pub.publish(object_pub_string);
			pub = "o";
	        loop_rate.sleep();
		}
       
        ros::spinOnce();		
	}
	return 0;
}

