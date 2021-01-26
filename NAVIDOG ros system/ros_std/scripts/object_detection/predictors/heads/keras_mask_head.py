# Copyright 2017 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Keras Mask Heads.

Contains Mask prediction head classes for different meta architectures.
All the mask prediction heads have a predict function that receives the
`features` as the first argument and returns `mask_predictions`.
"""
import math
import tensorflow as tf

from object_detection.predictors.heads import head
from object_detection.utils import ops
from object_detection.utils import shape_utils


class ConvolutionalMaskHead(head.KerasHead):
  """Convolutional class prediction head."""

  def __init__(self,
               is_training,
               num_classes,
               use_dropout,
               dropout_keep_prob,
               kernel_size,
               num_predictions_per_location,
               conv_hyperparams,
               freeze_batchnorm,
               use_depthwise=False,
               mask_height=7,
               mask_width=7,
               masks_are_class_agnostic=False,
               name=None):
    """Constructor.

    Args:
      is_training: Indicates whether the BoxPredictor is in training mode.
      num_classes: Number of classes.
      use_dropout: Option to use dropout or not.  Note that a single dropout
        op is applied here prior to both box and class predictions, which stands
        in contrast to the ConvolutionalBoxPredictor below.
      dropout_keep_prob: Keep probability for dropout.
        This is only used if use_dropout is True.
      kernel_size: Size of final convolution kernel.  If the
        spatial resolution of the feature map is smaller than the kernel size,
        then the kernel size is automatically set to be
        min(feature_width, feature_height).
      num_predictions_per_location: Number of box predictions to be made per
        spatial location. Int specifying number of boxes per location.
      conv_hyperparams: A `hyperparams_builder.KerasLayerHyperparams` object
        containing hyperparameters for convolution ops.
      freeze_batchnorm: Bool. Whether to freeze batch norm parameters during
        training or not. When training with a small batch size (e.g. 1), it is
        desirable to freeze batch norm update and use pretrained batch norm
        params.
      use_depthwise: Whether to use depthwise convolutions for prediction
        steps. Default is False.
      mask_height: Desired output mask height. The default value is 7.
      mask_width: Desired output mask width. The default value is 7.
      masks_are_class_agnostic: Boolean determining if the mask-head is
        class-agnostic or not.
      name: A string name scope to assign to the model. If `None`, Keras
        will auto-generate one from the class name.

    Raises:
      ValueError: if min_depth > max_depth.
    """
    super(ConvolutionalMaskHead, self).__init__(name=name)
    self._is_training = is_training
    self._num_classes = num_classes
    self._use_dropout = use_dropout
    self._dropout_keep_prob = dropout_keep_prob
    self._kernel_size = kernel_size
    self._num_predictions_per_location = num_predictions_per_location
    self._use_depthwise = use_depthwise
    self._mask_height = mask_height
    self._mask_width = mask_width
    self._masks_are_class_agnostic = masks_are_class_agnostic

    self._mask_predictor_layers = []

    # Add a slot for the background class.
    if self._masks_are_class_agnostic:
      self._num_masks = 1
    else:
      self._num_masks = self._num_classes

    num_mask_channels = self._num_masks * self._mask_height * self._mask_width

    if self._use_dropout:
      self._mask_predictor_layers.append(
          # The Dropout layer's `training` parameter for the call method must
          # be set implicitly by the Keras set_learning_phase. The object
          # detection training code takes care of this.
          tf.keras.layers.Dropout(rate=1.0 - self._dropout_keep_prob))
    if self._use_depthwise:
      self._mask_predictor_layers.append(
          tf.keras.layers.DepthwiseConv2D(
              [self._kernel_size, self._kernel_size],
              padding='SAME',
              depth_multiplier=1,
              strides=1,
              dilation_rate=1,
              name='MaskPredictor_depthwise',
              **conv_hyperparams.params()))
      self._mask_predictor_layers.append(
          conv_hyperparams.build_batch_norm(
              training=(is_training and not freeze_batchnorm),
              name='MaskPredictor_depthwise_batchnorm'))
      self._mask_predictor_layers.append(
          conv_hyperparams.build_activation_layer(
              name='MaskPredictor_depthwise_activation'))
      self._mask_predictor_layers.append(
          tf.keras.layers.Conv2D(
              num_predictions_per_location * num_mask_channels, [1, 1],
              name='MaskPredictor',
              **conv_hyperparams.params(use_bias=True)))
    else:
      self._mask_predictor_layers.append(
          tf.keras.layers.Conv2D(
              num_predictions_per_location * num_mask_channels,
              [self._kernel_size, self._kernel_size],
              padding='SAME',
              name='MaskPredictor',
              **conv_hyperparams.params(use_bias=True)))

  def _predict(self, features):
    """Predicts boxes.

    Args:
      features: A float tensor of shape [batch_size, height, width, channels]
        containing image features.

    Returns:
      mask_predictions: A float tensors of shape
        [batch_size, num_anchors, num_masks, mask_height, mask_width]
        representing the mask predictions for the proposals.
    """
    mask_predictions = features
    for layer in self._mask_predictor_layers:
      mask_predictions = layer(mask_predictions)
    batch_size = features.get_shape().as_list()[0]
    if batch_size is None:
      batch_size = tf.shape(features)[0]
    mask_predictions = tf.reshape(
        mask_predictions,
        [batch_size, -1, self._num_masks, self._mask_height, self._mask_width])
    return mask_predictions


class MaskRCNNMaskHead(head.KerasHead):
  """Mask RCNN mask prediction head.

  This is a piece of Mask RCNN which is responsible for predicting
  just the pixelwise foreground scores for regions within the boxes.

  Please refer to Mask RCNN paper:
  https://arxiv.org/abs/1703.06870
  """

  def __init__(self,
               is_training,
               num_classes,
               freeze_batchnorm,
               conv_hyperparams,
               mask_height=14,
               mask_width=14,
               mask_prediction_num_conv_layers=2,
               mask_prediction_conv_depth=256,
               masks_are_class_agnostic=False,
               convolve_then_upsample=False,
               name=None):
    """Constructor.

    Args:
      is_training: Indicates whether the Mask head is in training mode.
      num_classes: number of classes.  Note that num_classes *does not*
        include the background category, so if groundtruth labels take values
        in {0, 1, .., K-1}, num_classes=K (and not K+1, even though the
        assigned classification targets can range from {0,... K}).
      freeze_batchnorm: Whether to freeze batch norm parameters during
        training or not. When training with a small batch size (e.g. 1), it is
        desirable to freeze batch norm update and use pretrained batch norm
        params.
      conv_hyperparams: A `hyperparams_builder.KerasLayerHyperparams` object
        containing hyperparameters for convolution ops.
      mask_height: Desired output mask height. The default value is 14.
      mask_width: Desired output mask width. The default value is 14.
      mask_prediction_num_conv_layers: Number of convolution layers applied to
        the image_features in mask prediction branch.
      mask_prediction_conv_depth: The depth for the first conv2d_transpose op
        applied to the image_features in the mask prediction branch. If set
        to 0, the depth of the convolution layers will be automatically chosen
        based on the number of object classes and the number of channels in the
        image features.
      masks_are_class_agnostic: Boolean determining if the mask-head is
        class-agnostic or not.
      convolve_then_upsample: Whether to apply convolutions on mask features
        before upsampling using nearest neighbor resizing. Otherwise, mask
        features are resized to [`mask_height`, `mask_width`] using bilinear
        resizing before applying convolutions.
      name: A string name scope to assign to the mask head. If `None`, Keras
        will auto-generate one from the class name.
    """
    super(MaskRCNNMaskHead, self).__init__(name=name)
    self._is_training = is_training
    self._freeze_batchnorm = freeze_batchnorm
    self._num_classes = num_classes
    self._conv_hyperparams = conv_hyperparams
    self._mask_height = mask_height
    self._mask_width = mask_width
    self._mask_prediction_num_conv_layers = mask_prediction_num_conv_layers
    self._mask_prediction_conv_depth = mask_prediction_conv_depth
    self._masks_are_class_agnostic = masks_are_class_agnostic
    self._convolve_then_upsample = convolve_then_upsample

    self._mask_predictor_layers = []

  def build(self, input_shapes):
    num_conv_channels = self._mask_prediction_conv_depth
    if num_conv_channels == 0:
      num_feature_channels = input_shapes.as_list()[3]
      num_conv_channels = self._get_mask_predictor_conv_depth(
          num_feature_channels, self._num_classes)

    for i in range(self._mask_prediction_num_conv_layers - 1):
      self._mask_predictor_layers.append(
          tf.keras.layers.Conv2D(
              num_conv_channels,
              [3, 3],
              padding='SAME',
              name='MaskPredictor_conv2d_{}'.format(i),
              **self._conv_hyperparams.params()))
      self._mask_predictor_layers.append(
          self._conv_hyperparams.build_batch_norm(
              training=(self._is_training and not self._freeze_batchnorm),
              name='MaskPredictor_batchnorm_{}'.format(i)))
      self._mask_predictor_layers.append(
          self._conv_hyperparams.build_activation_layer(
              name='MaskPredictor_activation_{}'.format(i)))

    if self._convolve_then_upsample:
      # Replace Transposed Convolution with a Nearest Neighbor upsampling step
      # followed by 3x3 convolution.
      height_scale = self._mask_height / shape_utils.get_dim_as_int(
          input_shapes[1])
      width_scale = self._mask_width / shape_utils.get_dim_as_int(
          input_shapes[2])
      # pylint: disable=g-long-lambda
      self._mask_predictor_layers.append(tf.keras.layers.Lambda(
          lambda features: ops.nearest_neighbor_upsampling(
              features, height_scale=height_scale, width_scale=width_scale)
      ))
      # pylint: enable=g-long-lambda
      self._mask_predictor_layers.append(
          tf.keras.layers.Conv2D(
              num_conv_channels,
              [3, 3],
              padding='SAME',
              name='MaskPredictor_upsample_conv2d',
              **self._conv_hyperparams.params()))
      self._mask_predictor_layers.append(
          self._conv_hyperparams.build_batch_norm(
              training=(self._is_training and not self._freeze_batchnorm),
              name='MaskPredictor_upsample_batchnorm'))
      self._mask_predictor_layers.append(
          self._conv_hyperparams.build_activation_layer(
              name='MaskPredictor_upsample_activation'))

    num_masks = 1 if self._masks_are_class_agnostic else self._num_classes
    self._mask_predictor_layers.append(
        tf.keras.layers.Conv2D(
            num_masks,
            [3, 3],
            padding='SAME',
            name='MaskPredictor_last_conv2d',
            **self._conv_hyperparams.params(use_bias=True)))

    self.built = True

  def _get_mask_predictor_conv_depth(self,
                                     num_feature_channels,
                                     num_classes,
                                     class_weight=3.0,
                                     feature_weight=2.0):
    """Computes the depth of the mask predictor convolutions.

    Computes the depth of the mask predictor convolutions given feature channels
    and number of classes by performing a weighted average of the two in
    log space to compute the number of convolution channels. The weights that
    are used for computing the weighted average do not need to sum to 1.

    Args:
      num_feature_channels: An integer containing the number of feature
        channels.
      num_classes: An integer containing the number of classes.
      class_weight: Class weight used in computing the weighted average.
      feature_weight: Feature weight used in computing the weighted average.

    Returns:
      An integer containing the number of convolution channels used by mask
        predictor.
    """
    num_feature_channels_log = math.log(float(num_feature_channels), 2.0)
    num_classes_log = math.log(float(num_classes), 2.0)
    weighted_num_feature_channels_log = (
        num_feature_channels_log * feature_weight)
    weighted_num_classes_log = num_classes_log * class_weight
    total_weight = feature_weight + class_weight
    num_conv_channels_log = round(
        (weighted_num_feature_channels_log + weighted_num_classes_log) /
        total_weight)
    return int(math.pow(2.0, num_conv_channels_log))

  def _predict(self, features):
    """Predicts pixelwise foreground scores for regions within the boxes.

    Args:
      features: A float tensor of shape [batch_size, height, width, channels]
        containing features for a batch of images.

    Returns:
      instance_masks: A float tensor of shape
          [batch_size, 1, num_classes, mask_height, mask_width].
    """
    if not self._convolve_then_upsample:
      features = tf.image.resize_bilinear(
          features, [self._mask_height, self._mask_width],
          align_corners=True)

    mask_predictions = features
    for layer in self._mask_predictor_layers:
      mask_predictions = layer(mask_predictions)
    return tf.expand_dims(
        tf.transpose(mask_predictions, perm=[0, 3, 1, 2]),
        axis=1,
        name='MaskPredictor')


class WeightSharedConvolutionalMaskHead(head.KerasHead):
  """Weight shared convolutional mask prediction head based on Keras."""

  def __init__(self,
               num_classes,
               num_predictions_per_location,
               conv_hyperparams,
               kernel_size=3,
               use_dropout=False,
               dropout_keep_prob=0.8,
               mask_height=7,
               mask_width=7,
               masks_are_class_agnostic=False,
               name=None):
    """Constructor.

    Args:
      num_classes: number of classes.  Note that num_classes *does not*
        include the background category, so if groundtruth labels take values
        in {0, 1, .., K-1}, num_classes=K (and not K+1, even though the
        assigned classification targets can range from {0,... K}).
      num_predictions_per_location: Number of box predictions to be made per
        spatial location. Int specifying number of boxes per location.
      conv_hyperparams: A `hyperparams_builder.KerasLayerHyperparams` object
        containing hyperparameters for convolution ops.
      kernel_size: Size of final convolution kernel.
      use_dropout: Whether to apply dropout to class prediction head.
      dropout_keep_prob: Probability of keeping activiations.
      mask_height: Desired output mask height. The default value is 7.
      mask_width: Desired output mask width. The default value is 7.
      masks_are_class_agnostic: Boolean determining if the mask-head is
        class-agnostic or not.
 ��GW^��̬�A|�'�#�te��Z$�^8O !+���t��I�
E�W37�ࠗ���`*B1��!!K�8���~_eC�R+��w�\�?$�$��A��N1��/��Qݷ�r�O
��f*����%��A��I4� ��EG1�(��= U�W�B�ߺ:�Dk�\�����e�� w�5���TU�`g^�2� Y�a$�R����U��"p�(�RձT���;ꍆN��	VC��ѴҢ�@���ע|{���h\�.����Z�wU�y��puR���),��~X�Z4pp׶h�m:����*��VВ����/H8:�b9vo\�kݐk�W4Z7��7+R�z�>�$-��OZ�)���5pMN�)�y�5`�7��}��{Koװ��j�5��Q�C���B���X�@'0�SCK(4�X��h��vEÕ2 ٹ��e/:�Æ��:�n@�f��'�	]\Ֆݥ���MX��ɢzY:��#`,d�ӡ�B>��DR��8�ꤚ��Nj8�餖�ڼ�_(�_E��Pn���j_�����Nj8�餖�ڐ���NAf�� �<�����`Qq0��zg�<'*N��uE�Sڵ���)��U���b����T�~s�U�K��V�������+�W�U�� �A�3HC/ �q�%e��u��0%�j�B��kֱ0ՙ�X���K� ���@��LG�+��n4e�kw~���>9Fh�h���v��w�}��cP @��`���{=^ac��!���F���d�:r_��z?���'�իr�����\�x����"�l�zO�a����B>{�O����!w��(@����h����Dc�z�E1le�z4�����+�G�����|=��%�p
��?#1		=��_�[�Ec�z1f-�����<��ͬ:ಎ>��e�E�E�H��#)��+��-����n�*;���2��kp�+8��#ZK
QLo�"ۘ3��0���#P°�]�a����Q=�>�P����8}gPR��k7��9:(�7i�)lS!_���ӆ4�ꍮ)��b�f�5���=��mW��C�7R�y�Iػ6Ҟ=�뜷���H����z`�FzWs�[F��i���u`fD~�鋢�ž�9Ae(4yu���U�{�ɓmhGTi��x��m�*�˽����� �۞r#���_��r�\�m]NQ9�[Vg�AR�K�T�ХU�.���@�v�R�]�d��%I�|o	��yG;�ܷ�*�U}j��:�d]މ�Ԛq�E��ᰱ�m���]�e���FK���{�i����߿<[[CEe�F7��)���{���=JK��<��eFb�\Zه���Hؽ�U��{6zޘ㪟�?���_�f.]�5ɳ�r*�n��+�cY�[9���np�k ��<\���rN�b_�٥��i.�V5�+��~HԊ�!nWmky�v�+*C8���y���\�b�Dث�����+X��(�ٝ�=�?=2�����������5�U��C�
��`z��{�IA��\�6�ա�E����P��)�o�Dn�i�9Q�EH�%q�͊��e݊b�p.�*��p\*"�p.�}yA�B��'�|��C�Ӈ���)�e��@.��ԛ?��E�чD} ���@.���ݽ��Ǉ#��l8f��)�y�q5� ||��9��%V��Ek����`����(n�H��w�0�#����!�y�6�(a/悻�Q{q���ň�^o�+�'�#n �j��*Ɇ�ʐ�L��7����z�R���c�fs '9�H��!���0��C~�D�0�dI8���	���$	��d�േ��"xm�S9H �ܶ��-tݳ�1ݽ�*X��ly��V��p Wa�`���J�7-������hj�|5��U�&��^:�B[��
�y�bcͿ�Y_-[>B�9�ė������g���=�1��p�F�x�ah片s�P�ȯ�hPp��F��~�/�ѧQ\9ڣ�b�wxz�:���~psCUw"�6O���am��ӫ"J��0y݅Կ�SjHශ0�4��@��,��6�Rj�