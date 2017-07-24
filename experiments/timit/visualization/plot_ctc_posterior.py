#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Plot the trained CTC posteriors (TIMIT corpus)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys
import tensorflow as tf
import yaml

sys.path.append('../../../')
from experiments.timit.data.load_dataset_ctc import Dataset
from experiments.timit.visualization.core.plot.ctc import posterior_test
from models.ctc.load_model import load


def do_plot(network, params, epoch=None):
    """Plot the CTC posteriors.
    Args:
        network: model to restore
        params: A dictionary of parameters
        epoch: epoch to restore
    """
    # Load dataset
    test_data = Dataset(data_type='test', label_type=params['label_type'],
                        batch_size=1,
                        num_stack=params['num_stack'],
                        num_skip=params['num_skip'],
                        is_sorted=False, is_progressbar=True)

    # Define placeholders
    network.inputs = tf.placeholder(
        tf.float32,
        shape=[None, None, network.input_size],
        name='input')
    network.labels = tf.SparseTensor(
        tf.placeholder(tf.int64, name='indices'),
        tf.placeholder(tf.int32, name='values'),
        tf.placeholder(tf.int64, name='shape'))
    network.inputs_seq_len = tf.placeholder(tf.int64,
                                            shape=[None],
                                            name='inputs_seq_len')
    network.keep_prob_input = tf.placeholder(tf.float32,
                                             name='keep_prob_input')
    network.keep_prob_hidden = tf.placeholder(tf.float32,
                                              name='keep_prob_hidden')
    network.keep_prob_output = tf.placeholder(tf.float32,
                                              name='keep_prob_output')

    # Add to the graph each operation (including model definition)
    _, logits = network.compute_loss(network.inputs,
                                     network.labels,
                                     network.inputs_seq_len,
                                     network.keep_prob_input,
                                     network.keep_prob_hidden,
                                     network.keep_prob_output)
    posteriors_op = network.posteriors(logits)

    # Create a saver for writing training checkpoints
    saver = tf.train.Saver()

    with tf.Session() as sess:
        ckpt = tf.train.get_checkpoint_state(network.model_dir)

        # If check point exists
        if ckpt:
            # Use last saved model
            model_path = ckpt.model_checkpoint_path
            if epoch is not None:
                model_path = model_path.split('/')[:-1]
                model_path = '/'.join(model_path) + '/model.ckpt-' + str(epoch)
            saver.restore(sess, model_path)
            print("Model restored: " + model_path)
        else:
            raise ValueError('There are not any checkpoints.')

        posterior_test(session=sess,
                       posteriors_op=posteriors_op,
                       network=network,
                       dataset=test_data,
                       label_type=params['label_type'],
                       save_path=network.model_dir,
                       show=True)


def main(model_path, epoch):

    # Load config file
    with open(os.path.join(model_path, 'config.yml'), "r") as f:
        config = yaml.load(f)
        params = config['param']

    # Except for a blank label
    if params['label_type'] == 'phone61':
        params['num_classes'] = 61
    elif params['label_type'] == 'phone48':
        params['num_classes'] = 48
    elif params['label_type'] == 'phone39':
        params['num_classes'] = 39
    elif params['label_type'] == 'character':
        params['num_classes'] = 28
    elif params['label_type'] == 'character_capital_divide':
        params['num_classes'] = 71

    # Model setting
    CTCModel = load(model_type=params['model'])
    network = CTCModel(
        batch_size=1,
        input_size=params['input_size'] * params['num_stack'],
        num_unit=params['num_unit'],
        num_layer=params['num_layer'],
        num_classes=params['num_classes'],
        parameter_init=params['weight_init'],
        clip_grad=params['clip_grad'],
        clip_activation=params['clip_activation'],
        dropout_ratio_input=params['dropout_input'],
        dropout_ratio_hidden=params['dropout_hidden'],
        dropout_ratio_output=params['dropout_output'],
        num_proj=params['num_proj'],
        weight_decay=params['weight_decay'])

    network.model_dir = model_path
    print(network.model_dir)
    do_plot(network=network, params=params, epoch=epoch)


if __name__ == '__main__':

    args = sys.argv
    if len(args) == 2:
        model_path = args[1]
        epoch = None
    elif len(args) == 3:
        model_path = args[1]
        epoch = args[2]
    else:
        raise ValueError(
            ("Set a path to saved model.\n"
             "Usase: python plot_ctc_posterior.py path_to_saved_model"))
    main(model_path=model_path, epoch=epoch)
