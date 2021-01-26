from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import matplotlib; matplotlib.use('Agg')
import numpy as np
import PIL.Image as Image
import PIL.ImageColor as ImageColor
import PIL.ImageDraw as ImageDraw
import PIL.ImageFont as ImageFont
import six
from six.moves import range
from six.moves import zip
import cv2 as cv
import math as mt

_TITLE_LEFT_MARGIN = 10
_TITLE_TOP_MARGIN = 10
STANDARD_COLORS = [
    'AliceBlue', 'Chartreuse', 'Aqua', 'Aquamarine', 'Azure', 'Beige', 'Bisque',
    'BlanchedAlmond', 'BlueViolet', 'BurlyWood', 'CadetBlue', 'AntiqueWhite',
    'Chocolate', 'Coral', 'CornflowerBlue', 'Cornsilk', 'Crimson', 'Cyan',
    'DarkCyan', 'DarkGoldenRod', 'DarkGrey', 'DarkKhaki', 'DarkOrange',
    'DarkOrchid', 'DarkSalmon', 'DarkSeaGreen', 'DarkTurquoise', 'DarkViolet',
    'DeepPink', 'DeepSkyBlue', 'DodgerBlue', 'FireBrick', 'FloralWhite',
    'ForestGreen', 'Fuchsia', 'Gainsboro', 'GhostWhite', 'Gold', 'GoldenRod',
    'Salmon', 'Tan', 'HoneyDew', 'HotPink', 'IndianRed', 'Ivory', 'Khaki',
    'Lavender', 'LavenderBlush', 'LawnGreen', 'LemonChiffon', 'LightBlue',
    'LightCoral', 'LightCyan', 'LightGoldenRodYellow', 'LightGray', 'LightGrey',
    'LightGreen', 'LightPink', 'LightSalmon', 'LightSeaGreen', 'LightSkyBlue',
    'LightSlateGray', 'LightSlateGrey', 'LightSteelBlue', 'LightYellow', 'Lime',
    'LimeGreen', 'Linen', 'Magenta', 'MediumAquaMarine', 'MediumOrchid',
    'MediumPurple', 'MediumSeaGreen', 'MediumSlateBlue', 'MediumSpringGreen',
    'MediumTurquoise', 'MediumVioletRed', 'MintCream', 'MistyRose', 'Moccasin',
    'NavajoWhite', 'OldLace', 'Olive', 'OliveDrab', 'Orange', 'OrangeRed',
    'Orchid', 'PaleGoldenRod', 'PaleGreen', 'PaleTurquoise', 'PaleVioletRed',
    'PapayaWhip', 'PeachPuff', 'Peru', 'Pink', 'Plum', 'PowderBlue', 'Purple',
    'Red', 'RosyBrown', 'RoyalBlue', 'SaddleBrown', 'Green', 'SandyBrown',
    'SeaGreen', 'SeaShell', 'Sienna', 'Silver', 'SkyBlue', 'SlateBlue',
    'SlateGray', 'SlateGrey', 'Snow', 'SpringGreen', 'SteelBlue', 'GreenYellow',
    'Teal', 'Thistle', 'Tomato', 'Turquoise', 'Violet', 'Wheat', 'White',
    'WhiteSmoke', 'Yellow', 'YellowGreen'
]

text_coding = {1: '1',  2: '2',  3: '<',  4: '>',  5: '3', 6: '!',
                7: '4',  8: 'blur',  9: '5',  10: 'hazy', 11: '6', 12: '7',
                13: '8', 14: 'special', 15: '0', 16: 'alarm', 17: '9', 18: 'G',
                19: 'B', 20: 'up', 21: 'down', 22: 'call', 23: 'L', 24: 'star',
                25: 'P', 26: '-', 27: 'M', 28: 'stop', 29: 'U', 30: 'D',
                31: 'R', 32: 'A', 33: 'C', 34: 'S', 35: 'E', 36: 'F',
                37: 'O', 38: 'K', 39: 'H', 40: 'N', 41: 'T', 42: 'V',
                43: 'I', 44: 'Z', 45: 'J', 46: 'X', 47: '<null>'}

box_point_eq = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]

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
    image_copy = image.copy()
    button_up = image_copy[round(btu_top):round(btu_bottom),round(btu_left):round(btu_right)]
    button_down = image_copy[round(btd_top):round(btd_bottom),round(btd_left):round(btd_right)]

    button_up_binary = IMAGE_BINARY(button_up)
    button_down_binary = IMAGE_BINARY(button_down)
    up_on_off = image_value_average(button_up_binary)
    print("up" + str(up_on_off))
    down_on_off = image_value_average(button_down_binary)
    print("down" + str(down_on_off))
    return [up_on_off,down_on_off]
    #if up_on_off - down_on_off >= 10: return 2 #down
    #elif up_on_off - down_on_off <= -10: return 1 #up
    #else : return 0 #none

def object_tracking(image,bound_box):
    (left,right,top,bottom) = bound_box
    track_window = (round(left),round(top),round(right - left),round(bottom - top))
    (x,y,w,h) = track_window
    Set = None
    OPENCV_OBJECT_TRACKERS = {
        "csrt": cv.TrackerCSRT_create,
        "kcf": cv.TrackerKCF_create,
        "boosting": cv.TrackerBoosting_create,
        "mil": cv.TrackerMIL_create,
        "tld": cv.TrackerTLD_create,
        "medianflow": cv.TrackerMedianFlow_create,
        "mosse": cv.TrackerMOSSE_create
    }
    tracker = OPENCV_OBJECT_TRACKERS["csrt"]()

    if not(0 in (w,h)) :
        Set = True

    if Set:
        roi = (x,y,w,h)
        tracker.init(image, roi)
        return tracker

def _get_multiplier_for_color_randomness():
  num_colors = len(STANDARD_COLORS)
  prime_candidates = [5, 7, 11, 13, 17]
  prime_candidates = [p for p in prime_candidates if num_colors % p]
  if not prime_candidates:
    return 1

  abs_distance = [np.abs(num_colors / 10. - p) for p in prime_candidates]
  num_candidates = len(abs_distance)
  inds = [i for _, i in sorted(zip(abs_distance, range(num_candidates)))]
  return prime_candidates[inds[0]]

# def BUTTONRECOGNIZE(image,btu_box,btd_box):
#     (btu_left,btu_right,btu_top,btu_bottom) = btu_box
#     (btd_left, btd_right, btd_top, btd_bottom) = btd_box
#
#     image_copy = image.copy()
#
#     # roi = image_copy[round(tl_top)+30 :round(tl_bottom)-30, round(tl_left)+30:round(tl_right)-30]
#     #
#     # h_roi, w_roi, _ = roi.shape
#     #
#     # traffic_red = roi[0:round(h_roi / 2), 0:round(w_roi)]
#     # traffic_green = roi[round(h_roi / 2):round(h_roi), 0:round(w_roi)]
#     # if traffic_red.any() or traffic_green.any():
#     #     red_gray = cv.cvtColor(traffic_red, cv.COLOR_RGB2GRAY)
#     #     green_gray = cv.cvtColor(traffic_green, cv.COLOR_RGB2GRAY)
#     #
#     #     _, red_result = cv.threshold(red_gray, 150, 255, cv.THRESH_BINARY)
#     #     _, green_result = cv.threshold(green_gray, 150, 255, cv.THRESH_BINARY)
#     #
#     #     w_red = len(red_result[0])
#     #     h_red = len(red_result)
#     #     w_green = len(green_result[0])
#     #     h_green = len(green_result)
#     #
#     #     div_sum_red = w_red * h_red
#     #     div_sum_green = w_green * h_green
#     #
#     #     avg_red = []
#     #     avg_green = []
#     #
#     #     for r in range(h_red): avg_red.append(sum(red_result[r]))
#     #     for g in range(h_green): avg_green.append(sum(green_result[g]))
#     #
#     #     red = sum(avg_red) / div_sum_red
#     #     green = sum(avg_green) / div_sum_green
#     #
#     #     if green > red:
#     #         return 0
#     #     else:
#     # return 0  # None
#     return 1#위버튼
#     # return 2  # 아래버튼


def draw_bounding_box_on_image_array(image,
                                     ymin,
                                     xmin,
                                     ymax,
                                     xmax,
                                     obj_num,
                                     color='red',
                                     thickness=4,
                                     display_str_list=(),
                                     use_normalized_coordinates=True):
  image_pil = Image.fromarray(np.uint8(image)).convert('RGB')
  draw_bounding_box_on_image(image_pil, ymin, xmin, ymax, xmax, obj_num, color,
                             thickness, display_str_list,
                             use_normalized_coordinates)
  np.copyto(image, np.array(image_pil))

def draw_bounding_box_on_image(image,
                               ymin,
                               xmin,
                               ymax,
                               xmax,
                               obj_num,
                               color='red',
                               thickness=4,
                               display_str_list=(),
                               use_normalized_coordinates=True):
  draw = ImageDraw.Draw(image)
  im_width, im_height = image.size
  global im_width_gl, im_height_gl
  im_width_gl = im_width
  im_height_gl = im_height
  if use_normalized_coordinates:
    (left, right, top, bottom) = (xmin * im_width, xmax * im_width,
                                  ymin * im_height, ymax * im_height)
  else:
    (left, right, top, bottom) = (xmin, xmax, ymin, ymax)

  box_center_x = (right + left)/2
  box_center_y = (top + bottom)/2
  box_point_eq[obj_num].append([box_center_x,box_center_y,left, right, top, bottom])

  global box_size
  global box_point
  box_size = 0
  box_point = (0,0,0,0)
  if len(box_point_eq[obj_num]) == 2:
      box_center_x1, box_center_y1 = box_point_eq[obj_num][0][0], box_point_eq[obj_num][0][1]
      box_center_x2, box_center_y2 = box_point_eq[obj_num][1][0], box_point_eq[obj_num][1][1]

      distance_center_point = mt.sqrt(pow(box_center_x1 - box_center_x2,2) + pow(box_center_y1 - box_center_y2,2))
      # print(distance_center_point)
      if distance_center_point <= 15 :
          (left,right,top,bottom) = (box_point_eq[obj_num][0][2], box_point_eq[obj_num][0][3],box_point_eq[obj_num][0][4], box_point_eq[obj_num][0][5])
          box_point = (left,right,top,bottom)
          box_size = bottom - top
          del box_point_eq[obj_num][1]
      else :
          box_point_eq[obj_num][0] = box_point_eq[obj_num][1]
          box_point = (left, right, top, bottom)
          box_size = bottom - top
          del box_point_eq[obj_num][1]

  draw.line([(left, top), (left, bottom), (right, bottom),
             (right, top), (left, top)], width=thickness, fill=color)
  try:
    font = ImageFont.truetype('arial.ttf', 24)
  except IOError:
    font = ImageFont.load_default()

  display_str_heights = [font.getsize(ds)[1] for ds in display_str_list]
  total_display_str_height = (1 + 2 * 0.05) * sum(display_str_heights)

  if top > total_display_str_height:
    text_bottom = top
  else:
    text_bottom = bottom + total_display_str_height

  for display_str in display_str_list[::-1]:
    text_width, text_height = font.getsize(display_str)
    margin = np.ceil(0.05 * text_height)
    draw.rectangle(
        [(left, text_bottom - text_height - 2 * margin), (left + text_width,text_bottom)],
        fill=color)
    draw.text(
        (left + margin, text_bottom - text_height - margin),
        display_str,
        fill='black',
        font=font)
    text_bottom -= text_height - 2 * margin

def draw_mask_on_image_array(image, mask, color='red', alpha=0.4):

  if image.dtype != np.uint8:
    raise ValueError('`image` not of type np.uint8')
  if mask.dtype != np.uint8:
    raise ValueError('`mask` not of type np.uint8')
  if np.any(np.logical_and(mask != 1, mask != 0)):
    raise ValueError('`mask` elements should be in [0, 1]')
  if image.shape[:2] != mask.shape:
    raise ValueError('The image has spatial dimensions %s but the mask has '
                     'dimensions %s' % (image.shape[:2], mask.shape))
  rgb = ImageColor.getrgb(color)
  pil_image = Image.fromarray(image)

  solid_color = np.expand_dims(
      np.ones_like(mask), axis=2) * np.reshape(list(rgb), [1, 1, 3])
  pil_solid_color = Image.fromarray(np.uint8(solid_color)).convert('RGBA')
  pil_mask = Image.fromarray(np.uint8(255.0*alpha*mask)).convert('L')
  pil_image = Image.composite(pil_solid_color, pil_image, pil_mask)
  np.copyto(image, np.array(pil_image.convert('RGB')))

def draw_keypoints_on_image_array(image,
                                  keypoints,
                                  color='red',
                                  radius=2,
                                  use_normalized_coordinates=True):

  image_pil = Image.fromarray(np.uint8(image)).convert('RGB')
  draw_keypoints_on_image(image_pil, keypoints, color, radius,
                          use_normalized_coordinates)
  np.copyto(image, np.array(image_pil))

def draw_keypoints_on_image(image,
                            keypoints,
                            color='red',
                            radius=2,
                            use_normalized_coordinates=True):

  draw = ImageDraw.Draw(image)
  im_width, im_height = image.size
  keypoints_x = [k[1] for k in keypoints]
  keypoints_y = [k[0] for k in keypoints]
  if use_normalized_coordinates:
    keypoints_x = tuple([im_width * x for x in keypoints_x])
    keypoints_y = tuple([im_height * y for y in keypoints_y])
  for keypoint_x, keypoint_y in zip(keypoints_x, keypoints_y):
    draw.ellipse([(keypoint_x - radius, keypoint_y - radius),
                  (keypoint_x + radius, keypoint_y + radius)],
                 outline=color, fill=color)

def visualize_boxes_and_labels_on_image_array(
    image,
    boxes,
    classes,
    scores,
    category_index,
    instance_masks=None,
    instance_boundaries=None,
    keypoints=None,
    track_ids=None,
    use_normalized_coordinates=False,
    max_boxes_to_draw=20,
    min_score_thresh=.5,
    agnostic_mode=False,
    line_thickness=4,
    groundtruth_box_visualization_color='black',
    skip_scores=False,
    skip_labels=False,
    skip_track_ids=False,
    predict_chars = None,
    test = None):

  box_to_display_str_map = collections.defaultdict(list)
  box_to_color_map = collections.defaultdict(str)
  box_to_instance_masks_map = {}
  box_to_instance_boundaries_map = {}
  box_to_keypoints_map = collections.defaultdict(list)
  box_to_track_ids_map = {}

  if not max_boxes_to_draw:
    max_boxes_to_draw = boxes.shape[0]
  for i in range(min(max_boxes_to_draw, boxes.shape[0])):
    if scores is None or scores[i] > min_score_thresh:
      box = tuple(boxes[i].tolist())
      if instance_masks is not None:
        box_to_instance_masks_map[box] = instance_masks[i]
      if instance_boundaries is not None:
        box_to_instance_boundaries_map[box] = instance_boundaries[i]
      if keypoints is not None:
        box_to_keypoints_map[box].extend(keypoints[i])
      if track_ids is not None:
        box_to_track_ids_map[box] = track_ids[i]
      if scores is None:
        box_to_color_map[box] = groundtruth_box_visualization_color
      else:
        display_str = ''
        if not skip_labels:
          if not agnostic_mode:
            if classes[i] in six.viewkeys(category_index):
              class_name= category_index[classes[i]]['name']
            else:
              class_name = 'N/A'
            str_disp = ''
            if predict_chars is not None:
                char_1 = text_coding[predict_chars[i][0] + 1]
                char_2 = text_coding[predict_chars[i][1] + 1]
                char_3 = text_coding[predict_chars[i][2] + 1]
                if predict_chars[i][0] != 46:
                    str_disp += char_1
                if predict_chars[i][1] != 46:
                    str_disp += char_2
                if predict_chars[i][2] != 46:
                    str_disp += char_3
                display_str = str("/"+class_name + "/num"+str(i)+"/"+str_disp+"/") #object_analysis
            else: display_str = str("/" + class_name + "/num" + str(i) + "/")

        if not skip_scores:
          if not display_str:
            display_str = '{}%'.format(int(100*scores[i]))

          else:
            display_str = display_str + str(int(100*scores[i])) + "/"

        if not skip_track_ids and track_ids is not None:
          if not display_str:
            display_str = 'ID {}'.format(track_ids[i])
          else:
            display_str = '{}: ID {}'.format(display_str, track_ids[i])

        box_to_display_str_map[box].append(display_str)


        if agnostic_mode:
          box_to_color_map[box] = 'DarkOrange'
        elif track_ids is not None:
          prime_multipler = _get_multiplier_for_color_randomness()
          box_to_color_map[box] = STANDARD_COLORS[
              (prime_multipler * track_ids[i]) % len(STANDARD_COLORS)]
        else:
          box_to_color_map[box] = STANDARD_COLORS[
              classes[i] % len(STANDARD_COLORS)]

  category_name = [0] * 20
  bound_box_coord = [0]*20
  button_category = [0]*20
  category_score = [0]*20

  object_num = 0

  for box, color in box_to_color_map.items():
            ymin, xmin, ymax, xmax = box

            if instance_masks is not None:
              draw_mask_on_image_array(
                  image,
                  box_to_instance_masks_map[box],
                  color=color
              )
            if instance_boundaries is not None:
              draw_mask_on_image_array(
                  image,
                  box_to_instance_boundaries_map[box],
                  color='red',
                  alpha=1.0
              )

            parse_object = str(box_to_display_str_map[box]).split('/')
            object_name = parse_object[1]
            object_num = int(parse_object[2][-1])
            if predict_chars is not None:
                button_recog = parse_object[3]
                object_score = parse_object[4]
                button_category[object_num] = button_recog
            else: object_score = parse_object[3]


            draw_bounding_box_on_image_array(
                image,
                ymin,
                xmin,
                ymax,
                xmax,
                object_num,
                color=color,
                thickness=line_thickness,
                display_str_list=box_to_display_str_map[box],
                use_normalized_coordinates=use_normalized_coordinates)
            if test == True:
                height, width, _ = image.shape
                (left, right, top, bottom) = (round(xmin * width), round(xmax * width),
                                              round(ymin * height), round(ymax * height))
                bound_box_coord[object_num] = (left, right, top, bottom)
            else: bound_box_coord[object_num] = box_point

            category_name[object_num] = object_name
            category_score[object_num] = object_score

  if keypoints is not None:
    draw_keypoints_on_image_array(
        image,
        box_to_keypoints_map[box],
        color=color,
        radius=line_thickness / 2,
        use_normalized_coordinates=use_normalized_coordinates)

  if predict_chars is not None:
      return image, category_name[0:object_num + 1], bound_box_coord[0:object_num + 1],button_category[0:object_num + 1], category_score[0:object_num + 1]
  else:
      return image, category_name[0:object_num + 1], bound_box_coord[0:object_num + 1], category_score[0:object_num + 1]







