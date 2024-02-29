import os
import random
from math import floor, ceil

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
from tensorflow.keras.layers import Input
from tensorflow.keras.layers import concatenate
from tensorflow.python.keras import Model

from app.models import tbl_version

# CONFIG
DATA_FREQ = 20
SENS_NUMBER = 6


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
    # cnn.add(Dense(output_size, activation='softmax'))
    cnn.add(Dense(output_size, activation='sigmoid'))

    # Generate name
    model_uuid = 'static/mpu_' + str(uuid.uuid1()) + '.h5'
    cnn.compile(optimizer=SGD(learning_rate=0.0045), loss='binary_crossentropy', metrics=['accuracy'])

    # cnn.compile(optimizer=SGD(learning_rate=0.0045), loss='categorical_crossentropy', metrics=['accuracy'])
    cnn.save(model_uuid)
    return model_uuid

def train_model2(modelo, dfs, labels, frecuencias, cantidad, nFrecuencias, version_last):
    num_epoch = 500

    # input_shape = Input(shape=(modelo.fldNDuration*20, 6, 1))
    models = []
    for i in range(nFrecuencias):
        input_shape = Input(shape=(modelo.fldNDuration*frecuencias[i], cantidad[i], 1))
        x = Conv2D(32, 5, activation='relu', padding='same')(input_shape)
        x = Conv2D(16, 3, activation='relu', padding='same')(x)
        x = MaxPool2D(pool_size=(2, 2))(x)
        x = Flatten()(x)
        x = Model(inputs=input_shape, outputs=x)
        models.append(x)

    if nFrecuencias <= 1:
        combined = models[0].output
    else:
        combined = concatenate([x.output for x in models], axis=-1)
    print("Hoja")
    z = Dense(60, activation="tanh")(combined)
    z = Dense(2, activation="sigmoid")(z)
    print("Capas")
    model = Model(inputs=[x.input for x in models], outputs=z)
    print("modelo")
    model_uuid = 'static/mul_' + str(uuid.uuid1()) + '.h5'
    model.compile(optimizer=SGD(learning_rate=0.0045), loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    print("compile")
    X_train, X_test, y_train, y_test = split_normalize_data2(modelo, dfs, cantidad, frecuencias, nFrecuencias, labels)
    print("normalize")
    history = model.fit(X_train, y_train, batch_size=32, shuffle=True, epochs=num_epoch, validation_data=(X_test, y_test), verbose=1)
    print("fit")
    model.save(model_uuid)
    evaluation = model.evaluate(X_test, y_test)
    print("evaluate")
    version = tbl_version(fldSUrl=model_uuid,
                          fldFAccuracy=float(evaluation[1]),
                          fldNEpoch=num_epoch,
                          fldFLoss=float(evaluation[0]),
                          fldSOptimizer='SGD',
                          fldFLearningRate=0.0045)

    return version

def split_normalize_data2(model, dfs, cantidades, frecuencias, nFrecuencias, labels):
    label_enc = LabelEncoder()
    label_enc.fit([x.fldSLabel for x in model.movements])
    y = label_enc.transform(labels)
    X_trains = []
    X_tests = []
    for i in range(nFrecuencias):
        X_trains.append([])
        X_tests.append([])
    Y_trains = []
    Y_tests = []
    lista = list(range(len(labels)))
    random.shuffle(lista)
    lTrain = lista[0:floor(len(lista)*0.8)]
    lTest = lista[floor(len(lista)*0.8):len(lista)]

    for index in lTrain:
        Y_trains.append(y[index])
        for i in range(len(dfs)):
            X_trains[i].append(dfs[i].iloc[index])
    for index in lTest:
        Y_tests.append(y[index])
        for i in range(len(dfs)):
            X_tests[i].append(dfs[i].iloc[index])
    for i in range(nFrecuencias):
        X_trains[i] = np.array(X_trains[i]).reshape(len(Y_trains), model.fldNDuration*frecuencias[i], cantidades[i], 1)
        X_tests[i] = np.array(X_tests[i]).reshape(len(Y_tests), model.fldNDuration*frecuencias[i], cantidades[i], 1)
    #     parcial = [X_trains[i:i]]
    #     X_trains = X_trains.to_numpy().reshape(len(lTrain), model.fldNDuration * frecuencias[i], cantidades[i], 1)
    #     X_tests = X_tests.to_numpy().reshape(len(lTest), model.fldNDuration * frecuencias[i], cantidades[i], 1)

    return X_trains, X_tests, np.array(Y_trains), np.array(Y_tests)

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


def generate_columns_index(end, sens):
    columns_list = list(range(0, end))
    for i in range(0, len(columns_list), sens):
        columns_list[i] = 'ac' + str(columns_list[i])
        columns_list[i + 1] = 'ac' + str(columns_list[i + 1])
        columns_list[i + 2] = 'ac' + str(columns_list[i + 2])
        columns_list[i + 3] = 'gy' + str(columns_list[i + 3])
        columns_list[i + 4] = 'gy' + str(columns_list[i + 4])
        columns_list[i + 5] = 'gy' + str(columns_list[i + 5])
    return columns_list


def data_adapter(model, captures):
    columns = len(model.dispositivos)
    rows = model.fldNDuration * DATA_FREQ
    columns_list = generate_columns_index(columns * rows, len(model.dispositivos))
    df = pd.DataFrame(columns=columns_list)
    # print(df)
    labels = []
    for capture in captures:
        datos = []
        for dato in capture.datos:
            datos.append(dato)
        datos_sorted_partial = sorted(datos, key=lambda muestra:muestra.fkDispositivoSensor)
        datos_sorted = sorted(datos_sorted_partial, key=lambda muestra: muestra.fldNSample)
        lista = []
        for data in datos_sorted:
            lista.append(data.fldFValor)
        labels.append(capture.owner.fldSLabel)
        np_data = np.resize(lista, (1, len(lista)))
        df_length = len(df)
        df.loc[df_length] = np_data[0].tolist()
    pd.set_option('display.max_columns', columns * rows)
    df['label'] = labels
    return df

def data_adapter2(model, captures):
    frecuencias = []
    cantidad = []
    for d in model.dispositivos:
        if(d.sensor.fldNFrecuencia not in frecuencias):
            frecuencias.append(d.sensor.fldNFrecuencia)
            cantidad.append(1)
        else:
            index = frecuencias.index(d.sensor.fldNFrecuencia)
            cantidad[index] += 1
    nFrecuencias = len(frecuencias)
    columns_lists = []
    for i in range(nFrecuencias):
        column_list = []
        for j in range(frecuencias[i]*model.fldNDuration):
            for k in range(cantidad[i]):
                column_list.append("D"+str(k)+"S"+str(j))
        columns_lists.append(column_list)
    # columns = len(model.dispositivos)
    # rows = model.fldNDuration * DATA_FREQ
    # columns_list = generate_columns_index(columns * rows, len(model.dispositivos))
    dfs = []
    for cl in columns_lists:
        dfs.append(pd.DataFrame(columns=cl))
    # print(df)
    labels = []
    for capture in captures:
        datos = []
        listas = []
        for i in range(nFrecuencias):
            datos.append([])
            listas.append([])
        for dato in capture.datos:
            index = frecuencias.index(dato.dispositivoSensor.sensor.fldNFrecuencia)
            datos[index].append(dato)
        for i in range(len(datos)):
            datos_sorted_partial = sorted(datos[i], key=lambda muestra:muestra.fkDispositivoSensor)
            datos_sorted = sorted(datos_sorted_partial, key=lambda muestra: muestra.fldNSample)
            listas[i] = [d.fldFValor for d in datos_sorted]
            np_data = np.resize(listas[i], (1, len(listas[i])))
            df_length = len(dfs[i])
            dfs[i].loc[df_length] = np_data[0].tolist()
        labels.append(capture.owner.fldSLabel)
    # pd.set_option('display.max_columns', len(columns_list))
    return dfs, labels, frecuencias, cantidad, nFrecuencias

def data_adapter_old(model, captures):
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
