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
from tensorflow.keras import Model

from app.models import tbl_version


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


def train_model3(modelo, dfs, labels, frecuencias, cantidad, nFrecuencias, version_last):
    num_epoch = 500
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
    z = Dense(3, activation="linear")(z)
    print("Capas")
    model = Model(inputs=[x.input for x in models], outputs=z)
    print("modelo")
    model_uuid = 'static/mulR_' + str(uuid.uuid1()) + '.h5'
    # model.compile(optimizer=SGD(learning_rate=0.0045), loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    model.compile(optimizer=SGD(learning_rate=0.0045), loss='mean_squared_error', metrics=['accuracy'])
    print("compile")
    X_train, X_test, y_train, y_test = split_normalize_data3(modelo, dfs, cantidad, frecuencias, nFrecuencias, labels)
    print("normalize")
    history = model.fit(X_train, y_train, batch_size=32, shuffle=True, epochs=num_epoch, validation_data=(X_test, y_test), verbose=1)
    print("fit")
    model.save(model_uuid)
    return model_uuid


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

def split_normalize_data3(model, dfs, cantidades, frecuencias, nFrecuencias, labels):
    # label_enc = LabelEncoder()
    # label_enc.fit([x.fldSLabel for x in model.movements])
    #y = label_enc.transform(labels)
    y = labels
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


def data_adapter3(model, captures):
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
            #dfs[i].loc[df_length] = np_data[0].tolist()
        #labels.append([capture.fldFStart, capture.fldFMid, capture.fldFEnd])
        otro(nFrecuencias, capture, frecuencias, dfs, labels, cantidad)
        otro(nFrecuencias, capture, frecuencias, dfs, labels, cantidad)
        otro(nFrecuencias, capture, frecuencias, dfs, labels, cantidad)
        otro(nFrecuencias, capture, frecuencias, dfs, labels, cantidad)
        otro(nFrecuencias, capture, frecuencias, dfs, labels, cantidad)
    # pd.set_option('display.max_columns', len(columns_list))
    return dfs, labels, frecuencias, cantidad, nFrecuencias

def otro(nFrecuencias, capture, frecuencias, dfs, labels, cantidad):
    datos = []
    listas = []
    for i in range(nFrecuencias):
        datos.append([])
        listas.append([])
    reandVal = random.randint(-25, 25)/100
    if reandVal == 0:
        reandVal = 0.1
    if reandVal > (1-capture.fldFEnd):
        reandVal = 0
    if -1*reandVal > capture.fldFStart:
        reandVal = 0
    for dato in capture.datos:
        index = frecuencias.index(dato.dispositivoSensor.sensor.fldNFrecuencia)
        datos[index].append(dato)
    for i in range(len(datos)):
        datos_sorted_partial = sorted(datos[i], key=lambda muestra: muestra.fkDispositivoSensor)
        datos_sorted = sorted(datos_sorted_partial, key=lambda muestra: muestra.fldNSample)
        listas[i] = [d.fldFValor for d in datos_sorted]
        desplazamiento = round(frecuencias[i] * reandVal)
        if reandVal > 0:
            for j in range(abs(desplazamiento)):
                for l in range(cantidad[i]):
                    for k in range(len(listas[i])-1):
                        listas[i][-1 * k] = listas[i][(-1 * k)-1]
                    listas[i][0] = 0.0
        else:
            for j in range(abs(desplazamiento)):
                for l in range(cantidad[i]):
                    for k in range(len(listas[i])-1):
                        listas[i][k] = listas[i][k+1]
                    listas[i][-1] = 0.0
        np_data = np.resize(listas[i], (1, len(listas[i])))
        df_length = len(dfs[i])
        dfs[i].loc[df_length] = np_data[0].tolist()
    labels.append([max(min(capture.fldFStart + reandVal, 1), 0), max(min(capture.fldFMid + reandVal, 1), 0), max(min(capture.fldFEnd + reandVal, 1), 0)])


def generar_negativos(dfs, labels, nombre):
    negativos = len([x for x in labels if x != nombre])
    positivos = len([x for x in labels if x == nombre])
    lpositivos = [i for i, valor in enumerate(labels) if valor == nombre]
    repeticiones = round(positivos/negativos) - 1
    if repeticiones > 0:
        for i in range(negativos+positivos):
            if labels[i] != nombre:
                for j in range(repeticiones):
                    for k in range(len(dfs)):
                        dfs[k].loc[len(dfs[k])] = dfs[k].loc[i]
                        for l in range(len(dfs[k].iloc[i])):
                            std = abs(1 - np.std(dfs[k].iloc[lpositivos, l]))
                            factor = random.uniform(1-std, 1+std)
                            dfs[k].iloc[len(dfs[k])-1, l] *= factor
                    labels.append(labels[i])
    return dfs, labels

