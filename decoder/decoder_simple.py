import os
import sys

import tensorflow as tf
import tensorflow.contrib.layers as tcl

sys.path.append('../')


from utils.weightsinit import get_weightsinit
from utils.activation import get_activation
from utils.normalization import get_normalization

from network.devgg import DEVGG



class DecoderSimple(object):

	def __init__(self, config, is_training):
		self.name = config.get('name', 'DecoderSimple')
		self.config = config
		network_config = config.copy()
		self.network = DEVGG(network_config, is_training)

	def __call__(self, i):
		x, end_points = self.network(i)
		return x

	@property
	def vars(self):
		return tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope=self.name)

