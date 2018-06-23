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

import os
import sys
sys.path.append('.')
sys.path.append("../")

import tensorflow as tf
import tensorflow.contrib.layers as tcl
import numpy as np

from encoder.encoder import get_encoder
from decoder.decoder import get_decoder
from classifier.classifier import get_classifier
from discriminator.discriminator import get_discriminator

from utils.learning_rate import get_learning_rate
from utils.learning_rate import get_global_step
from utils.optimizer import get_optimizer
from utils.loss import get_loss

from .basemodel import BaseModel


class SemiDeepGenerativeModel2(BaseModel):
	"""
		Implementation of "Semi-Supervised Learning with Deep Generative Models"
		Diederik P. Kingma, Danilo J. Rezende, Shakir Mohamed, Max Welling

		@article{DBLP:journals/corr/KingmaRMW14,
			author    = {Diederik P. Kingma and
						Danilo Jimenez Rezende and
						Shakir Mohamed and
						Max Welling},
			title     = {Semi-Supervised Learning with Deep Generative Models},
			journal   = {CoRR},
			volume    = {abs/1406.5298},
			year      = {2014},
			url       = {http://arxiv.org/abs/1406.5298},
			archivePrefix = {arXiv},
			eprint    = {1406.5298},
			timestamp = {Wed, 07 Jun 2017 14:42:55 +0200},
			biburl    = {https://dblp.org/rec/bib/journals/corr/KingmaRMW14},
			bibsource = {dblp computer science bibliography, https://dblp.org}
		}
	"""

	def __init__(self, config,
		**kwargs
	):

		super(SemiDeepGenerativeModel2, self).__init__(config, **kwargs)

		# parameters must be configured
		self.input_shape = config['input_shape']
		self.hz_dim = config['hz_dim']
		self.hx_dim = config['hx_dim']
		self.nb_classes = config['nb_classes']
		self.config = config

		# optional params
		self.debug = config.get('debug', False)
		self.m1_train_steps = config.get('m1_train_steps', 5000)

		# build model
		self.is_training = tf.placeholder(tf.bool, name='is_training')

		self.build_model_m1()
		self.build_model_m2()
		self.build_model()

		if self.is_summary:
			self.get_summary()


	def _draw_sample( self, mean, log_var ):
		epsilon = tf.random_normal( ( tf.shape( mean ) ), 0, 1 )
		sample = mean + tf.exp( 0.5 * log_var ) * epsilon
		return sample


	def build_model_m1(self):

		self.xu = tf.placeholder(tf.float32, shape=[None,] + self.input_shape, name='xu_input')

		###########################################################################
		# network define
		# 
		# x_encoder : x -> hx
		self.config['x encoder params']['name'] = 'EncoderHX_X'
		self.x_encoder = get_encoder(self.config['x encoder'], 
									self.config['x encoder params'], self.is_training)
		# decoder : hx -> x
		self.config['hx decoder params']['name'] = 'DecoderX_HX'
		self.hx_decoder = get_decoder(self.config['hx decoder'], self.config['hx decoder params'], self.is_training)

		###########################################################################
		# for unsupervised training:
		# 
		# xu --> mean_hxu, log_var_hxu ==> kl loss
		#					|
		# 			   sample_hxu --> xu_decode ==> reconstruction loss
		mean_hxu, log_var_hxu = self.x_encoder(self.xu)
		sample_hxu = self._draw_sample(mean_hxu, log_var_hxu)
		xu_decode = self.hx_decoder(sample_hxu)

		self.m1_loss_kl_z = (get_loss('kl', 'gaussian', {'mean' : mean_hxu, 'log_var' : log_var_hxu})
								* self.config.get('loss kl z weight', 1.0))
		self.m1_loss_recon = (get_loss('reconstruction', 'mse', {'x' : self.xu, 'y' : xu_decode})
								* self.config.get('loss recon weight', 1.0))
		self.m1_loss = self.m1_loss_kl_z + self.m1_loss_recon


	def build_model_m2(self):
		self.xl = tf.placeholder(tf.float32, shape=[None,] + self.input_shape, name='xl_input')
		self.yl = tf.placeholder(tf.float32, shape=[None, self.nb_classes], name='yl_input')

		###########################################################################
		# network define
		# 
		# hx_y_encoder : [hx, y] -> hz
		self.config['hx y encoder params']['name'] = 'EncoderHZ_HXY'
		self.hx_y_encoder = get_encoder(self.config['hx y encoder'], 
									self.config['hx y encoder params'], self.is_training)
		# hz_y_decoder : [hz, y] -> x_decode
		self.config['hz y decoder params']['name'] = 'DecoderX_HZY'
		self.hz_y_decoder = get_decoder(self.config['hz y decoder'], self.config['hz y decoder params'], self.is_training)
		# hx_classifier : hx -> ylogits
		self.config['hx classifier params']['name'] = 'ClassifierHX'
		self.hx_classifier = get_classifier(self.config['hx classifier'], self.config['hx classifier params'], self.is_training)

		###########################################################################
		# for supervised training:
		# 
		# xl --> mean_hxl, log_var_hxl
		#		  		  |
		#			 sample_hxl --> yllogits ==> classification loss
		#				  |
		# 			[sample_hxl, yl] --> mean_hzl, log_var_hzl ==> kl loss
		#				          |               |
		# 	  			        [yl,	   	   sample_hzl] --> xl_decode ==> reconstruction loss
		mean_hxl, log_var_hxl = self.x_encoder(self.xl)
		sample_hxl = self._draw_sample(mean_hxl, log_var_hxl)
		yllogits = self.hx_classifier(sample_hxl)
		mean_hzl, log_var_hzl = self.hx_y_encoder(tf.concat([sample_hxl, self.yl], axis=1))
		sample_hzl = self._draw_sample(mean_hzl, log_var_hzl)
		decode_hxl = self.hz_y_decoder(tf.concat([sample_hzl, self.yl], axis=1))


		self.m2_su_loss_kl_z = (get_loss('kl', 'gaussian', {'mean' : mean_hzl, 
															'log_var' : log_var_hzl, })
								* self.config.get('loss kl z weight', 1.0))
		self.m2_su_loss_recon = (get_loss('reconstruction', 'mse', {	'x' : sample_hxl, 
																		'y' : decode_hxl})
								* self.config.get('reconstruction loss weight', 1.0))
		self.m2_su_loss_cls = (get_loss('classification', 'cross entropy', {'logits' : yllogits, 
																			'labels' : self.yl})
								* self.config.get('classiciation loss weight', 1.0))
		self.m2_su_loss = self.m2_su_loss_kl_z + self.m2_su_loss_recon + self.m2_su_loss_cls


		###########################################################################
		# for unsupervised training:
		#
		# xu --> mean_hxu, log_var_hxu
		#                |
		#             sample_hxu --> yulogits --> yuprobs
		# 				  |       
		#   		 [sample_hxu,    y0] --> mean_hzu0, log_var_hzu0 ==> kl_loss * yuprobs[0]
		# 				  |			  |					|
		#				  |			[y0,           sample_hzu0] --> decode_hxu0 ==> reconstruction loss * yuprobs[0]
		#				  |
		#   	     [sample_hxu,    y1] --> mean_hzu1, log_var_hzu1 ==> kl_loss * yuprobs[1]
		#				  |			  |			        |
		#				  |			[y1,           sample_hzu1] --> decode_hxu1 ==> reconstruction loss * yuprobs[1]
		#		.......
		mean_hxu, log_var_hxu = self.x_encoder(self.xu)
		sample_hxu = self._draw_sample(mean_hxu, log_var_hxu)
		yulogits = self.hx_classifier(sample_hxu)

		yuprobs = tf.nn.softmax(yulogits)

		unsu_loss_kl_z_list = []
		unsu_loss_recon_list = []

		for i in range(self.nb_classes):
			yu_fake = tf.ones([tf.shape(self.xu)[0], ], dtype=tf.int32) * i
			yu_fake = tf.one_hot(yu_fake, depth=self.nb_classes)

			mean_hzu, log_var_hzu = self.hx_y_encoder(tf.concat([sample_hxu, yu_fake], axis=1))
			sample_hzu = self._draw_sample(mean_hzu, log_var_hzu)
			decode_hxu = self.hz_y_decoder(tf.concat([sample_hzu, yu_fake], axis=1))

			unsu_loss_kl_z_list.append(
				get_loss('kl', 'gaussian', {'mean' : mean_hzu, 
											'log_var' : log_var_hzu, 
											'instance_weight' : yuprobs[:, i] })
			)

			unsu_loss_recon_list.append(
				get_loss('reconstruction', 'mse', {	'x' : sample_hxu, 
													'y' : decode_hxu,
													'instance_weight' : yuprobs[:, i]})
			)

		self.m2_unsu_loss_kl_z = (tf.reduce_sum(unsu_loss_kl_z_list)
								* self.config.get('loss kl z weight', 1.0))
		self.m2_unsu_loss_recon = (tf.reduce_sum(unsu_loss_recon_list)
								* self.config.get('loss recon weight', 1.0))

		self.m2_unsu_loss = self.m2_unsu_loss_kl_z + self.m2_unsu_loss_recon  #+ self.m2_unsu_loss_kl_y 


	def build_model(self):
		self.xt = tf.placeholder(tf.float32, shape=[None,] + self.input_shape, name='xt_input')

		###########################################################################
		# for test models
		# 
		# xt --> mean_hxt, log_var_hxt
		#               |
		#             sample_hxt --> ytlogits --> ytprobs
		# 			   |			    			 |
		#		     [sample_hxt,    			  ytprobs] --> mean_hzt, log_var_hzt
		mean_hxt, log_var_hxt = self.x_encoder(self.xt)
		sample_hxt = self._draw_sample(mean_hxt, log_var_hxt)
		ytlogits = self.hx_classifier(sample_hxt)
		self.ytprobs = tf.nn.softmax(ytlogits)
		self.mean_hzt, self.log_var_hzt = self.hx_y_encoder(tf.concat([sample_hxt, self.ytprobs], axis=1))

		###########################################################################
		# optimizer configure
		self.global_step, self.global_step_update = get_global_step()

		if 'lr' in self.config:
			self.learning_rate = get_learning_rate(self.config['lr_scheme'], float(self.config['lr']), self.global_step, self.config['lr_params'])
			optimizer_params = {'learning_rate' : self.learning_rate}
		else:
			optimizer_params = {}

		self.m1_optimizer = get_optimizer(self.config['optimizer'], optimizer_params, self.m1_loss, 
						self.m1_vars)
		self.m2_supervised_optimizer = get_optimizer(self.config['optimizer'], optimizer_params, self.m2_su_loss, 
						self.m2_vars)
		self.m2_unsupervised_optimizer = get_optimizer(self.config['optimizer'], optimizer_params, self.m2_unsu_loss, 
						self.m2_vars)

		self.m1_train_op = tf.group([self.m1_optimizer, self.global_step_update])
		self.m2_supervised_train_op = tf.group([self.m2_supervised_optimizer, self.global_step_update])
		self.m2_unsupervised_train_op = tf.group([self.m2_unsupervised_optimizer, self.global_step_update])

		###########################################################################
		# model saver
		self.saver = tf.train.Saver(self.vars + [self.global_step,])


	@property
	def m1_vars(self):
		return self.x_encoder.vars + self.hx_decoder.vars

	@property
	def m2_vars(self):
		return self.hx_y_encoder.vars + self.hx_classifier.vars + self.hz_y_decoder.vars

	@property
	def vars(self):
		return self.x_encoder.vars + self.hx_decoder.vars + self.hx_y_encoder.vars + self.hx_classifier.vars + self.hz_y_decoder.vars


	def train_on_batch_supervised(self, sess, x_batch, y_batch):

		step = sess.run([self.global_step])[0]

		feed_dict = {
			self.xl : x_batch,
			self.yl : y_batch,
			self.is_training : True
		}

		if step < 5000:
			return step, 0, 0, None
		else:
			return self.train(sess, feed_dict, update_op = self.m2_supervised_train_op,
									loss = self.m2_su_loss, summary=self.m2_supervised_summary)


	def train_on_batch_unsupervised(self, sess, x_batch):
		step = sess.run([self.global_step])[0]
		feed_dict = {
			self.xu : x_batch,
			self.is_training : True
		}

		if step < 5000:
			return self.train(sess, feed_dict, update_op = self.m1_train_op,
									loss = self.m1_loss, summary=self.m1_summary)
		else:
			return self.train(sess, feed_dict, update_op = self.m2_unsupervised_train_op,
									loss = self.m2_unsu_loss, summary = self.m2_supervised_summary)


	def predict(self, sess, x_batch):
		'''
			p(y | x)
		'''
		feed_dict = {
			self.xtest : x_batch,
			self.is_training : False
		}
		y_pred = sess.run([self.ytest], feed_dict = feed_dict)[0]
		return y_pred


	def hidden_variable_distribution(self, sess, x_batch):
		'''
			p(z | x)
		'''
		feed_dict = {
			self.xtest : x_batch,
			self.is_training : False
		}
		mean_z, log_var_z = sess.run([self.mean_ztest, self.log_var_ztest], feed_dict=feed_dict)
		return mean_z, log_var_z


	def summary(self, sess):
		if self.is_summary:
			sum = sess.run(self.sum_hist)
			return sum
		else:
			return None


	def get_summary(self):

		# summary scalars are logged per step
		sum_list = []
		sum_list.append(tf.summary.scalar('m1/kl_z_loss', self.m1_loss_kl_z))
		sum_list.append(tf.summary.scalar('m1/reconstruction_loss', self.m1_loss_recon))
		sum_list.append(tf.summary.scalar('m1/loss', self.m1_loss))
		self.m1_summary = tf.summary.merge(sum_list)

		sum_list = []
		sum_list.append(tf.summary.scalar('m2/supervised_kl_z_loss', self.m2_su_loss_kl_z))
		sum_list.append(tf.summary.scalar('m2/supervised_reconstruction_loss', self.m2_su_loss_recon))
		sum_list.append(tf.summary.scalar('m2/supervised_clasification_loss', self.m2_su_loss_cls))
		sum_list.append(tf.summary.scalar('m2/supervised_loss', self.m2_su_loss))
		self.m2_supervised_summary = tf.summary.merge(sum_list)

		sum_list = []
		sum_list.append(tf.summary.scalar('m2/unsupervised_kl_z_loss', self.m2_unsu_loss_kl_z))
		sum_list.append(tf.summary.scalar('m2/unsupervised_reconstruction_loss', self.m2_unsu_loss_recon))
		sum_list.append(tf.summary.scalar('m2/unsupervised_loss', self.m2_unsu_loss))
		self.m2_unsupervised_summary = tf.summary.merge(sum_list)
		
		# summary hists are logged by calling self.summary()
		sum_list = [tf.summary.histogram(var.name, var) for var in self.vars]
		self.sum_hist = tf.summary.merge(sum_list)
