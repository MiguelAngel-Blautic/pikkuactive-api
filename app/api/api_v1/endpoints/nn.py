import os

import tensorflow as tf
import pandas as pd
import numpy as np
import uuid

from tensorflow.keras.optimizers import Adam, SGD
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Flatten, Dense
from tensorflow.keras.layers import Conv2D, MaxPool2D
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from app.models import tbl_version

# CONFIG
DATA_FREQ = 20
SENS_NUMBER = 6
LEARNING_RATE = 0.0045


def create_model(model,output_size=2):
    columns = len(model.devices) * 6
    rows = model.fldNDuration * 20
    input_shape = (rows, columns, 1)

    cnn = Sequential()
    cnn.add(Conv2D(32, 5, input_shape=input_shape, activation='relu', padding='same'))
    cnn.add(Conv2D(16, 3, activation='relu', padding='same'))
    cnn.add(MaxPool2D(pool_size=(2, 2)))
    cnn.add(Flatten())
    cnn.add(Dense(60, activation='tanh'))
    cnn.add(Dense(output_size, activation='softmax'))

    # Generate name
    model_uuid = 'static/mpu_' + str(uuid.uuid1()) + '.h5'
    cnn.compile(optimizer=SGD(learning_rate=0.0045), loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    cnn.save(model_uuid)
    return model_uuid


def train_model(model, df, version_last):
    url = ''
    if version_last is None or version_last.url is None or not os.path.exists(version_last.url):
        url = create_model(model, len(model.movements))
    else:
        url = version_last.url

    num_epoch = 500
    tf_model = tf.keras.models.load_model(url)

    X_reshaped_train, X_reshaped_test, y_train, y_test = split_normalize_data(model, df)
    optimizador = SGD(learning_rate=LEARNING_RATE)
    if type(optimizador) == Adam:
        opt = "ADAM"
    else:
        opt = "SGD"
    tf_model.compile(optimizer=optimizador, loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    history = tf_model.fit(X_reshaped_train, y_train, batch_size=32, shuffle=True, epochs=num_epoch,
                           validation_data=(X_reshaped_test, y_test), verbose=1)
    tf_model.save(url)
    evaluation = tf_model.evaluate(X_reshaped_test, y_test)
    version = tbl_version(fldSUrl=url,
                          fldFAccuracy=float(evaluation[1]),
                          fldNEpoch=num_epoch,
                          fldFLoss=float(evaluation[0]),
                          fldSOptimizer=opt,
                          fldFLearningRate=LEARNING_RATE)

    return version


def split_normalize_data(model, df):
    label_enc = LabelEncoder()
    label_enc.fit([x.fldSLabel for x in model.movements])

    # Normalize
    filter_ac_col = [col for col in df if col.startswith('ac')]
    filter_gy_col = [col for col in df if col.startswith('gy')]
    normalized_df = df.copy()
    normalized_df[filter_ac_col] = normalized_df[filter_ac_col] / 4
    normalized_df[filter_gy_col] = normalized_df[filter_gy_col] / 1000

    # Split
    X = normalized_df.drop(['label'], axis=1)
    y = normalized_df['label']
    print(y)
    y = label_enc.transform(y)
    print(y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)

    # Reshape
    X_train = X_train.to_numpy()
    X_reshaped_train = X_train.reshape(X_train.shape[0], model.fldNDuration * DATA_FREQ, len(model.devices) * SENS_NUMBER,
                                       1)
    X_reshaped_test = X_test.to_numpy().reshape(X_test.shape[0], model.fldNDuration * DATA_FREQ,
                                                len(model.devices) * SENS_NUMBER, 1)

    return X_reshaped_train, X_reshaped_test, y_train, y_test


def generate_columns_index(end):
    columns_list = list(range(0, end))
    for i in range(0, len(columns_list), SENS_NUMBER):
        columns_list[i] = 'ac' + str(columns_list[i])
        columns_list[i + 1] = 'ac' + str(columns_list[i + 1])
        columns_list[i + 2] = 'ac' + str(columns_list[i + 2])
        columns_list[i + 3] = 'gy' + str(columns_list[i + 3])
        columns_list[i + 4] = 'gy' + str(columns_list[i + 4])
        columns_list[i + 5] = 'gy' + str(columns_list[i + 5])
    return columns_list


def data_adapter(model, captures):
    columns = len(model.devices) * SENS_NUMBER
    rows = model.fldNDuration * DATA_FREQ

    input_shape = (rows, columns, 1)
    columns_list = generate_columns_index(columns * rows)

    df = pd.DataFrame(columns=columns_list)
    # print(df)
    labels = []
    for capture in captures:
        only_data = []
        my_range = len(capture.mpu)
        if my_range == rows * len(model.devices):
            for i_data in range(0, len(capture.mpu), len(model.devices)):
                data_x = []
                for i in range(len(model.devices)):
                    data_x.append(capture.mpu[i_data + i])

                sorted_data = sorted(data_x, key=lambda data: data.device.fldNNumberDevice)

                list_sorted = []
                for data in sorted_data:
                    list_sorted.append(data.fldFAccX)
                    list_sorted.append(data.fldFAccY)
                    list_sorted.append(data.fldFAccZ)
                    list_sorted.append(data.fldFGyrX)
                    list_sorted.append(data.fldFGyrY)
                    list_sorted.append(data.fldFGyrZ)

                only_data.append(list_sorted)

                # print(i_data)

            labels.append(capture.owner.fldSLabel)
            np_data = np.resize(only_data, (1, len(only_data) * len(only_data[0])))
            df_length = len(df)
            df.loc[df_length] = np_data[0].tolist()
    pd.set_option('display.max_columns', columns * rows)
    df['label'] = labels
    # print(df.shape)
    # print(df)

    return df


def saveModel():
    pass
