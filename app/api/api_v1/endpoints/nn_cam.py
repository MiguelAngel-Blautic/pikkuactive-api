import os

import tensorflow as tf
import pandas as pd
import numpy as np
import uuid
from tensorflow.keras.optimizers import SGD
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Flatten, Dense
from tensorflow.keras.layers import Conv2D, MaxPool2D
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from app.models import tbl_version

# CONFIG
DATA_FREQ = 10
SENS_NUMBER = 34  # 17 puntos por 2 coordenadas


def create_model(model, output_size=2):
    columns = SENS_NUMBER
    rows = model.fldNDuration * DATA_FREQ
    input_shape = (rows, columns, 1)

    cnn = Sequential()
    cnn.add(Conv2D(32, 5, input_shape=input_shape, activation='relu', padding='same'))
    cnn.add(Conv2D(16, 3, activation='relu', padding='same'))
    cnn.add(MaxPool2D(pool_size=(2, 2)))
    cnn.add(Flatten())
    cnn.add(Dense(60, activation='tanh'))
    # cnn.add(Dense(output_size, activation='softmax'))
    cnn.add(Dense(output_size, activation='sigmoid'))

    # Generate name
    model_uuid = 'static/cam_' + str(uuid.uuid1()) + '.h5'
    cnn.compile(optimizer=SGD(learning_rate=0.0045), loss='binary_crossentropy', metrics=['accuracy'])

    # cnn.compile(optimizer=SGD(learning_rate=0.0045), loss='categorical_crossentropy', metrics=['accuracy'])
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
    print('Shape', y_train.shape)

    tf_model.compile(optimizer=SGD(learning_rate=0.0045), loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    history = tf_model.fit(X_reshaped_train, y_train, batch_size=32, shuffle=True, epochs=num_epoch,
                           validation_data=(X_reshaped_test, y_test), verbose=1)
    tf_model.save(url)
    evaluation = tf_model.evaluate(X_reshaped_test, y_test)
    version = tbl_version(fldSUrl=url,
                          fldFAccuracy=float(evaluation[1]),
                          fldNEpoch=num_epoch,
                          fldFLoss=float(evaluation[0]),
                          fldSOptimizer='SGD',
                          fldFLearningRate=0.0045)

    return version


def split_normalize_data(model, df):
    label_enc = LabelEncoder()
    label_enc.fit([x.fldSLabel for x in model.movements])

    # Normalize
    normalized_df = df.copy()

    # Split
    X = normalized_df.drop(['label'], axis=1)
    y = normalized_df['label']
    print(y)
    y = label_enc.transform(y)
    print(y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)

    # Reshape
    X_train = X_train.to_numpy()
    X_reshaped_train = X_train.reshape(X_train.shape[0], model.fldNDuration * DATA_FREQ, SENS_NUMBER,
                                       1)
    X_reshaped_test = X_test.to_numpy().reshape(X_test.shape[0], model.fldNDuration * DATA_FREQ,
                                                SENS_NUMBER, 1)

    return X_reshaped_train, X_reshaped_test, y_train, y_test


def generate_columns_index(end):
    columns_list = list(range(0, end))
    for i in range(0, len(columns_list), SENS_NUMBER):
        for j in range(0, SENS_NUMBER, 2):
            columns_list[i+j] = 'p'+str((j//2)+1)+'X'
            columns_list[i+j+1] = 'p'+str((j//2)+1)+'Y'
    return columns_list


def data_adapter(model, captures):
    columns = SENS_NUMBER
    rows = model.fldNDuration * DATA_FREQ

    input_shape = (rows, columns, 1)
    columns_list = generate_columns_index(columns * rows)  # ['p1', 'p2'...]
    # columns_list = ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p12', 'p13', 'p14', 'p15', 'p16', 'p17']
    # columns_list = []
    # for i in range(1, 17):
    #    columns_list.append('p'+str(i)+'X')
    #    columns_list.append('p'+str(i)+'Y')

    df = pd.DataFrame(columns=columns_list)
    labels = []
    for capture in captures:
        only_data = []
        datos = capture.datos
        if len(datos) > 1:

            # datos.sort(key=lambda x: (x.fldNSample, x.fkDispositivoSensor))
            datosX = [objeto for objeto in datos if objeto.dispositivoSensor.fkSensor < 25]
            datosX.sort(key=lambda x: (x.fldNSample, x.fkDispositivoSensor))
            datosY = [x for x in datos if x.dispositivoSensor.fkSensor > 25]
            datosY.sort(key=lambda x: (x.fldNSample, x.fkDispositivoSensor))
            for i in range(len(datosX)):
                only_data.append(datosX[i].fldFValor)
                only_data.append(datosY[i].fldFValor)

            labels.append(capture.owner.fldSLabel)
            np_data = np.resize(only_data, (1, len(only_data)))
            df_length = len(df)
            df.loc[df_length] = np_data[0].tolist()
    pd.set_option('display.max_columns', columns * rows)
    df['label'] = labels
    return df


def saveModel():
    pass
