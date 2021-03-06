'''
                Base_ResNet_50

            conv1:   3x3 32 1
            conv2_x ~ conv5_x:
                every conv:
                    conv -> global pooling 1x1xC
                         -> fc             1x1xC/R
                         -> relu
                         -> fc             1x1xC
                         -> sigmoid        1x1xC
                         -> scale
                    conv = conv x scale
            conv2_x: |1x1 32|
                     |3x3 32|
                     |1x1 128|  x3
            conv3_x: |1x1 64|
                     |3x3 64|
                     |1x1 256|  x8
            conv4_x: |1x1 128|
                     |3x3 128|
                     |1x1 512|  x36
            conv5_x: |1x1 256|
                     |3x3 256|
                     |1x1 1024| x3
            fc49: -> 100
            fc50: -> 10  + softmax

            Made by JinFan in 2019.11.30
'''



import tensorflow as tf
import os
import pickle
import numpy as np
import matplotlib.pyplot as plt

CIFAR = '../../../DeepLearning/神经网络/神经网络入门/cifar-10'
print(os.listdir(CIFAR))


def load_data(filename):
    """read data from data file."""
    with open(filename, 'rb') as f:
        data = pickle.load(f, encoding='bytes')
        return data[b'data'], data[b'labels']


# tensorflow.Dataset.
class CifarData:
    def __init__(self, filenames, need_shuffle):
        all_data = []
        all_labels = []
        for filename in filenames:
            data, labels = load_data(filename)
            all_data.append(data)
            all_labels.append(labels)
        self._data = np.vstack(all_data)
        self._data = self._data / 127.5 - 1
        self._labels = np.hstack(all_labels)
        print(self._data.shape)
        print(self._labels.shape)

        self._num_examples = self._data.shape[0]
        self._need_shuffle = need_shuffle
        self._indicator = 0
        if self._need_shuffle:
            self._shuffle_data()

    def _shuffle_data(self):
        # [0,1,2,3,4,5] -> [5,3,2,4,0,1]
        p = np.random.permutation(self._num_examples)
        self._data = self._data[p]
        self._labels = self._labels[p]

    def next_batch(self, batch_size):
        """return batch_size examples as a batch."""
        end_indicator = self._indicator + batch_size
        if end_indicator > self._num_examples:
            if self._need_shuffle:
                self._shuffle_data()
                self._indicator = 0
                end_indicator = batch_size
            else:
                raise Exception("have no more examples")
        if end_indicator > self._num_examples:
            raise Exception("batch size is larger than all examples")
        batch_data = self._data[self._indicator: end_indicator]
        batch_labels = self._labels[self._indicator: end_indicator]
        self._indicator = end_indicator
        return batch_data, batch_labels


train_filenames = [os.path.join(CIFAR, 'data_batch_%d' % i) for i in range(1, 6)]
test_filenames = [os.path.join(CIFAR, 'test_batch')]

train_data = CifarData(train_filenames, True)
test_val_x, test_val_y = CifarData(test_filenames, True).next_batch(10000)
val_x, val_y = test_val_x[5000:], test_val_y[5000:]
test_x, test_y = test_val_x[:5000], test_val_y[:5000]

def SE_conv(x, output_channel, stride, fitter, name, R, activation):
    with tf.name_scope(name):
        conv = tf.layers.conv2d(x,
                                output_channel,
                                fitter,
                                strides=stride,
                                padding="same",
                                activation=activation,
                                name=name)
        global_pool = tf.reduce_mean(conv, [1, 2])
        fc1 = tf.layers.dense(global_pool, output_channel // R, activation=tf.nn.relu)
        sigmoid = tf.nn.sigmoid(tf.layers.dense(fc1, output_channel))
        sigmoid_reshape = tf.reshape(sigmoid, [-1, 1, 1, output_channel])
        return tf.multiply(conv, sigmoid_reshape)

def residual_block1(x):
    """residual connection implementation"""
    strides = (1, 1)
    conv1 = SE_conv(x, 32, strides, (3, 3), "conv1", 16, tf.nn.relu)
    print(conv1)
    conv2 = SE_conv(conv1, 32, strides, (3, 3), "conv2", 16, tf.nn.relu)
    print(conv2)
    conv3 = SE_conv(conv2, 32, strides, (3, 3), "conv3", 16, tf.nn.relu)
    print(conv3)

    output_x = tf.concat([conv3, conv1], axis=-1)
    print("output_shape", output_x.shape)
    return output_x

def residual_block2(x):
    """residual connection implementation"""
    strides = (1, 1)
    conv1 = SE_conv(x, 64, strides, (3, 3), "conv1", 16, tf.nn.relu)
    print(conv1)
    conv2 = SE_conv(conv1, 64, strides, (3, 3), "conv2", 16, tf.nn.relu)
    print(conv2)
    conv3 = SE_conv(conv2, 64, strides, (3, 3), "conv3", 16, tf.nn.relu)
    print(conv3)
    output_x = tf.concat([conv3, conv1], axis=-1)
    return output_x

def residual_block3(x):
    """residual connection implementation"""
    strides = (1, 1)
    conv1 = SE_conv(x, 128, strides, (3, 3), "conv1", 16, tf.nn.relu)
    print(conv1)
    conv2 = SE_conv(conv1, 128, strides, (3, 3), "conv2", 16, tf.nn.relu)
    print(conv2)
    conv3 = SE_conv(conv2, 128, strides, (3, 3), "conv3", 16, tf.nn.relu)
    print(conv3)

    output_x = tf.concat([conv3, conv1], axis=-1)
    return output_x

def residual_block4(x):
    """residual connection implementation"""
    strides = (1, 1)
    conv1 = SE_conv(x, 256, strides, (3, 3), "conv1", 16, tf.nn.relu)
    print(conv1)
    conv2 = SE_conv(conv1, 256, strides, (3, 3), "conv2", 16, tf.nn.relu)
    print(conv2)
    conv3 = SE_conv(conv2, 256, strides, (3, 3), "conv3", 16, tf.nn.relu)
    print(conv3)

    output_x = tf.concat([conv3, conv1], axis=-1)
    return output_x



def res_net(x,
            num_residual_blocks,
            num_filter_base,
            class_num):
    """residual network implementation"""
    num_subsampling = len(num_residual_blocks)
    layers = []
    # x: [None, width, height, channel] -> [width, height, channel]
    input_size = x.get_shape().as_list()[1:]
    with tf.variable_scope('conv0'):
        conv0 = tf.layers.conv2d(x,
                                 num_filter_base,
                                 (3, 3),
                                 strides=(1, 1),
                                 padding='same',
                                 activation=tf.nn.relu,
                                 name='conv0')
        layers.append(conv0)
    # eg:num_subsampling = 4, sample_id = [0,1,2,3]
    for i in range(num_residual_blocks[0]):
        with tf.variable_scope("conv1_%d" % i):
            channels = layers[-1].get_shape().as_list()[-1]
            print(channels)
            conv = residual_block1(
                layers[-1])
            layers.append(conv)
    with tf.variable_scope("pool1"):
        pool = tf.layers.max_pooling2d(layers[-1],
                                   (2, 2),  # kernel size
                                   (2, 2),  # stride
                                   name='pool1')
        layers.append(pool)
    for i in range(num_residual_blocks[1]):
        with tf.variable_scope("conv2_%d" % i):
            channels = layers[-1].get_shape().as_list()[-1]
            print(channels)
            conv = residual_block2(
                layers[-1])
            layers.append(conv)
    with tf.variable_scope("pool2"):
        pool = tf.layers.max_pooling2d(layers[-1],
                                       (2, 2),  # kernel size
                                       (2, 2),  # stride
                                       name='pool2')
        layers.append(pool)
    for i in range(num_residual_blocks[2]):
        with tf.variable_scope("conv3_%d" % i):
            channels = layers[-1].get_shape().as_list()[-1]
            print(channels)
            conv = residual_block3(
                layers[-1])
            layers.append(conv)
    with tf.variable_scope("pool3"):
        pool = tf.layers.max_pooling2d(layers[-1],
                                       (2, 2),  # kernel size
                                       (2, 2),  # stride
                                       name='pool3')
        layers.append(pool)

    for i in range(num_residual_blocks[3]):
        with tf.variable_scope("conv4_%d" % i):
            channels = layers[-1].get_shape().as_list()[-1]
            print(channels)
            conv = residual_block4(
                layers[-1])
            layers.append(conv)

    with tf.variable_scope('fc'):
        # layer[-1].shape : [None, width, height, channel]
        # kernal_size: image_width, image_height
        global_pool = tf.reduce_mean(layers[-1], [1,2])
        fc1 = tf.layers.dense(global_pool, 100)
        logits = tf.layers.dense(fc1, class_num)
        layers.append(logits)
    return layers[-1]


with tf.name_scope("build_network"):
    x = tf.placeholder(tf.float32, [None, 3072])
    y = tf.placeholder(tf.int64, [None])
    # [None], eg: [0,5,6,3]
    x_image = tf.reshape(x, [-1, 3, 32, 32])
    # 32*32
    x_image = tf.transpose(x_image, perm=[0, 2, 3, 1])

    y_ = res_net(x_image, [3, 8, 36, 3], 32, 10)

    loss = tf.losses.sparse_softmax_cross_entropy(labels=y, logits=y_)
    # y_ -> sofmax
    # y -> one_hot
    # loss = ylogy_

    # indices
    predict = tf.argmax(y_, 1)
    # [1,0,1,1,1,0,0,0]
    correct_prediction = tf.equal(predict, y)
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float64))

    with tf.name_scope('train_op'):
        train_op = tf.train.AdamOptimizer(1e-3).minimize(loss)



with tf.name_scope("train"):
    init = tf.global_variables_initializer()
    batch_size = 30
    train_steps = 2000
    epochs = 10

    with tf.Session() as sess:
        sess.run(init)
        train_loss = []
        train_loss_all = []
        for epoch in range(epochs):
            train_acc, val_acc = [], []
            for i in range(train_steps):
                batch_data, batch_labels = train_data.next_batch(batch_size)
                loss_train, acc_train, _ = sess.run(
                    [loss, accuracy, train_op],
                    feed_dict={
                        x: batch_data,
                        y: batch_labels})
                train_loss.append(loss_train)
                if (i + 1) % 100 == 0:
                    train_acc.append(acc_train)
                    print('[Train] Epoch: %d Step: %d, loss: %4.5f'
                          % (epoch+1, i + 1, loss_train))
            train_loss_all.append(np.mean(train_loss))
            for i in range(5):
                loss_val, acc_val, _ = sess.run(
                    [loss, accuracy, train_op], feed_dict={
                        x: val_x[i*100:(i+1)*100],
                        y: val_y[i*100:(i+1)*100]
                    })
                val_acc.append(acc_val)
                print('[Val] Epoch: %d Step: %d, loss: %4.5f'
                      % (epoch+1, i + 1, loss_val))
            print("Epoch %d Train_Acc: %4.5f, Val_Acc: %4.5f" %
                (epoch+1, np.mean(train_acc), np.mean(val_acc)))
        loss_test, acc_test, _ = sess.run([loss, accuracy, train_op],
                                          feed_dict={
                                              x: test_x,
                                              y: test_y
                                          })
        print("[Test] Loss %4.5f, Accuracy %4.5f" % (loss_test, acc_test))

        plt.plot(train_loss_all)
        plt.title("Train Loss")
        plt.xlabel("epoch")
        plt.ylabel("loss")
        plt.show()
















