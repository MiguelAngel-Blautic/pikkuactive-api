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
from tensorflow.keras.optimizers import Adam, SGD
from tensorflow.keras.optimizers import Adadelta
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
from tensorflow.keras.optimizers import Adam, SGD
from tensorflow.keras.optimizers import Adadelta
# CONFIG
DATA_FREQ = 20
SENS_NUMBER = 1

def create_model(model, output_size=2):
    n_devices = len(model.devices)
    samples = model.fldNDuration * DATA_FREQ
    # input_shape = (n_devices*samples,)
    columns = 0
    for d in model.devices:
        columns += d.fldNSensores
    # samples = model.fldNDuration * DATA_FREQ
    input_shape = (samples * columns,)

    modelEmg = Sequential()
    modelEmg.add(Dense(20, input_shape=input_shape, activation='sigmoid'))
    modelEmg.add(Dense(60, activation='sigmoid'))
    modelEmg.add(Dense(output_size, activation='softmax'))

    # Generate name
    model_uuid = 'static/ecg_' + str(uuid.uuid1()) + '.h5'
    modelEmg.compile(optimizer=SGD(learning_rate=0.0045), loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    modelEmg.save(model_uuid)
    return model_uuid


def train_model(model, df, version_last, max_value=1):
    url = ''
    if version_last is None or version_last.url is None or not os.path.exists(version_last.url):
        url = create_model(model, len(model.movements))
    else:
        url = version_last.url

    num_epoch = 500
    tf_model = tf.keras.models.load_model(url)
    X_train_Emg, X_test_Emg, y_train, y_test = split_normalize_data(model, df, max_value)

    tf_model.compile(optimizer=Adam(learning_rate=0.0035), loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    tf_model.fit(X_train_Emg, y_train, batch_size=32, shuffle=True, epochs=num_epoch,
                 validation_data=(X_test_Emg, y_test), verbose=1)

    tf_model.save(url)
    evaluation = tf_model.evaluate(X_test_Emg, y_test)
    version = tbl_version(fldSUrl=url,
                          fldFAccuracy=float(evaluation[1]),
                          fldNEpoch=num_epoch,
                          fldFLoss=float(evaluation[0]),
                          fldSOptimizer='SGD',
                          fldFLearningRate=0.0045)

    return version


def split_normalize_data(model, df, max_value):
    label_enc = LabelEncoder()
    label_enc.fit([x.fldSLabel for x in model.movements])

    # Normalize
    filter_emg_col = [col for col in df if col.startswith('emg')]
    normalized_df = df.copy()
    normalized_df[filter_emg_col] = normalized_df[filter_emg_col] / max_value

    # Split
    X = normalized_df.drop(['fldSLabel'], axis=1)
    y = normalized_df['fldSLabel']
    y = label_enc.transform(y)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)

    return X_train, X_test, y_train, y_test


def generate_columns_index(end):
    columns_list = list(range(0, end))
    for i in range(0, len(columns_list), SENS_NUMBER):
        columns_list[i] = 'emg' + str(columns_list[i])
    return columns_list


def data_adapter(model, captures):
    n_devices = len(model.devices)

    samples = model.fldNDuration * DATA_FREQ

    columns = 0
    for d in model.devices:
        columns += d.fldNSensores
    columns_list = generate_columns_index(samples * columns)
    print(samples, " - ", columns, " - ", columns_list)

    df = pd.DataFrame(columns=columns_list)
    print(df)
    labels = []

    for capture in captures:

        only_data = []
        my_range = len(capture.ecg)*columns

        if my_range == samples * columns:
            for i_data in range(0, len(capture.ecg), len(model.devices)):
                data_x = []
                for i in range(len(model.devices)):
                    data_x.append(capture.ecg[i_data + i])

                sorted_data = sorted(data_x, key=lambda data: data.device.fldNNumberDevice)

                list_sorted = []
                for data in sorted_data:
                    n_sens = data.device.fldNSensores
                    if n_sens > 0:
                        list_sorted.append(data.fldFData0)
                    if n_sens > 1:
                        list_sorted.append(data.fldFData1)
                    if n_sens > 2:
                        list_sorted.append(data.fldFData2)
                    if n_sens > 3:
                        list_sorted.append(data.fldFData3)

                only_data.append(list_sorted)

                # print(i_data)

            labels.append(capture.owner.fldSLabel)
            np_data = np.resize(only_data, (1, len(only_data) * len(only_data[0])))
            df_length = len(df)
            df.loc[df_length] = np_data[0].tolist()
    pd.set_option('display.max_columns', columns * samples)
    df['fldSLabel'] = labels
    # print(df.shape)
    # print(df)

    return df


def saveModel():
    pass












