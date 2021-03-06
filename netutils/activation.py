

import tensorflow as tf
import tensorflow.contrib.layers as tcl



def get_lrelu(params):
    if params == None:
        leak=0.1
    else :
        leak=float(params[0])

    def lrelu(x, leak=leak, name="lrelu"):
        with tf.variable_scope(name):
            return tf.maximum(x, x*leak)
    return lrelu


def get_activation(name_config):
    name = name_config.split()[0]

    if len(name_config.split()) > 1:
        params = name_config.split()[1:]
    else:
        params = None

    if name == 'relu':
        return tf.nn.relu
    elif name == 'lrelu' or name == 'leaky_relu':
        return get_lrelu(params)
    elif name == 'softmax' : 
        return tf.nn.softmax
    elif name == 'sigmoid':
        return tf.nn.sigmoid
    elif name == 'tanh':
        return tf.tanh
    elif name == 'softplus':
        return tf.nn.softplus
    elif name == 'elu':
        return tf.nn.elu
    elif name == 'none' : 
        return None
    else :
        raise Exception("None actiavtion named " + name)

