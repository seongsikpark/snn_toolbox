# -*- coding: utf-8 -*-
"""

see http://arxiv.org/pdf/1312.4400v3.pdf

Should get to 8.81% error when using data-augmentation (10.41% without).

Apply ZCA whitening and GCN.

Learning rate should be reduced by factor 0.1 twice over training.

Created on Fri Aug 19 09:15:25 2016

@author: rbodo
"""


from __future__ import absolute_import
from __future__ import print_function

from keras.datasets import cifar10
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers.core import Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, AveragePooling2D
from keras.utils import np_utils
from keras.regularizers import l2
from keras.optimizers import SGD

from snntoolbox.io_utils.plotting import plot_history

batch_size = 128
nb_classes = 10
nb_epoch = 40

# Input image dimensions
img_rows, img_cols = 32, 32
img_channels = 3

# Data set
(X_train, y_train), (X_test, y_test) = cifar10.load_data()
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)
print(X_train.shape[0], 'train samples')
print(X_test.shape[0], 'test samples')

model = Sequential()

model.add(Convolution2D(192, 5, 5, border_mode='same', init='he_normal',
                        input_shape=(img_channels, img_rows, img_cols)))
model.add(Activation('relu'))
model.add(Convolution2D(160, 1, 1, W_regularizer=l2(0.001), init='he_normal',
                        b_regularizer=l2(0.001)))
model.add(Activation('relu'))
model.add(Convolution2D(96, 1, 1, W_regularizer=l2(0.001), init='he_normal',
                        b_regularizer=l2(0.001)))
model.add(Activation('relu'))
model.add(AveragePooling2D(pool_size=(3, 3), strides=(2, 2),
                           border_mode='same'))
model.add(Dropout(0.5))

model.add(Convolution2D(192, 5, 5, border_mode='same', init='he_normal',
                        W_regularizer=l2(0.001), b_regularizer=l2(0.001)))
model.add(Activation('relu'))
model.add(Convolution2D(192, 1, 1, W_regularizer=l2(0.001), init='he_normal',
                        b_regularizer=l2(0.001)))
model.add(Activation('relu'))
model.add(Convolution2D(192, 1, 1, W_regularizer=l2(0.001), init='he_normal',
                        b_regularizer=l2(0.001)))
model.add(Activation('relu'))
model.add(AveragePooling2D(pool_size=(3, 3), strides=(2, 2),
                           border_mode='same'))
model.add(Dropout(0.5))

model.add(Convolution2D(192, 3, 3, border_mode='same', init='he_normal',
                        W_regularizer=l2(0.001), b_regularizer=l2(0.001)))
model.add(Activation('relu'))
model.add(Convolution2D(192, 1, 1, W_regularizer=l2(0.001), init='he_normal',
                        b_regularizer=l2(0.001)))
model.add(Activation('relu'))
model.add(Convolution2D(10, 1, 1, W_regularizer=l2(0.001), init='he_normal',
                        b_regularizer=l2(0.001)))
model.add(Activation('relu'))
model.add(AveragePooling2D(pool_size=(8, 8), strides=(1, 1)))
model.add(Flatten())
model.add(Activation('softmax'))

sgd = SGD(lr=0.01, momentum=0.9, decay=1e-6, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd,
              metrics=['accuracy'])

# Whether to apply global contrast normalization and ZCA whitening
gcn = True
zca = True

traingen = ImageDataGenerator(rescale=1./255, featurewise_center=gcn,
                              featurewise_std_normalization=gcn,
                              zca_whitening=zca, horizontal_flip=True,
                              rotation_range=10, width_shift_range=0.1,
                              height_shift_range=0.1)

# Compute quantities required for featurewise normalization
# (std, mean, and principal components if ZCA whitening is applied)
traingen.fit(X_train/255)

trainflow = traingen.flow(X_train, Y_train, batch_size=batch_size)

testgen = ImageDataGenerator(rescale=1./255, featurewise_center=gcn,
                             featurewise_std_normalization=gcn,
                             zca_whitening=zca)

testgen.fit(X_test/255)

testflow = testgen.flow(X_test, Y_test, batch_size=batch_size)

# Fit the model on the batches generated by datagen.flow()
history = model.fit_generator(trainflow, nb_epoch=nb_epoch,
                              samples_per_epoch=X_train.shape[0],
                              validation_data=testflow,
                              nb_val_samples=len(X_test))
plot_history(history)

score = model.evaluate_generator(testflow, val_samples=len(X_test))
print('Test score:', score[0])
print('Test accuracy:', score[1])

filename = '{:2.2f}'.format(score[1] * 100)
open(filename + '.json', 'w').write(model.to_json())
model.save_weights(filename + '.h5', overwrite=True)
