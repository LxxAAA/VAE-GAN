# -*- coding: utf-8 -*-
# MIT License
# 
# Copyright (c) 2018 ZhicongYan
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================


import tensorflow as tf
import tensorflow.contrib.layers as tcl


def inception_v3_figure4(
	name, x, end_points, 
	act_fn, norm_fn, norm_params, winit_fn, 
	filters=[[48,64], [64,96,], [32], [64]],
	is_avg_pooling=True, downsample=False):

	if downsample:
		ds=2
	else:
		ds=1

	with tf.variable_scope(name):
		with tf.variable_scope('branch0'):
			branch_0 = tcl.conv2d(x, filters[0][0], 1, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0a_1x1')
			branch_0 = tcl.conv2d(branch_0, filters[0][1], 5,
						stride=ds, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0b_5x5')
		with tf.variable_scope('branch1'):
			branch_1 = tcl.conv2d(x, filters[1][0],  1, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_1a_1x1')
			branch_1 = tcl.conv2d(branch_1, filters[1][1], 3, 
						stride=ds, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_1b_3x3')
		with tf.variable_scope('branch2'):
			if is_avg_pooling:
				branch_2 = tcl.avg_pool2d(x, 3, stride=ds, scope='avgpool_2a_3x3')
			else:
				branch_2 = tcl.max_pool2d(x, 3, stride=ds, scope='maxpool_2a_3x3')
			branch_2 = tcl.conv2d(branch_2, filters[2][0], 1,
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_2b_1x1')
		with tf.variable_scope('branch3'):
			branch_3 = tcl.conv2d(x, filters[3][0],  1, 
						stride=ds, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_3a_1x1')

		x = tf.concat(axis=3, values=[branch_0, branch_1, branch_2, branch_3])
		end_points[name] = x
	return x, end_points


def inception_v3_figure5(
	name, x, end_points, 
	act_fn, norm_fn, norm_params, winit_fn, 
	filters=[[64,96,96,], [48,64,], [64], [64]],
	is_avg_pooling=True):

	with tf.variable_scope(name):
		with tf.variable_scope('branch0'):
			branch_0 = tcl.conv2d(x, filters[0][0], 1, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0a_1x1')
			branch_0 = tcl.conv2d(branch_0, filters[0][1], 3,
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0b_3x3')
			branch_0 = tcl.conv2d(branch_0, filters[0][2], 3,
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0c_3x3')
		with tf.variable_scope('branch1'):
			branch_1 = tcl.conv2d(x, filters[1][0],  1, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_1a_1x1')
			branch_1 = tcl.conv2d(branch_1, filters[1][1], 3, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_1b_3x3')
		with tf.variable_scope('branch2'):
			if is_avg_pooling:
				branch_2 = tcl.avg_pool2d(x, 3, stride=1,
						padding='SAME', scope='avgpool_2a_3x3')
			else:
				branch_2 = tcl.max_pool2d(x, 3, stride=1, 
						padding='SAME', scope='maxpool_2a_3x3')

			if not downsample:
				branch_2 = tcl.conv2d(branch_2, filters[2][0], 1,
							stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
							padding='SAME', weights_initializer=winit_fn, scope='conv2d_2b_1x1')

		with tf.variable_scope('branch3'):
			branch_3 = tcl.conv2d(x, filters[3][0],  1, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_3a_1x1')

		x = tf.concat(axis=3, values=[branch_0, branch_1, branch_2, branch_3])

		end_points[name] = x
	return x, end_points


def inception_v3_figure5_downsample(
	name, x, end_points, 
	act_fn, norm_fn, norm_params, winit_fn, 
	filters=[[64,96,96,], [384,],],
	is_avg_pooling=True):


	with tf.variable_scope(name):
		with tf.variable_scope('branch0'):
			branch_0 = tcl.conv2d(x, filters[0][0], 1, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0a_1x1')
			branch_0 = tcl.conv2d(branch_0, filters[0][1], 3,
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0b_3x3')
			branch_0 = tcl.conv2d(branch_0, filters[0][2], 3,
						stride=2, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='VALID', weights_initializer=winit_fn, scope='conv2d_0c_3x3')

		with tf.variable_scope('branch1'):
			branch_1 = tcl.conv2d(x, filters[1][0], 3, 
						stride=2, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='VALID', weights_initializer=winit_fn, scope='conv2d_1a_3x3')

		with tf.variable_scope('branch2'):
			if is_avg_pooling:
				branch_2 = tcl.avg_pool2d(x, 3, stride=2,
						padding='VALID', scope='avgpool_2a_3x3')
			else:
				branch_2 = tcl.max_pool2d(x, 3, stride=2, 
						padding='VALID', scope='maxpool_2a_3x3')

		x = tf.concat(axis=3, values=[branch_0, branch_1, branch_2])

		end_points[name] = x
	return x, end_points



def inception_v3_figure6(
	name, x, end_points, n,
	act_fn, norm_fn, norm_params, winit_fn, 
	filters=[[128,128,128,128,192,], [128,128,192,], [192], [192]],
	is_avg_pooling=True):


	with tf.variable_scope(name):
		with tf.variable_scope('branch0'):
			branch_0 = tcl.conv2d(x, filters[0][0], 1, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0a_1x1')
			branch_0 = tcl.conv2d(branch_0, filters[0][1], [1, n],
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0b_1xn')
			branch_0 = tcl.conv2d(branch_0, filters[0][2], [n, 1],
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0c_nx1')
			branch_0 = tcl.conv2d(branch_0, filters[0][3], [1, n],
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0d_1xn')
			branch_0 = tcl.conv2d(branch_0, filters[0][4], [n, 1],
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0e_nx1')

		with tf.variable_scope('branch1'):
			branch_1 = tcl.conv2d(x, filters[1][0],  1, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_1a_1x1')
			branch_1 = tcl.conv2d(branch_1, filters[1][1], [1, n], 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_1b_1xn')
			branch_1 = tcl.conv2d(branch_1, filters[1][2], [n, 1], 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_1c_nx1')

		with tf.variable_scope('branch2'):
			if is_avg_pooling:
				branch_2 = tcl.avg_pool2d(x, 3, 
						padding='SAME', stride=1, scope='avgpool_2a_3x3')
			else:
				branch_2 = tcl.max_pool2d(x, 3, 
						padding='SAME', stride=1, scope='maxpool_2a_3x3')
			branch_2 = tcl.conv2d(branch_2, filters[2][0], 1,
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_2b_1x1')

	
		with tf.variable_scope('branch3'):
			branch_3 = tcl.conv2d(x, filters[3][0],  1, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_3a_1x1')


		x = tf.concat(axis=3, values=[branch_0, branch_1, branch_2, branch_3])

		end_points[name] = x
	return x, end_points



def inception_v3_figure6_downsample(
	name, x, end_points, n,
	act_fn, norm_fn, norm_params, winit_fn, 
	filters=[[192,192,192,192,], [192,320], [192], [192]],
	is_avg_pooling=True):

	with tf.variable_scope(name):
		with tf.variable_scope('branch0'):
			branch_0 = tcl.conv2d(x, filters[0][0], 1, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0a_1x1')
			branch_0 = tcl.conv2d(branch_0, filters[0][1], [1, n],
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0b_1xn')
			branch_0 = tcl.conv2d(branch_0, filters[0][2], [n, 1],
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0c_nx1')
			branch_0 = tcl.conv2d(branch_0, filters[0][3], [3, 3],
						stride=2, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='VALID', weights_initializer=winit_fn, scope='conv2d_0d_3x3')

		with tf.variable_scope('branch1'):
			branch_1 = tcl.conv2d(x, filters[1][0],  1, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_1a_1x1')
			branch_1 = tcl.conv2d(branch_1, filters[1][1], [3, 3], 
						stride=2, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='VALID', weights_initializer=winit_fn, scope='conv2d_1b_3x3')

		with tf.variable_scope('branch2'):
			if is_avg_pooling:
				branch_2 = tcl.avg_pool2d(x, 3, 
						padding='VALID', stride=2, scope='avgpool_2a_3x3')
			else:
				branch_2 = tcl.max_pool2d(x, 3, 
						padding='VALID', stride=2, scope='maxpool_2a_3x3')

		x = tf.concat(axis=3, values=[branch_0, branch_1, branch_2])

		end_points[name] = x
	return x, end_points



def inception_v3_figure7(
	name, x, end_points,
	act_fn, norm_fn, norm_params, winit_fn, 
	filters=[[448,384,[384,384,],], [384,[384,384,],], [192], [320]],
	is_avg_pooling=True, downsample=False):

	if downsample:
		ds=2
	else:
		ds=1

	with tf.variable_scope(name):
		with tf.variable_scope('branch0'):
			branch_0 = tcl.conv2d(x, filters[0][0], 1, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0a_1x1')
			branch_0 = tcl.conv2d(branch_0, filters[0][1], [3, 3],
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_0b_3x3')

			with tf.variable_scope('branch0a'):
				branch_0a = tcl.conv2d(branch_0, filters[0][2][0], [1, 3],
							stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
							padding='SAME', weights_initializer=winit_fn, scope='conv2d_0ac_1x3')
			with tf.variable_scope('branch0b'):
				branch_0b = tcl.conv2d(branch_0, filters[0][2][1], [3, 1],
							stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
							padding='SAME', weights_initializer=winit_fn, scope='conv2d_0bc_3x1')

		with tf.variable_scope('branch1'):
			branch_1 = tcl.conv2d(x, filters[1][0],  1, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_1a_1x1')
			with tf.variable_scope('branch1a'):
				branch_1a = tcl.conv2d(branch_1, filters[1][1][0], [1, 3],
							stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
							padding='SAME', weights_initializer=winit_fn, scope='conv2d_1ab_1x3')
			with tf.variable_scope('branch1b'):
				branch_1b = tcl.conv2d(branch_1, filters[1][1][1], [3, 1],
							stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
							padding='SAME', weights_initializer=winit_fn, scope='conv2d_1bb_3x1')

		with tf.variable_scope('branch2'):
			if is_avg_pooling:
				branch_2 = tcl.avg_pool2d(x, 3, 
							padding='SAME', stride=1, scope='avgpool_2a_3x3')
			else:
				branch_2 = tcl.max_pool2d(x, 3, 
							padding='SAME', stride=1, scope='maxpool_2a_3x3')
			branch_2 = tcl.conv2d(branch_2, filters[2][0], 1,
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_2b_1x1')

		with tf.variable_scope('branch3'):
			branch_3 = tcl.conv2d(x, filters[3][0],  1, 
						stride=1, activation_fn=act_fn, normalizer_fn=norm_fn, normalizer_params=norm_params,
						padding='SAME', weights_initializer=winit_fn, scope='conv2d_3a_1x1')
		x = tf.concat(axis=3, values=[branch_0a, branch_0b, branch_1a, branch_1b, branch_2, branch_3])
		end_points[name] = x
	return x, end_points



