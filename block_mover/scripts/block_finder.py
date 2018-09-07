#!/usr/bin/env python
import rospy
import cv2
import numpy as np

import argparse
import struct
import sys
import copy
import rospkg
import math

from matplotlib import pyplot as plt

from std_msgs.msg import String, Int32
from sensor_msgs.msg import Image, CameraInfo, Range
from geometry_msgs.msg import Pose, PoseArray, Point, Quaternion

from image_geometry import PinholeCameraModel

from visualization_msgs.msg import Marker, MarkerArray

from cv_bridge import CvBridge
import baxter_interface

import tf

TOP_CAM = False
HAND_CAM = True
SIM  = False


TUNE_HSV_VALS = False

if(TOP_CAM):
    BLU_LOW_HUE     = 106
    BLU_HIGH_HUE    = 115
    BLU_LOW_SAT     = 160
    BLU_HIGH_SAT    = 255
    BLU_LOW_VAL     = 127
    BLU_HIGH_VAL    = 255

    GRN_LOW_HUE     = 39
    GRN_HIGH_HUE    = 72
    GRN_LOW_SAT     = 34
    GRN_HIGH_SAT    = 255
    GRN_LOW_VAL     = 85
    GRN_HIGH_VAL    = 255

    TEAL_LOW_HUE     = 90
    TEAL_HIGH_HUE    = 104
    TEAL_LOW_SAT     = 97
    TEAL_HIGH_SAT    = 201
    TEAL_LOW_VAL     = 42
    TEAL_HIGH_VAL    = 255

    RED_LOW_HUE_1     = 0
    RED_HIGH_HUE_1    = 15
    RED_LOW_HUE_2     = 160
    RED_HIGH_HUE_2    = 180
    RED_LOW_SAT     = 0
    RED_HIGH_SAT    = 255
    RED_LOW_VAL     = 0
    RED_HIGH_VAL    = 180

    YEL_LOW_HUE     = 4
    YEL_HIGH_HUE    = 38
    YEL_LOW_SAT     = 83
    YEL_HIGH_SAT    = 255
    YEL_LOW_VAL     = 182
    YEL_HIGH_VAL    = 255

if(HAND_CAM):
    BLU_LOW_HUE     = 100
    BLU_HIGH_HUE    = 133
    BLU_LOW_SAT     = 117
    BLU_HIGH_SAT    = 255
    BLU_LOW_VAL     = 28
    BLU_HIGH_VAL    = 255

    GRN_LOW_HUE     = 37
    GRN_HIGH_HUE    = 104
    GRN_LOW_SAT     = 60
    GRN_HIGH_SAT    = 199
    GRN_LOW_VAL     = 10
    GRN_HIGH_VAL    = 255

    TEAL_LOW_HUE     = 90
    TEAL_HIGH_HUE    = 104
    TEAL_LOW_SAT     = 97
    TEAL_HIGH_SAT    = 201
    TEAL_LOW_VAL     = 42
    TEAL_HIGH_VAL    = 255

    RED_LOW_HUE_1     = 0
    RED_HIGH_HUE_1    = 10
    RED_LOW_HUE_2     = 160
    RED_HIGH_HUE_2    = 180
    RED_LOW_SAT     = 5
    RED_HIGH_SAT    = 255
    RED_LOW_VAL     = 20
    RED_HIGH_VAL    = 255

    YEL_LOW_HUE     = 10
    YEL_HIGH_HUE    = 70
    YEL_LOW_SAT     = 33
    YEL_HIGH_SAT    = 255
    YEL_LOW_VAL     = 182
    YEL_HIGH_VAL    = 255


if(SIM):
    BLU_LOW_HUE     = 90
    BLU_HIGH_HUE    = 130
    BLU_LOW_SAT     = 0
    BLU_HIGH_SAT    = 255
    BLU_LOW_VAL     = 0
    BLU_HIGH_VAL    = 255

    GRN_LOW_HUE     = 30
    GRN_HIGH_HUE    = 80
    GRN_LOW_SAT     = 0
    GRN_HIGH_SAT    = 255
    GRN_LOW_VAL     = 0
    GRN_HIGH_VAL    = 255
    
    TEAL_LOW_HUE     = 80
    TEAL_HIGH_HUE    = 105
    TEAL_LOW_SAT     = 0
    TEAL_HIGH_SAT    = 255
    TEAL_LOW_VAL     = 0
    TEAL_HIGH_VAL    = 100

    RED_LOW_HUE_1     = 0
    RED_HIGH_HUE_1    = 10
    RED_LOW_HUE_2     = 175
    RED_HIGH_HUE_2    = 180
    RED_LOW_SAT     = 100
    RED_HIGH_SAT    = 255
    RED_LOW_VAL     = 140
    RED_HIGH_VAL    = 255

    YEL_LOW_HUE     = 1
    YEL_HIGH_HUE    = 30
    YEL_LOW_SAT     = 180
    YEL_HIGH_SAT    = 255
    YEL_LOW_VAL     = 0
    YEL_HIGH_VAL    = 255



colors = {
        "red":      {   "low_h": [RED_LOW_HUE_1, RED_LOW_HUE_2],   "high_h": [RED_HIGH_HUE_1, RED_HIGH_HUE_2],
                        "low_s": RED_LOW_SAT,   "high_s": RED_HIGH_SAT,
                        "low_v": RED_LOW_VAL,   "high_v": RED_HIGH_VAL  },
        #"yellow":   {   "low_h": YEL_LOW_HUE,   "high_h": YEL_HIGH_HUE,
        #                "low_s": YEL_LOW_SAT,   "high_s": YEL_HIGH_SAT,
        #                "low_v": YEL_LOW_VAL,   "high_v": YEL_HIGH_VAL  },
        "green":    {   "low_h": GRN_LOW_HUE,   "high_h": GRN_HIGH_HUE,
                        "low_s": GRN_LOW_SAT,   "high_s": GRN_HIGH_SAT,
                        "low_v": GRN_LOW_VAL,   "high_v": GRN_HIGH_VAL  },
        "blue":     {   "low_h": BLU_LOW_HUE,   "high_h": BLU_HIGH_HUE,
                        "low_s": BLU_LOW_SAT,   "high_s": BLU_HIGH_SAT,
                        "low_v": BLU_LOW_VAL,   "high_v": BLU_HIGH_VAL  },
        #"teal":     {   "low_h": TEAL_LOW_HUE,  "high_h": TEAL_HIGH_HUE,
        #                "low_s": TEAL_LOW_SAT,  "high_s": TEAL_HIGH_SAT,
        #                "low_v": TEAL_LOW_VAL,  "high_v": TEAL_HIGH_VAL  }
}

color_vals = {
    "red":    (0, 0, 255),
    "green":  (0, 255, 0),
    "blue":   (255, 0, 0),
    "yellow": (0, 255, 255),
    "teal":   (255, 60, 0)
}


# From https://github.com/botforge/ColorTrackbar
def nothing(x):
    pass

# From https://github.com/botforge/ColorTrackbar
def find_hsv_values(img):
    # optional argument for trackbars

    # named ites for easy reference
    barsWindow = 'Bars'
    hl = 'H Low'
    hh = 'H High'
    sl = 'S Low'
    sh = 'S High'
    vl = 'V Low'
    vh = 'V High'

    # set up for video capture on camera 0

    # create window for the slidebars
    cv2.namedWindow(barsWindow, flags = cv2.WINDOW_AUTOSIZE)

    # create the sliders
    cv2.createTrackbar(hl, barsWindow, 0, 179, nothing)
    cv2.createTrackbar(hh, barsWindow, 0, 179, nothing)
    cv2.createTrackbar(sl, barsWindow, 0, 255, nothing)
    cv2.createTrackbar(sh, barsWindow, 0, 255, nothing)
    cv2.createTrackbar(vl, barsWindow, 0, 255, nothing)
    cv2.createTrackbar(vh, barsWindow, 0, 255, nothing)

    # set initial values for sliders
    cv2.setTrackbarPos(hl, barsWindow, 0)
    cv2.setTrackbarPos(hh, barsWindow, 179)
    cv2.setTrackbarPos(sl, barsWindow, 0)
    cv2.setTrackbarPos(sh, barsWindow, 255)
    cv2.setTrackbarPos(vl, barsWindow, 0)
    cv2.setTrackbarPos(vh, barsWindow, 255)

    while(True):
        frame = img
        frame = cv2.GaussianBlur(frame, (5, 5), 0)
        
        # convert to HSV from BGR
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # read trackbar positions for all
        hul = cv2.getTrackbarPos(hl, barsWindow)
        huh = cv2.getTrackbarPos(hh, barsWindow)
        sal = cv2.getTrackbarPos(sl, barsWindow)
        sah = cv2.getTrackbarPos(sh, barsWindow)
        val = cv2.getTrackbarPos(vl, barsWindow)
        vah = cv2.getTrackbarPos(vh, barsWindow)

        # make array for final values
        HSVLOW = np.array([hul, sal, val])
        HSVHIGH = np.array([huh, sah, vah])

        # apply the range on a mask
        mask = cv2.inRange(hsv, HSVLOW, HSVHIGH)
        maskedFrame = cv2.bitwise_and(frame, frame, mask = mask)

        # display the camera and masked images
        cv2.imshow('Masked', maskedFrame)
        cv2.imshow('Camera', frame)

        # check for q to quit program with 5ms delay
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    # clean up our resources
    cap.release()
    cv.destroyAllWindows()

class BlockFinder():
    def __init__(self, limb):
        self.limb = limb

        self.block_poses = []
        self.markers = MarkerArray()
        self.ray_markers = MarkerArray()
        self.tf_listener = tf.TransformListener()
        self.top_camera_model = None
        self.hand_camera_model = None
        self.min_ir_depth = 0.1
        self.object_height = 0.1
        self.bridge = CvBridge()
        self.ir_reading = None

        self.pub_rate = rospy.Rate(1)
        self.seg_img = {
            "red": np.zeros((800,800,3), dtype=np.uint8),
            "yellow": np.zeros((800,800,3), dtype=np.uint8),
            "green": np.zeros((800,800,3), dtype=np.uint8),
            "blue": np.zeros((800,800,3), dtype=np.uint8),
            }
        self.rect_seg_img = np.zeros((800,800,3), dtype=np.uint8)

        self.pixel_loc = None

        # TODO: Tune!
        self.top_cam_table_dist = 1.33

    def publish(self):
        self.pose_pub           = rospy.Publisher("block_finder/" + self.limb + "/block_poses", PoseArray, queue_size=1)
        #self.block_xy_pub             = rospy.Publisher("block_finder/" + self.limb + "/block_xy", Point, queue_size=1)
        self.red_seg_img_pub    = rospy.Publisher("block_finder/" + self.limb + "/red_segmented_image", Image, queue_size=1)
        self.yellow_seg_img_pub = rospy.Publisher("block_finder/" + self.limb + "/yellow_segmented_image", Image, queue_size=1)
        self.blue_seg_img_pub   = rospy.Publisher("block_finder/" + self.limb + "/blue_segmented_image", Image, queue_size=1)
        self.green_seg_img_pub  = rospy.Publisher("block_finder/" + self.limb + "/green_segmented_image", Image, queue_size=1)
        self.rect_seg_img_pub   = rospy.Publisher("block_finder/" + self.limb + "/rect_segmented_image", Image, queue_size=1)
        self.marker_pub         = rospy.Publisher("block_finder/" + self.limb + "/block_markers", MarkerArray, queue_size=1)
        self.ray_marker_pub     = rospy.Publisher("block_finder/image_rays", MarkerArray, queue_size=20)

    def subscribe(self):
        # The camera in left or right hand
        self.hand_cam_sub   = rospy.Subscriber("/cameras/" + self.limb + "_camera/image", Image, self.hand_cam_callback)

        # The camera above the table
        #self.top_cam_sub    = rospy.Subscriber("/camera/rgb/image_rect_color", Image, self.top_cam_callback)
        self.hand_cam_info_sub       = rospy.Subscriber("/cameras/" + self.limb + "_camera/camera_info_std", CameraInfo, self.hand_cam_info_callback)
        #self.top_cam_info_sub       = rospy.Subscriber("/camera/rgb/camera_info", CameraInfo, self.top_cam_info_callback)
        self.ir_sub         = rospy.Subscriber("/robot/range/" + self.limb + "_range/state", Range, self.ir_callback)
        

    def hand_cam_callback(self, data):
        cv_image = self.bridge.imgmsg_to_cv2(data)

        self.find_blocks(cv_image, camera_name="right_hand")
    
    def top_cam_callback(self, data):
        cv_image = self.bridge.imgmsg_to_cv2(data)

        self.find_blocks(cv_image, camera_name="top")

    '''
    Thresholds camera image and stores object centroid location (x,y) in Baxter's base frame.
    '''
    def find_blocks(self, cv_image, camera_name):
        block_pose_list = []
        block_marker_list = MarkerArray()
        ray_marker_list = MarkerArray()
        
        # Mask cv_image to remove baxter's grippers

        if(TUNE_HSV_VALS):
            find_hsv_values(cv_image)

        height, width, depth = cv_image.shape
        low_s = 0
        low_v = 0

        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)

        images = [hsv, hsv, hsv, hsv, hsv]
        i = 0
        ray_id = 0

        # Find table

        for color in colors:
            low_h = colors[color]["low_h"]
            high_h = colors[color]["high_h"]
            low_s = colors[color]["low_s"]
            high_s = colors[color]["high_s"]
            low_v = colors[color]["low_v"]
            high_v = colors[color]["high_v"]

            #Converting image to HSV format
            if color == "red":
                hsv_mask_1 = cv2.inRange(hsv, np.array([low_h[0], low_s, low_v]), np.array([high_h[0], high_s, high_v]))
                hsv_mask_2 = cv2.inRange(hsv, np.array([low_h[1], low_s, low_v]), np.array([high_h[1], high_s, high_v]))

                hsv_mask = hsv_mask_1 | hsv_mask_2


            else:
                hsv_mask = cv2.inRange(hsv, np.array([low_h, low_s, low_v]), np.array([high_h, high_s, high_v]))

            # Apply mask to original image
            masked_img = cv2.bitwise_and(cv_image, cv_image, mask=hsv_mask)

            # Store HSV masked image for the current color
            self.seg_img[color] = masked_img.copy()
            #cv2.imshow(color, masked_img)

            #Morphological opening (remove small objects from the foreground)
            erode_1 = cv2.erode(hsv_mask, np.ones((5,5), np.uint8), iterations=1)
            dilate_1 = cv2.dilate(erode_1, np.ones((5,5), np.uint8), iterations=1)

            #Morphological closing (fill small holes in the foreground)
            dilate_2 = cv2.dilate(dilate_1, np.ones((10,10), np.uint8), iterations=1)
            erode_2 = cv2.erode(dilate_2, np.ones((10,10), np.uint8), iterations=1)

            images[i] = erode_2.copy()
            
            ret, thresh = cv2.threshold(erode_2,157,255,0)

            contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)

            #Draw the countours.
            #cv2.drawContours(cv_image, contours, -1, (0,255,0), 3)
            
            num_obj = len(contours) # number of objects found in current frame

            for contour in contours:
                area = cv2.contourArea(contour)
                
                if(area*self.ir_reading > 180):
                    
                    rospy.loginfo("AREA: %f", area)
                    rect = cv2.minAreaRect(contour)
                    print(rect[1][0])
                    print(rect[1][1])
                    box = cv2.cv.BoxPoints(rect)
                    box = np.int0(box)
                    cv2.drawContours(cv_image, [box], 0, color_vals[color] , 2)


                    x, y, w, h = cv2.boundingRect(contour)
                    cropped_img = masked_img[y-5:y+h+5, x-5:x+w+5]

                    block_angle = calc_angle(cropped_img)
                    block_ratio = calc_ratio(box[1][1], box[1][0])

                    block_type = calc_block_type(block_ratio)

                    moms = cv2.moments(contour)

                    if moms['m00']*self.ir_reading > 180:
                        cx = int(moms['m10']/moms['m00'])
                        cy = int(moms['m01']/moms['m00'])

                        print 'cx = ', cx
                        print 'cy = ', cy

                        #cx = cx - self.camera_model.cx()
                        #cy = cy - self.camera_model.cy()

                        cv2.circle(cv_image,(cx,cy), 10, color_vals[color], 1)

                        # Write the block tshape
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        cv2.putText(cv_image,block_type,(cx,cy), font, 4,(255,255,255),2)

                        self.pixel_loc = [cx, cy]
                        


                        rospy.loginfo("Found %d %s objects", num_obj, color)
                        obj_found = True
                        if(camera_name == "right_hand"):
                            vec = np.array(self.hand_camera_model.projectPixelTo3dRay((cx, cy)))
                        elif(camera_name == "top"):
                            vec = np.array(self.top_camera_model.projectPixelTo3dRay((cx, cy)))
                        else:
                            # Invalid camera name
                            rospy.loginfo("The camera name you passed to find blocks is invalid!")
                            return


                        if(self.ir_reading != None):
                            rospy.loginfo("IR reading is: %f", self.ir_reading)
                            if(camera_name =="right_hand"):
                                d = self.ir_reading + 0.15
                            elif(camera_name =="top"):
                                d = self.top_cam_table_dist
                            #d = 0.55

                            ray_pt_1 = 0 * vec
                            ray_pt_2 = 2 * vec


                            #d = (self.ir_reading - self.object_height)
                            norm_vec = np.array([0, 0, 1])

                            rospy.loginfo("Vec: %f, %f, %f", vec[0], vec[1], vec[2])
                            rospy.loginfo("Norm Vec: %f, %f, %f", norm_vec[0], norm_vec[1], norm_vec[2])

                            d_proj = d * np.dot(norm_vec, vec) / (np.linalg.norm(norm_vec) * np.linalg.norm(vec))


                            rospy.loginfo("Distance to object: %f", d)
                            rospy.loginfo("Projected distance to object: %f", d_proj)
                            
                            d_cam = d * vec
                            #d_cam = vec

                            homog_d_cam = np.concatenate((d_cam, np.ones(1))).reshape((4,1))
                            homog_ray_pt_1 = np.concatenate((ray_pt_1, np.ones(1))).reshape((4,1))
                            homog_ray_pt_2 = np.concatenate((ray_pt_2, np.ones(1))).reshape((4,1))

                            # Wait for transformation from base to head_camera
                            self.tf_listener.waitForTransform('/base', self.limb + "_camera", rospy.Time(), rospy.Duration(4))
                            (trans, rot) = self.tf_listener.lookupTransform('/base', self.limb + "_camera", rospy.Time())

                            camera_to_base = tf.transformations.compose_matrix(translate=trans, angles=tf.transformations.euler_from_quaternion(rot))

                            block_position_arr = np.dot(camera_to_base, homog_d_cam)
                            
                            # Transform ray to base frame
                            ray_pt_1_tf = np.dot(camera_to_base, homog_ray_pt_1)
                            ray_pt_2_tf = np.dot(camera_to_base, homog_ray_pt_2)

                            ray_marker_list.markers.append(create_ray_marker(
                                                frame="base", 
                                                id=ray_id,
                                                point1=Point(ray_pt_1_tf[0], ray_pt_1_tf[1], ray_pt_1_tf[2]),
                                                point2=Point(ray_pt_2_tf[0], ray_pt_2_tf[1], ray_pt_2_tf[2]),
                                                ray_color=color
                                            )
                            )
                            ray_id += 1
                            rospy.loginfo("Block position: %f, %f, %f", block_position_arr[0], block_position_arr[1], block_position_arr[2])
                           
                            block_position_p = Point()
                            block_position_arr_copy = block_position_arr.copy()
                            block_position_p.x = block_position_arr_copy[0]
                            block_position_p.y = block_position_arr_copy[1]
                            block_position_p.z = -.1

                            # TODO: Need to calculate this later

                            # Rotation about z-axis by small amount
                            block_orientation_arr = tf.transformations.quaternion_from_euler(0, 0, block_angle)

                            block_orientation = Quaternion()
                            block_orientation.x = block_orientation_arr[0]
                            block_orientation.y = block_orientation_arr[1]
                            block_orientation.z = block_orientation_arr[2]
                            block_orientation.w = block_orientation_arr[3]

                            # Create a marker to visualize in RVIZ 
                            curr_marker = create_block_marker(frame = "base", id = len(block_marker_list.markers), position = block_position_p, orientation=block_orientation, block_type=block_type, block_color = color, transparency = 1)

                            rospy.loginfo("Adding new marker and block pose!")
                            block_marker_list.markers.append(curr_marker)
                            block_pose_list.append(Pose(position=block_position_p, orientation=block_orientation))
                        else:
                            rospy.loginfo("No ir_data has been recieved yet!")
                    else:
                        rospy.loginfo("Moments aren't large enough!")
                else:
                    pass
                    rospy.loginfo("Contour area is not large enough!")
        
        self.rect_seg_img = cv_image.copy()
        self.block_poses = block_pose_list        
        self.ray_markers = ray_marker_list
        self.block_markers = block_marker_list
        

    def hand_cam_info_callback(self, data):
        self.hand_camera_model = PinholeCameraModel()
        self.hand_camera_model.fromCameraInfo(data)
        self.hand_cam_info_sub.unregister() # Unsubscribe after receiving CameraInfo first time
    
    def top_cam_info_callback(self, data):
        self.top_camera_model = PinholeCameraModel()
        self.top_camera_model.fromCameraInfo(data)
        self.top_cam_info_sub.unregister() # Unsubscribe after receiving CameraInfo first time

    def ir_callback(self, data):
        self.ir_reading = data.range
        #rospy.loginfo("IR reading: %f", self.ir_reading)
        if(self.ir_reading > 65):
            #rospy.loginfo("Invalid IR reading")
            self.ir_reading = 0.4

def calc_block_type(block_ratio):
    if(block_ratio > 0.5 and block_ratio <= 1.5):
        block_type = "1x1"
    elif(block_ratio > 1.5 and block_ratio <= 2.5):
        block_type = "1x2"
    elif(block_ratio > 2.5 and block_ratio <= 3.5):
        block_type = "1x3"
    elif(block_ratio > 3.5 and block_ratio <= 4.5):
        block_type = "1x4"
    else:
        rospy.loginfo("BLOCK RATIO is %f", block_ratio)
        block_type = "None"

    return block_type
def generate_gripper_mask(hand_cam_image):
    pass

def calc_ratio(height, width):
    #rospy.loginfo("Height: %d, Width: %d", h, w)
    if(height > width):
        temp = height
        height = width
        width = temp

    rospy.loginfo("Height: %d, Width: %d", height, width)

    ratio = width / height

    return ratio


def calc_angle(cropped_image):
    # PCA
    pca_img = cropped_image.copy()
    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    #From a matrix of pixels to a matrix of coordinates of non-black points.
    #(note: mind the col/row order, pixels are accessed as [row, col]
    #but when we draw, it's (x, y), so have to swap here or there)
    mat = []
    for col in range(w):
        for row in range(h):
            if gray[row, col] > 0:
                mat.append([col, row])

    mat = np.array(mat).astype(np.float32) #have to convert type for PCA

    #mean (e. g. the geometrical center)
    #and eigenvectors (e. g. directions of principal components)
    m, e = cv2.PCACompute(mat, mean = None)

    #now to draw: let's scale our primary axis by 100,
    #and the secondary by 50
    center = tuple(m[0])
    endpoint1 = tuple(m[0] + e[0]*100)
    endpoint2 = tuple(m[0] + e[1]*50)
    
    """
    cv2.circle(pca_img, center, 5, 255)
    # Major Axis
    cv2.line(pca_img, center, endpoint1, 255, 4)

    # Minor Axis
    cv2.line(pca_img, center, endpoint2, 255, 4)

    plt.imshow(pca_img)
    plt.show()
    """

    # Calculate angle of major axis
    major_x = endpoint1[0] - center[0]
    major_y = endpoint1[1] - center[1]
    minor_x = endpoint2[0] - center[0]
    minor_y = endpoint2[1] - center[1]

    angle_rad_major = math.atan2(major_y, major_x)

    return angle_rad_major

def calc_center_angle_old(cont, cv_img):
    
    #img_shape = cv_img.shape

    #blank_img = np.zeros(img_shape, dtype=np.uint8)

    #cont_img = cv2.drawContours(cv_img, cont, 0, (0, 0, 255), 2)

    gray_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray_img, 50, 100, apertureSize = 3)


    #cv2.imshow("gray", gray_img)
    # TODO: optimize this by only performing operation on subsection of image
    lines = cv2.HoughLinesP(edges, rho=1, theta=0.017, threshold=30, minLineLength=2, maxLineGap=5) # From https://github.com/osrf/baxter_demos/blob/master/config/object_finder.yaml

    if lines is None:
        rospy.loginfo( "No lines found" )
        return None

    lines = lines.reshape(lines.shape[1], lines.shape[2])

    # Calculate the lengths of each line
    lengths = np.square(lines[:, 0]-lines[:, 2]) +\
            np.square(lines[:, 1]-lines[:, 3])
    lines = np.hstack((lines, lengths.reshape((lengths.shape[0], 1)) ))
    lines = lines[lines[:,4].argsort()]
    lines = lines[::-1] #Reverse the sorted array
    lines = lines[:, 0:4]

    longest_line = lines[0] #Get the longest line

    angle = math.atan2(longest_line[1] - longest_line[3], longest_line[0] - longest_line[2])

    rospy.loginfo("Angle: %f", angle * 180 / math.pi)


def create_block_marker(frame, id, position, orientation, block_type, block_color, transparency):
    curr_marker = Marker()
    curr_marker.header.frame_id = frame
    
    curr_marker.type = 1 # sphere
    curr_marker.action = 0
    curr_marker.id = id
    curr_marker.frame_locked = True
    curr_marker.pose.position = position
    curr_marker.pose.orientation = orientation
   
    single_unit_dim = 0.03

    if(block_type == "1x1"):
        curr_marker.scale.x = single_unit_dim
        curr_marker.scale.y = single_unit_dim
        curr_marker.scale.z = single_unit_dim
    elif(block_type == "1x2"):
        curr_marker.scale.x = single_unit_dim
        curr_marker.scale.y = 2*single_unit_dim 
        curr_marker.scale.z = single_unit_dim 
    elif(block_type == "1x3"):
        curr_marker.scale.x = single_unit_dim 
        curr_marker.scale.y = 3 *single_unit_dim
        curr_marker.scale.z = single_unit_dim
    elif(block_type == "1x4"):
        curr_marker.scale.x = single_unit_dim 
        curr_marker.scale.y = 4 *single_unit_dim
        curr_marker.scale.z = single_unit_dim

    else:
        rospy.logerror("%s is not a supported block type. The only supported block types are 2x1, 1x2, and 1x3", block_type)


    if(block_color == "red"):
        curr_marker.color.r = 1.0
        curr_marker.color.g = 0.0
        curr_marker.color.b = 0.0
    elif(block_color == "blue"):
        curr_marker.color.r = 0.0
        curr_marker.color.g = 0.0
        curr_marker.color.b = 1.0
    elif(block_color == "green"):
        curr_marker.color.r = 0.0
        curr_marker.color.g = 1.0
        curr_marker.color.b = 0.0
    elif(block_color == "yellow"):
        curr_marker.color.r = 1.0
        curr_marker.color.g = 1.0
        curr_marker.color.b = 0.0
    elif(block_color == "teal"):
        curr_marker.color.r = 0.0
        curr_marker.color.g = 0.2
        curr_marker.color.b = 1.0
    else:
        rospy.logerr("Color %s doesn't have a supported marker yet! you should add one.", color)
    
    # Alpha value (transparency)
    curr_marker.color.a = transparency

    curr_marker.lifetime = rospy.Duration(0)

    return curr_marker


def create_ray_marker(frame, id, point1, point2, ray_color):
    curr_marker = Marker()
    curr_marker.header.frame_id = frame
    
    curr_marker.type = 5 # line list
    curr_marker.action = 0
    curr_marker.id = id
    curr_marker.frame_locked = True
    #curr_marker.pose.position = position
    #curr_marker.pose.orientation = orientation

    if(ray_color == "red"):
        curr_marker.color.r = 1.0
        curr_marker.color.g = 0.0
        curr_marker.color.b = 0.0
    elif(ray_color == "blue"):
        curr_marker.color.r = 0.0
        curr_marker.color.g = 0.0
        curr_marker.color.b = 1.0
    elif(ray_color == "green"):
        curr_marker.color.r = 0.0
        curr_marker.color.g = 1.0
        curr_marker.color.b = 0.0
    elif(ray_color == "yellow"):
        curr_marker.color.r = 1.0
        curr_marker.color.g = 1.0
        curr_marker.color.b = 0.0
    elif(ray_color == "teal"):
        curr_marker.color.r = 0.0
        curr_marker.color.g = 0.2
        curr_marker.color.b = 1.0
    else:
        rospy.logerr("Color %s doesn't have a supported marker yet! you should add one.", color)
    curr_marker.scale.x = .01

    points_list = []
    #point1 = Point(x = 0, y = 0, z = 0)
    #point1 = Point(x = 0, y = 1, z = 0)

    position = Point(x = 0, y = 0, z = 0)
    orientation = Quaternion(w = 0, x = 0, y = 0, z = 0)

    curr_marker.pose.position = position
    curr_marker.pose.orientation = orientation


    points_list.append(point1)
    points_list.append(point2)
    curr_marker.points = points_list
    
    # Alpha value (transparency)
    curr_marker.color.a = 1

    curr_marker.lifetime = rospy.Duration(0)

    return curr_marker


def main():
    rospy.init_node('block_finder')

    block_finder = BlockFinder("right_hand")
    block_finder.subscribe()
    block_finder.publish()

    while not rospy.is_shutdown():
        print(block_finder.block_poses)

        if(len(block_finder.block_poses) > 0):
            rospy.loginfo("Publishing block location and pixel location")
            pose_msg = PoseArray()
            pose_msg.poses = block_finder.block_poses
            block_finder.pose_pub.publish(pose_msg)
            block_finder.marker_pub.publish(block_finder.block_markers)
            rospy.loginfo("There are %d block markers", len(block_finder.block_markers.markers))

            # Publish the camera x,y coordinate location of the block
            #block_finder.block_xy_pub.publish(block_finder.pixel_loc)

            # Publish ray that intersects with camera and object
            block_finder.ray_marker_pub.publish(block_finder.ray_markers)
            rospy.loginfo("There are %d ray markers", len(block_finder.ray_markers.markers))
    
        block_finder.rect_seg_img_pub.publish(block_finder.bridge.cv2_to_imgmsg(block_finder.rect_seg_img))
        block_finder.red_seg_img_pub.publish(block_finder.bridge.cv2_to_imgmsg(block_finder.seg_img["red"]))
        block_finder.green_seg_img_pub.publish(block_finder.bridge.cv2_to_imgmsg(block_finder.seg_img["green"]))
        block_finder.yellow_seg_img_pub.publish(block_finder.bridge.cv2_to_imgmsg(block_finder.seg_img["yellow"]))
        block_finder.blue_seg_img_pub.publish(block_finder.bridge.cv2_to_imgmsg(block_finder.seg_img["blue"]))
#
        

        # Sleep
        block_finder.pub_rate.sleep()

    return 

if __name__ == '__main__':
     main()