import os
import pickle
import sys
from datetime import datetime
from typing import List, Any

from fastdtw import fastdtw
import tensorflow as tf
import pandas as pd
import numpy as np
import uuid

from joblib import parallel_backend
from matplotlib import pyplot as plt
from numpy import median, std, mean
from scipy.spatial.distance import euclidean, squareform
from scipy.stats import mode
from sklearn import preprocessing
from sklearn.metrics import classification_report
from sklearn.neighbors import KNeighborsClassifier
from tensorflow.keras.optimizers import SGD
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Flatten, Dense
from tensorflow.keras.layers import Conv2D, MaxPool2D
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from app.models import tbl_version

# CONFIG
from app.models.tbl_mensajesInferencia import tbl_mensajesInferencia
from app.schemas import mpu
from app.schemas.mpu import MpuEstadisticas

DATA_FREQ = 20
SENS_NUMBER = 6


class knndtw(object):

    def __init__(self, n_neighbors=5, n_weights='uniform'):
        self.n_neighbors = n_neighbors
        self.n_weights = n_weights
        with parallel_backend("multiprocessing", n_jobs=-1):
            self.knn = KNeighborsClassifier(self.n_neighbors, metric=self.dtw, weights=self.n_weights, n_jobs=-1)

    def fit(self, X, y):
        self.X = X
        self.y = y
        self.knn.fit(X, y)

    def dtw(self, t1, t2):
        return fastdtw(t1, t2)[0]

    def predict(self, X, i):
        return self.knn.predict(X, i)

    def predict_proba(self, X):
        return self.knn.predict_proba(X)


def scale_data(data, target):
    # df_pre = data.drop('Unnamed: 0', axis=1)

    # Normalization
    df_pre = data
    scaler = StandardScaler()
    # X = df_pre.drop(target,axis=1)
    X = df_pre.drop('label', axis=1)
    x_norm = scaler.fit_transform(X.values)
    df_norm = pd.DataFrame(data=x_norm, columns=X.columns)
    df_norm[target] = df_pre[target]
    df_pre = df_norm.copy()

    # MIN-MAX
    min_max_scaler = preprocessing.MinMaxScaler(feature_range=(0, 1))
    X = df_pre.drop(target, axis=1)
    x_scaled = min_max_scaler.fit_transform(X.values)
    df_scaled = pd.DataFrame(data=x_scaled, columns=X.columns)
    df_scaled[target] = df_pre[target]
    df_pre = df_scaled.copy()

    # df_pre.loc[(df_pre[target] == 'lunches'),target] = 1
    # df_pre.loc[(df_pre[target] == 'other'),target] = 0

    return df_pre


def correct_incorrect(data, target, label):
    # pclasss = 1
    pclass = label

    df_correct = data.loc[data[target] == pclass].drop(target, axis=1)
    #print("Correct repetitions: {}".format(df_correct.shape[0]))

    df_incorrect = data.loc[data[target] != pclass].drop(target, axis=1)
    #print("Incorrect repetitions: {}".format(df_incorrect.shape[0]))

    return df_correct, df_incorrect


def remove_outliers(data, percentile):
    # Keep samples below the percentile

    return data[data < data.quantile(percentile)].dropna()


def rolling_window(data, window_size):
    # Resample Rolling Window

    return data.T.rolling(window_size).mean().dropna().T


def normalizar(df, min, max):
    for data in df:
        data = (data - min)/(max - min)


def analize(mpus, db):
    # Leer archivos m
    start = datetime.now()
    objects = []
    with open('m_ac1.model', 'rb') as model:
        objects.append(pickle.load(model))
    with open('m_ac2.model', 'rb') as model:
        objects.append(pickle.load(model))
    with open('m_ac3.model', 'rb') as model:
        objects.append(pickle.load(model))
    with open('m_g1.model', 'rb') as model:
        objects.append(pickle.load(model))
    with open('m_g2.model', 'rb') as model:
        objects.append(pickle.load(model))
    with open('m_g3.model', 'rb') as model:
        objects.append(pickle.load(model))
    m_ac1 = objects[0].model
    m_ac2 = objects[1].model
    m_ac3 = objects[2].model
    m_g1 = objects[3].model
    m_g2 = objects[4].model
    m_g3 = objects[5].model
    fin = datetime.now()
    # print("LECTURA: "+str(fin-start))

    # Datos
    start = datetime.now()
    datos = []
    for mpu1 in mpus.mpu:
        #datos.append(mpu1.fldFAccX)
        #datos.append(mpu1.fldFAccY)
        #datos.append(mpu1.fldFAccZ)
        datos.append(((((mpu1.fldFAccX*4) - objects[0].datos.media) / objects[0].datos.std) - objects[0].datos.min) / (objects[0].datos.max - objects[0].datos.min))
        datos.append(((((mpu1.fldFAccY*4) - objects[1].datos.media) / objects[1].datos.std) - objects[1].datos.min) / (objects[1].datos.max - objects[1].datos.min))
        datos.append(((((mpu1.fldFAccZ*4) - objects[2].datos.media) / objects[2].datos.std) - objects[2].datos.min) / (objects[2].datos.max - objects[2].datos.min))
        #datos.append(mpu1.fldFGyrX)
        #datos.append(mpu1.fldFGyrY)
        #datos.append(mpu1.fldFGyrZ)
        datos.append(((((mpu1.fldFGyrX*1000) - objects[3].datos.media) / objects[3].datos.std) - objects[3].datos.min) / (objects[3].datos.max - objects[3].datos.min))
        datos.append(((((mpu1.fldFGyrY*1000) - objects[4].datos.media) / objects[4].datos.std) - objects[4].datos.min) / (objects[4].datos.max - objects[4].datos.min))
        datos.append(((((mpu1.fldFGyrZ*1000) - objects[5].datos.media) / objects[5].datos.std) - objects[5].datos.min) / (objects[5].datos.max - objects[5].datos.min))
    mov = pd.DataFrame(datos).T
    fin = datetime.now()
    # print("Datos: "+str(fin-start))

    start = datetime.now()
    start1 = datetime.now()
    label_new5 = m_ac1.predict(np.array(mov.iloc[:, ::6]), 1)
    fin1 = datetime.now()
    # print("Predict proba 1: "+str(fin1-start1))
    start1 = datetime.now()
    proba_new5 = m_ac1.predict_proba(np.array(mov.iloc[:, ::6]))
    fin1 = datetime.now()
    # print("Predict 1: "+str(fin1-start1))
    start1 = datetime.now()
    label_new6 = m_ac2.predict(np.array(mov.iloc[:, 1::6]), 0)
    fin1 = datetime.now()
    # print("Predict proba 2: "+str(fin1-start1))
    start1 = datetime.now()
    proba_new6 = m_ac2.predict_proba(np.array(mov.iloc[:, 1::6]))
    fin1 = datetime.now()
    # print("Predict 2: "+str(fin1-start1))
    start1 = datetime.now()
    label_new7 = m_ac3.predict(np.array(mov.iloc[:, 2::6]), 0)
    fin1 = datetime.now()
    # print("Predict proba 3: "+str(fin1-start1))
    start1 = datetime.now()
    proba_new7 = m_ac3.predict_proba(np.array(mov.iloc[:, 2::6]))
    fin1 = datetime.now()
    # print("Predict 3: "+str(fin1-start1))
    start1 = datetime.now()
    label_new8 = m_g1.predict(np.array(mov.iloc[:, 3::6]), 0)
    fin1 = datetime.now()
    # print("Predict proba 4: "+str(fin1-start1))
    start1 = datetime.now()
    proba_new8 = m_g1.predict_proba(np.array(mov.iloc[:, 3::6]))
    fin1 = datetime.now()
    # print("Predict 4: "+str(fin1-start1))
    start1 = datetime.now()
    label_new9 = m_g2.predict(np.array(mov.iloc[:, 4::6]), 0)
    fin1 = datetime.now()
    # print("Predict proba 5: "+str(fin1-start1))
    start1 = datetime.now()
    proba_new9 = m_g2.predict_proba(np.array(mov.iloc[:, 4::6]))
    fin1 = datetime.now()
    # print("Predict 5: "+str(fin1-start1))
    start1 = datetime.now()
    label_new10 = m_g3.predict(np.array(mov.iloc[:, 5::6]), 0)
    fin1 = datetime.now()
    # print("Predict proba 6: "+str(fin1-start1))
    start1 = datetime.now()
    proba_new10 = m_g3.predict_proba(np.array(mov.iloc[:, 5::6]))
    fin1 = datetime.now()
    # print("Predict 6: "+str(fin1-start1))
    fin = datetime.now()
    # print("Inferencia: "+str(fin-start))

    start = datetime.now()
    list_count = []
    count = 0
    sensores_nombre = ["AccX", "AccY", "AccZ", "GyrX", "GyrY", "GyrZ"]
    for i in range(len(label_new5)):
        for j in range(5, 11):
            label = eval('label_new' + str(j))
            prob = eval('proba_new' + str(j))
            if label == "other" or label == "Other":
                count += (1 - prob[0][0])
            else:
                count += prob[0][0]
            list_count.append((sensores_nombre[j-5], label[i], prob[0][0]))
    count = (count/6)*100
    fin = datetime.now()
    # print("Respuesta: "+str(fin-start))
    df_val = pd.DataFrame(list_count, columns=['Sensor', 'Label', 'Prob'])

    informes = []
    start = datetime.now()
    for i in range(0, 6):
        t = generate_Single(objects[i], mov, i)
        informes.append(t)
    result = pd.concat(informes)
    result = result.sort_values(by='Value')[::-1]
    result = result.reset_index()
    result = result.drop("index", axis=1)
    fin = datetime.now()
    # print("Analisis: "+str(fin-start))

    #print(df_val.to_string()+"\n\n"+result.to_string()+"\n\nCorrect in "+str(count[0])+"%")
    res = resultados(result, db)
    return res


def resultados(result, db):
    dic = {}
    for n in result.sensor.unique():
        dic[n] = [0, 0, [0, 0, 0, 0], [0, 0, 0, 0]]
    for index, row in result.iterrows():
        dic[row.sensor][0] += row.Value
        dic[row.sensor][1] += row.P_N
        dic[row.sensor][2][int(row.Instant_time / (40 / 4))] += row.Value
        dic[row.sensor][3][int(row.Instant_time / (40 / 4))] += row.P_N
    max(dic, key=dic.get)
    max_sensors = [[0, 0, 0, ""], [0, 0, 0, ""], [0, 0, 0, ""]]
    for k in dic.keys():
        max_v = max(dic[k][2])
        indx = dic[k][2].index(max_v)
        max_p = dic[k][3][indx]
        sensor_n = k
        for i in range(3):
            if (max_sensors[i][0] < max_v):
                max_sensors.insert(i, [max_v, max_p, indx, sensor_n])
                max_sensors = max_sensors[:-1]
                break
    print(max_sensors)
    # PARTE 2
    tabla_sensores = []
    for k in dic.keys():
        counter = 0
        for e in dic[k][2]:
            if e > 0.5:
                counter += 1
        if counter > 2:
            sensor = []
            # El sensor
            sensor.append(k)  # dispositivo
            sensor.append(k)  # magnitud
            sensor.append(k)  # eje
            sensor.append('tt')
            for er in dic[k][2]:
                if er > 1:
                    sensor.append('++')
                    tabla_sensores.append(sensor)
                    break
        else:
            for er, i in zip(dic[k][2], range(4)):
                sensor = []
                if er > 0.1:
                    sensor.append(k)  # dispositivo
                    sensor.append(k)  # magnitud
                    sensor.append(k)  # eje
                    sensor.append('t' + str(i))
                    if er > 1 and dic[k][3][i] > 0:
                        sensor.append('++')
                    elif er > 1 and dic[k][3][i] < 0:
                        sensor.append('--')
                    elif er > 0 and dic[k][3][i] < 0:
                        sensor.append('-')
                    else:
                        sensor.append('+')
                    tabla_sensores.append(sensor)
        print(tabla_sensores)
        # Escribir mensajes
    res = tabla_sensores[:3]
    respuesta = ""
    for re in res:
        sensor = int(re[0] / 4) + 1
        eje = int((re[0]-1) % 3) + 1
        msj = db.query(tbl_mensajesInferencia).filter(tbl_mensajesInferencia.fldNSensor == sensor).filter(tbl_mensajesInferencia.fldNEje == eje).first()
        if re[3] == 't0':
            tiempo = "al principio del movimeinto"
        elif re[3] == 't1':
            tiempo = "antes de la mitad del movimiento"
        elif re[3] == 't2':
            tiempo = "despues de la mitad del movimiento"
        elif re[3] == 't3':
            tiempo = "al final del movimiento"
        else:
            tiempo = "en todo el movimiento"
        if re[4] == '++':
            intensidad = "Reducir mucho"
        elif re[4] == '+':
            intensidad = "Reducir un poco"
        elif re[4] == '-':
            intensidad = "Aumentar un poco"
        elif re[4] == '--':
            intensidad = "Aumentar mucho"
        else:
            intensidad = ''
        respuesta = respuesta + intensidad + ' ' + msj.fldSMensaje + ' ' + tiempo + ".\n"
    return respuesta


def completarModelo(mov_target, pclass, df_mov, index):
    df_mov_pre = scale_data(df_mov, mov_target)
    df_mov_sensor = df_mov_pre[df_mov_pre.columns[index::6]]
    df_mov_sensor[mov_target] = df_mov_pre[mov_target]
    df_mov_sensor_correct, df_mov_sensor1_incorrect = correct_incorrect(df_mov_sensor, mov_target, pclass)
    df_mov_sensor_clean = remove_outliers(df_mov_sensor_correct, 0.90)
    sref, sref_upper, sref_lower = get_normal_repetition(df_mov_sensor_clean)
    return sref, sref_upper, sref_lower

def joinMOV(mov_target, pclass, df_mov): # joinMOV('label', 'curl lateral mancuerna', dataframe)
    # Scale data
    df_mov_pre = scale_data(df_mov, mov_target)

    # Split sensors
    df_mov_sensor1 = df_mov_pre[df_mov_pre.columns[::6]]
    df_mov_sensor1[mov_target] = df_mov_pre[mov_target]
    df_mov_sensor2 = df_mov_pre[df_mov_pre.columns[1::6]]
    df_mov_sensor2[mov_target] = df_mov_pre[mov_target]
    df_mov_sensor3 = df_mov_pre[df_mov_pre.columns[2::6]]
    df_mov_sensor3[mov_target] = df_mov_pre[mov_target]
    df_mov_sensor4 = df_mov_pre[df_mov_pre.columns[3::6]]
    df_mov_sensor4[mov_target] = df_mov_pre[mov_target]
    df_mov_sensor5 = df_mov_pre[df_mov_pre.columns[4::6]]
    df_mov_sensor5[mov_target] = df_mov_pre[mov_target]
    df_mov_sensor6 = df_mov_pre[df_mov_pre.columns[5::6]]
    df_mov_sensor6[mov_target] = df_mov_pre[mov_target]

    # Split correct/incorrect data
    df_mov_sensor1_correct, df_mov_sensor1_incorrect = correct_incorrect(df_mov_sensor1, mov_target, pclass)
    df_mov_sensor2_correct, df_mov_sensor2_incorrect = correct_incorrect(df_mov_sensor2, mov_target, pclass)
    df_mov_sensor3_correct, df_mov_sensor3_incorrect = correct_incorrect(df_mov_sensor3, mov_target, pclass)
    df_mov_sensor4_correct, df_mov_sensor4_incorrect = correct_incorrect(df_mov_sensor4, mov_target, pclass)
    df_mov_sensor5_correct, df_mov_sensor5_incorrect = correct_incorrect(df_mov_sensor5, mov_target, pclass)
    df_mov_sensor6_correct, df_mov_sensor6_incorrect = correct_incorrect(df_mov_sensor6, mov_target, pclass)

    # Remove outliers
    df_mov_sensor1_clean = remove_outliers(df_mov_sensor1_correct, 0.90)
    df_mov_sensor2_clean = remove_outliers(df_mov_sensor2_correct, 0.90)
    df_mov_sensor3_clean = remove_outliers(df_mov_sensor3_correct, 0.90)
    df_mov_sensor4_clean = remove_outliers(df_mov_sensor4_correct, 0.90)
    df_mov_sensor5_clean = remove_outliers(df_mov_sensor5_correct, 0.90)
    df_mov_sensor6_clean = remove_outliers(df_mov_sensor6_correct, 0.90)

    return str(generateInforme(df_mov_sensor1_clean, df_mov_sensor2_clean, df_mov_sensor3_clean, df_mov_sensor4_clean, df_mov_sensor5_clean,
                          df_mov_sensor6_clean,
                          df_mov_sensor1_correct, df_mov_sensor2_correct, df_mov_sensor3_correct, df_mov_sensor4_correct, df_mov_sensor5_correct,
                          df_mov_sensor6_correct))


def dtw_distance(s_ref, df_signals):
    '''
    Calculates the dtw distance between the reference signal and the dataset of signals passed
    '''

    distance_array = []

    # Format data shape
    s_ref = s_ref.values.reshape(1, -1)

    # Calculate distances
    for index, row in df_signals.iterrows():
        s_comp = row.values.reshape(1, -1)
        distance, path = fastdtw(s_ref, s_comp, dist=euclidean)
        distance_array.append(distance)

    return distance_array


def signals_diff_calculation(sref, sref_upper, sref_lower, s_rep):
    s_diff = s_rep.copy()
    b = []
    for t in s_rep:
        if (s_rep[t] > sref_upper[t]).item():
            s_diff[t] = np.abs(s_rep[t] - sref_upper[t])
            b.append(1)
        elif (s_rep[t] < sref_lower[t]).item():
            s_diff[t] = np.abs(s_rep[t] - sref_lower[t])
            b.append(-1)
        else:
            s_diff[t] = 0
            b.append(0)

    return s_diff, b


def get_normal_repetition(clean_data):
    sref = clean_data.mean()
    sref_std = clean_data.std()
    sref_upper = sref + sref_std
    sref_lower = sref - sref_std
    return sref, sref_upper, sref_lower


def get_error(sref, sref_upper, sref_lower, rep):
    # Calculate distance from reference rep
    sdiff = signals_diff_calculation(sref, sref_upper, sref_lower, rep)

    return sdiff


def show_error(sdiff, b, e):
    transposed = sdiff.T
    transposed["P_N"] = b

    # print(transposed.columns)
    transposed
    transposed = transposed.reset_index()
    transposed = transposed.drop("index", axis=1)
    transposed.rename(columns={transposed.columns[0]: 'Value'}, inplace=True)
    t = transposed.sort_values(by=transposed.columns[0])[::-1]
    t = t.reset_index()
    t.rename(columns={"index": 'Instant_time'}, inplace=True)
    t["sensor"] = e
    # print(t)
    return t


def plot_data(sref, sref_upper, sref_lower, sdiff, rep):
  fig, ax1 = plt.subplots(figsize=(14,6))
  plt.xticks(rotation=90)
  #plt.title('S1' + ': Wrong far Lunge (Distance = {})'.format(np.round(distance,2)))

  ax1.plot(rep.squeeze(axis=0),color='red',label='rep')
  ax1.plot(sref, color='darkblue',label='Reference (mean)', linewidth=1)
  plt.fill_between(sref.index, sref_upper, sref_lower, color='skyblue')

  ax2 = ax1.twinx()
  ax2.bar(sdiff.squeeze(axis=0).index,sdiff.squeeze(axis=0),color='orange',label='Lunge Close')
  ax2.set_ylabel('Euclidean difference', color='orange')

  ax1.legend()
  ax1.set_xlabel('Time of sample')
  ax1.set_ylabel('Value of the sensors scaled')
  ax1.set_ylim(0,1)
  ax2.set_ylim(0, 1)
  plt.show()


def generate_Single(modelo, datos, index):
    sref = modelo.sref
    sref_upper = modelo.sref_upper
    sref_lower = modelo.sref_lower
    rep = datos.iloc[0, index::6].to_frame()
    # rep.set_index(sref.get_index())
    #sref = sref.reset_index(drop=True)
    # sref = sref.drop(axis=0)
    #sref_upper = sref_upper.reset_index().drop(axis=0)
    #sref_lower = sref_lower.reset_index().drop(axis=0)
    rep = rep.reset_index(drop=True)
    error, b = get_error(sref, sref_upper, sref_lower, rep.T)
    t = show_error(error, b, index+1)
    #plot_data(sref, sref_upper, sref_lower, error, rep.T)
    return t


def generateInforme(df_mov_sensor1_clean, df_mov_sensor2_clean, df_mov_sensor3_clean, df_mov_sensor4_clean, df_mov_sensor5_clean,
                    df_mov_sensor6_clean,
                    df_mov_sensor1_correct, df_mov_sensor2_correct, df_mov_sensor3_correct, df_mov_sensor4_correct, df_mov_sensor5_correct,
                    df_mov_sensor6_correct):
    sref5, sref_upper5, sref_lower5 = get_normal_repetition(df_mov_sensor1_clean)
    rep5 = df_mov_sensor1_correct.iloc[6].to_frame()
    error5, b5 = get_error(sref5, sref_upper5, sref_lower5, rep5.T)
    t5 = show_error(error5, b5)

    sref6, sref_upper6, sref_lower6 = get_normal_repetition(df_mov_sensor2_clean)
    rep6 = df_mov_sensor2_correct.iloc[6].to_frame()
    error6, b6 = get_error(sref6, sref_upper6, sref_lower6, rep6.T)
    t6 = show_error(error6, b6)

    sref7, sref_upper7, sref_lower7 = get_normal_repetition(df_mov_sensor3_clean)
    rep7 = df_mov_sensor3_correct.iloc[6].to_frame()
    error7, b7 = get_error(sref7, sref_upper7, sref_lower7, rep7.T)
    t7 = show_error(error7, b7)

    sref8, sref_upper8, sref_lower8 = get_normal_repetition(df_mov_sensor4_clean)
    rep8 = df_mov_sensor4_correct.iloc[6].to_frame()
    error8, b8 = get_error(sref8, sref_upper8, sref_lower8, rep8.T)
    t8 = show_error(error8, b8)

    sref9, sref_upper9, sref_lower9 = get_normal_repetition(df_mov_sensor5_clean)
    rep9 = df_mov_sensor5_correct.iloc[6].to_frame()
    error9, b9 = get_error(sref9, sref_upper9, sref_lower9, rep9.T)
    t9 = show_error(error9, b9)

    sref10, sref_upper10, sref_lower10 = get_normal_repetition(df_mov_sensor6_clean)
    rep10 = df_mov_sensor6_correct.iloc[6].to_frame()
    error10, b10 = get_error(sref10, sref_upper10, sref_lower10, rep10.T)
    t10 = show_error(error10, b10)

    result = pd.concat([t5, t6, t7, t8, t9, t10])
    result = result.sort_values(by='Value')[::-1]
    result = result.reset_index()
    result = result.drop("index", axis=1)

    return result


class ModeloKNN(object):
    def __init__(self, model, sref, sref_upper, sref_lower, datos):
        self.model = model
        self.sref = sref
        self.sref_upper = sref_upper
        self.sref_lower = sref_lower
        self.datos = datos
    model: Any
    sref: Any
    sref_upper: Any
    sref_lower: Any
    datos: Any



class KnnDtw(object):
    """K-nearest neighbor classifier using dynamic time warping
    as the distance measure between pairs of time series arrays

    Arguments
    ---------
    n_neighbors : int, optional (default = 5)
        Number of neighbors to use by default for KNN

    max_warping_window : int, optional (default = infinity)
        Maximum warping window allowed by the DTW dynamic
        programming function

    subsample_step : int, optional (default = 1)
        Step size for the timeseries array. By setting subsample_step = 2,
        the timeseries length will be reduced by 50% because every second
        item is skipped. Implemented by x[:, ::subsample_step]
    """

    def __init__(self, n_neighbors=5, max_warping_window=10000, subsample_step=1):
        self.n_neighbors = n_neighbors
        self.max_warping_window = max_warping_window
        self.subsample_step = subsample_step

    def fit(self, x, l):
        self.x = x
        self.l = l

    def _dtw_distance(self, ts_a, ts_b, d = lambda x,y: abs(x-y)):
        """Returns the DTW similarity distance between two 2-D
        timeseries numpy arrays.

        Arguments
        ---------
        ts_a, ts_b : array of shape [n_samples, n_timepoints]
            Two arrays containing n_samples of timeseries data
            whose DTW distance between each sample of A and B
            will be compared

        d : DistanceMetric object (default = abs(x-y))
            the distance measure used for A_i - B_j in the
            DTW dynamic programming function

        Returns
        -------
        DTW distance between A and B
        """

        # Create cost matrix via broadcasting with large int
        ts_a, ts_b = np.array(ts_a), np.array(ts_b)
        M, N = len(ts_a), len(ts_b)
        cost = sys.maxsize * np.ones((M, N)) # change maxint with maxsize

        # Initialize the first row and column
        cost[0, 0] = d(ts_a[0], ts_b[0])
        for i in range(1, M): #range is not defined
            cost[i, 0] = cost[i-1, 0] + d(ts_a[i], ts_b[0])

        for j in range(1, N):
            cost[0, j] = cost[0, j-1] + d(ts_a[0], ts_b[j])

         # Populate rest of cost matrix within window
        for i in range(1, M):
            for j in range(max(1, i - self.max_warping_window),
                            min(N, i + self.max_warping_window)):
                choices = cost[i - 1, j - 1], cost[i, j-1], cost[i-1, j]
                cost[i, j] = min(choices) + d(ts_a[i], ts_b[j])

        # Return DTW distance given window
        return cost[-1, -1]

    def _dist_matrix(self, x, y):
        """Computes the M x N distance matrix between the training
        dataset and testing dataset (y) using the DTW distance measure

        Arguments
        ---------
        x : array of shape [n_samples, n_timepoints]

        y : array of shape [n_samples, n_timepoints]

        Returns
        -------
        Distance matrix between each item of x and y with
            shape [training_n_samples, testing_n_samples]
        """

        # Compute the distance matrix
        dm_count = 0

        # Compute condensed distance matrix (upper triangle) of pairwise dtw distances
        # when x and y are the same array
        if(np.array_equal(x, y)):
            x_s = np.shape(x)
            dm = np.zeros((x_s[0] * (x_s[0] - 1)) // 2, dtype=np.double)


            for i in range(0, x_s[0] - 1):
                for j in range(i + 1, x_s[0]):
                    dm[dm_count] = self._dtw_distance(x[i, ::self.subsample_step],
                                                      y[j, ::self.subsample_step])

                    dm_count += 1

            # Convert to squareform
            dm = squareform(dm)
            return dm

        # Compute full distance matrix of dtw distnces between x and y
        else:
            x_s = np.shape(x)
            y_s = np.shape(y)
            dm = np.zeros((x_s[0], y_s[0]))
            dm_size = x_s[0]*y_s[0]


            for i in range(0, x_s[0]):
                for j in range(0, y_s[0]):
                    dm[i, j] = self._dtw_distance(x[i, ::self.subsample_step],
                                                  y[j, ::self.subsample_step])
                    # Update progress bar
                    dm_count += 1

            return dm

    def predict(self, x):
        """Predict the class labels or probability estimates for
        the provided data

        Arguments
        ---------
          x : array of shape [n_samples, n_timepoints]
              Array containing the testing data set to be classified

        Returns
        -------
          2 arrays representing:
              (1) the predicted class labels
              (2) the knn label count probability
        """

        dm = self._dist_matrix(x, self.x) # They have to be the same shape


        # Identify the k nearest neighbors
        knn_idx = dm.argsort()[:, :self.n_neighbors]

        # Identify k nearest labels
        knn_labels = self.l[knn_idx]

        # Model Label
        mode_data = mode(knn_labels, axis=1)
        mode_label = mode_data[0]
        mode_proba = mode_data[1]/self.n_neighbors

        return mode_label.ravel(), mode_proba.ravel()


def modelo(df, labelCorrect, accX, accY, accZ, gyrX, gyrY, gyrZ):
    y_df = df['label']
    labels = y_df.unique()

    X, X_val, Y, y_val = train_test_split(df, y_df, test_size=0.20, random_state=42, stratify=y_df)

    X = X.drop('label', axis=1)
    X = X.reset_index(drop=True)
    mov = X
    Y = Y.reset_index(drop=True)

    Xac1 = mov[mov.columns[::6]]
    x_train_ac1, x_test_ac1, y_train_ac1, y_test_ac1 = train_test_split(Xac1, Y, test_size=0.20, random_state=42, stratify=Y)
    Xac3 = mov[mov.columns[2::6]]
    x_train_ac3, x_test_ac3, y_train_ac3, y_test_ac3 = train_test_split(Xac3, Y, test_size=0.20, random_state=42, stratify=Y)
    Xac2 = mov[mov.columns[1::6]]
    x_train_ac2, x_test_ac2, y_train_ac2, y_test_ac2 = train_test_split(Xac2, Y, test_size=0.20, random_state=42, stratify=Y)
    Xg1 = mov[mov.columns[3::6]]
    x_train_g1, x_test_g1, y_train_g1, y_test_g1 = train_test_split(Xg1, Y, test_size=0.20, random_state=42, stratify=Y)
    Xg2 = mov[mov.columns[4::6]]
    x_train_g2, x_test_g2, y_train_g2, y_test_g2 = train_test_split(Xg2, Y, test_size=0.20, random_state=42, stratify=Y)
    Xg3 = mov[mov.columns[5::6]]
    x_train_g3, x_test_g3, y_train_g3, y_test_g3 = train_test_split(Xg3, Y, test_size=0.20, random_state=42, stratify=Y)

    m_ac1 = knndtw(n_neighbors=4)  # ,max_warping_window=10)
    m_ac1.fit(np.array(x_train_ac1).astype(np.float), np.array(y_train_ac1))
    label_ac1 = m_ac1.predict(np.array(x_test_ac1).astype(np.float))
    proba_ac1 = m_ac1.predict_proba(np.array(x_test_ac1).astype(np.float))
    # print(classification_report(label_ac1, x_test_ac1, target_names=labels))
    sref, sref_upper, sref_lower = completarModelo('label', labelCorrect, df, 0)
    modeloKnn = ModeloKNN(model=m_ac1, sref=sref, sref_upper=sref_upper, sref_lower=sref_lower, datos=accX)
    with open('m_ac1.model', 'wb') as model:
        pickle.dump(modeloKnn, model)

    m_ac2 = knndtw(n_neighbors=4)  # ,max_warping_window=10)
    m_ac2.fit(np.array(x_train_ac2).astype(np.float), np.array(y_train_ac2))
    label_ac2 = m_ac2.predict(np.array(x_test_ac2).astype(np.float))
    proba_ac2 = m_ac2.predict_proba(np.array(x_test_ac2).astype(np.float))
    # print(classification_report(label_ac2, x_test_ac2, target_names=labels))
    sref, sref_upper, sref_lower = completarModelo('label', labelCorrect, df, 1)
    modeloKnn = ModeloKNN(model=m_ac2, sref=sref, sref_upper=sref_upper, sref_lower=sref_lower, datos=accY)
    with open('m_ac2.model', 'wb') as model:
        pickle.dump(modeloKnn, model)

    m_ac3 = knndtw(n_neighbors=4)  # ,max_warping_window=10)
    m_ac3.fit(np.array(x_train_ac3).astype(np.float), np.array(y_train_ac3))
    label_ac3 = m_ac3.predict(np.array(x_test_ac3).astype(np.float))
    prova_ac3 = m_ac3.predict_proba(np.array(x_test_ac3).astype(np.float))
    # print(classification_report(label_ac3, x_test_ac3, target_names=labels))
    sref, sref_upper, sref_lower = completarModelo('label', labelCorrect, df, 2)
    modeloKnn = ModeloKNN(model=m_ac3, sref=sref, sref_upper=sref_upper, sref_lower=sref_lower, datos=accZ)
    with open('m_ac3.model', 'wb') as model:
        pickle.dump(modeloKnn, model)

    m_g1 = knndtw(n_neighbors=4)  # ,max_warping_window=10)
    m_g1.fit(np.array(x_train_g1).astype(np.float), np.array(y_train_g1))
    label_g1 = m_g1.predict(np.array(x_test_g1).astype(np.float))
    prova_g1 = m_g1.predict_proba(np.array(x_test_g1).astype(np.float))
    # print(classification_report(label_g1, x_test_g1, target_names=labels))
    sref, sref_upper, sref_lower = completarModelo('label', labelCorrect, df, 3)
    modeloKnn = ModeloKNN(model=m_g1, sref=sref, sref_upper=sref_upper, sref_lower=sref_lower, datos=gyrX)
    with open('m_g1.model', 'wb') as model:
        pickle.dump(modeloKnn, model)

    m_g2 = knndtw(n_neighbors=4)  # ,max_warping_window=10)
    m_g2.fit(np.array(x_train_g2).astype(np.float), np.array(y_train_g2))
    label_g2 = m_g2.predict(np.array(x_test_g2).astype(np.float))
    proba_g2 = m_g2.predict_proba(np.array(x_test_g2).astype(np.float))
    # print(classification_report(label_g2, x_test_g2, target_names=labels))
    sref, sref_upper, sref_lower = completarModelo('label', labelCorrect, df, 4)
    modeloKnn = ModeloKNN(model=m_g2, sref=sref, sref_upper=sref_upper, sref_lower=sref_lower, datos=gyrY)
    with open('m_g2.model', 'wb') as model:
        pickle.dump(modeloKnn, model)

    m_g3 = knndtw(n_neighbors=4)#,max_warping_window=10)
    m_g3.fit(np.array(x_train_g3).astype(np.float), np.array(y_train_g3))
    label_g3 = m_g3.predict(np.array(x_test_g3).astype(np.float))
    proba_g3 = m_g3.predict_proba(np.array(x_test_g3).astype(np.float))
    # print(classification_report(label_g3, x_test_g3, target_names=labels))
    sref, sref_upper, sref_lower = completarModelo('label', labelCorrect, df, 5)
    modeloKnn = ModeloKNN(model=m_g3, sref=sref, sref_upper=sref_upper, sref_lower=sref_lower, datos=gyrZ)
    with open('m_g3.model', 'wb') as model:
        pickle.dump(modeloKnn, model)


    def inferencia(mov):
        label_new5 = m_ac1.predict(np.array(mov[mov.columns[::6]]))
        proba_new5 = m_ac1.predict_proba(np.array(mov[mov.columns[::6]]))
        label_new6 = m_ac2.predict(np.array(mov[mov.columns[1::6]]))
        proba_new6 = m_ac2.predict_proba(np.array(mov[mov.columns[1::6]]))
        label_new7 = m_ac3.predict(np.array(mov[mov.columns[2::6]]))
        proba_new7 = m_ac3.predict_proba(np.array(mov[mov.columns[2::6]]))

        label_new8 = m_g1.predict(np.array(mov[mov.columns[3::6]]))
        proba_new8 = m_g1.predict_proba(np.array(mov[mov.columns[3::6]]))
        label_new9 = m_g2.predict(np.array(mov[mov.columns[4::6]]))
        proba_new9 = m_g2.predict_proba(np.array(mov[mov.columns[4::6]]))
        label_new10 = m_g3.predict(np.array(mov[mov.columns[5::6]]))
        proba_new10 = m_g3.predict_proba(np.array(mov[mov.columns[5::6]]))


def estadisticas(lista):
    mediaAcc = mean(lista)
    desvAcc = std(lista)
    lista = [(val - mediaAcc) / desvAcc for val in lista]
    maximoAcc = max(lista)
    minAcc = min(lista)
    return MpuEstadisticas(media=mediaAcc, std=desvAcc, max=maximoAcc, min=minAcc)


def data_adapter(model, captures):
    columns = []
    nColumns = len(model.devices) * model.fldNDuration * SENS_NUMBER * DATA_FREQ
    for i in range(0, nColumns, SENS_NUMBER):
        columns.append('acc' + str(i))
        columns.append('acc' + str(i + 1))
        columns.append('acc' + str(i + 2))
        columns.append('gyr' + str(i + 3))
        columns.append('gyr' + str(i + 4))
        columns.append('gyr' + str(i + 5))
    columns.append('label')
    lines = []

    accX = estadisticas([mpu.fldFAccX for capture in captures for mpu in capture.mpu])
    accY = estadisticas([mpu.fldFAccY for capture in captures for mpu in capture.mpu])
    accZ = estadisticas([mpu.fldFAccZ for capture in captures for mpu in capture.mpu])
    gyrX = estadisticas([mpu.fldFGyrX for capture in captures for mpu in capture.mpu])
    gyrY = estadisticas([mpu.fldFGyrY for capture in captures for mpu in capture.mpu])
    gyrZ = estadisticas([mpu.fldFGyrZ for capture in captures for mpu in capture.mpu])

    for capture in captures:
        captureLin = []
        for mpu in capture.mpu:
            captureLin.append((((mpu.fldFAccX - accX.media)/accX.std)-accX.min)/(accX.max - accX.min))
            captureLin.append((((mpu.fldFAccY - accY.media)/accY.std)-accY.min)/(accY.max - accY.min))
            captureLin.append((((mpu.fldFAccZ - accZ.media)/accZ.std)-accZ.min)/(accZ.max - accZ.min))
            captureLin.append((((mpu.fldFGyrX - gyrX.media)/gyrX.std)-gyrX.min)/(gyrX.max - gyrX.min))
            captureLin.append((((mpu.fldFGyrY - gyrY.media)/gyrY.std)-gyrY.min)/(gyrY.max - gyrY.min))
            captureLin.append((((mpu.fldFGyrZ - gyrZ.media)/gyrZ.std)-gyrZ.min)/(gyrZ.max - gyrZ.min))
        captureLin.append(capture.owner.fldSLabel)
        lines.append(captureLin)
    df = pd.DataFrame(np.array(lines), columns=columns)
    return df, accX, accY, accZ, gyrX, gyrY, gyrZ
