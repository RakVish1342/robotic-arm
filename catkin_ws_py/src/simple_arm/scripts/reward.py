#!/usr/bin/env python

import cv2
from geometry_msgs.msg import Pose # Same as Twist, Pose, Odom, Imu: https://answers.ros.org/question/216482/are-odom-pose-twist-and-imu-processed-differently-in-robot_localization/
import math
import rospy
from std_msgs.msg import Float64
from simple_arm.srv import *


class Reward(object):
    def __init__(self):
        rospy.init_node('box_location')
        print(">> Reward node initialized")

        self.subBoxLoc = rospy.Subscriber("/simple_arm/box_location", Pose, self.cbReward)
        self.pubReward = rospy.Publisher('/simple_arm/reward', Float64, queue_size=10)
        self.imgSize = (480, 640)
        self.center = (640/2, 480/2)
        self.goalThresh = 0.1
        # self.normalization = (480*480 + 640*640)**0.5
        self.normalization = 640 # For a 1-D case

        rospy.spin()

    def distance(self, pt1, pt2):
        # dist = ( (pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2 )**(0.5)
        dist = abs(pt1[0] - pt2[0]) # For 1D case
        return dist

    def cbReward(self, msg):
        try:
            boxLoc = (msg.position.x, msg.position.y)
            dist = self.distance(boxLoc, self.center)
            # print(dist)
            if dist <= self.goalThresh:
                reward = +1
            else:
                reward = - self.distance(boxLoc, self.center) / self.normalization
            msgOut = reward

            self.pubReward.publish(msgOut)

        except rospy.ServiceException, e:
            rospy.logwarn("Reward service failed: %s", e)


if __name__ == '__main__':
    try: 
        Reward()
    except rospy.ROSInterruptException:
        pass
