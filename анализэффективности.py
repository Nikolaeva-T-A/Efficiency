# -*- coding: utf-8 -*-
"""
Анализ Эффективности

Данный скрипт предназначен для анализа физиологических данных, получаемых из 
Excel-файлов. Он позволяет обрабатывать данные электроэнцефалограммы (EEG), 
электромиограммы (EMG), температуры (TEMP) и частоты сердечных сокращений (RR).
Скрипт автоматически загружает все файлы Excel в указанной папке, фильтрует 
данные для удаления артефактов и вычисляет эффективность по четырем параметрам.

Функции:
- Рассчитывает средние и нормализованные значения для параметров.
- Вычисляет процентные изменения между началом и концом наблюдений.
- Определяет эффективные и неэффективные участки на основе заданных критериев.

Требования:
- Необходимы библиотеки: pandas, matplotlib, openpyxl, xlrd.
- Данные должны быть в формате Excel с двумя листами: 'Info' (информация о пациенте)
  и 'Data' (измерения).

Вывод: результаты анализа будут сохранены в новый файл 'efficiacy_filtered.xlsx'.

Автор: Николаева Татьяна Андреевна, t.maryanovskaya@alumni.nsu.ru
Дата: 7.04.2024
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import xlrd
import openpyxl
import math
import re

folder_path = ''
files = [file for file in os.listdir(folder_path) if file.endswith(".xlsx")]
files.sort()


def mean_norm(data_all, data_analisys, param1, param2, decrease):
  mean_n = 0
  parametr = 0
  all1 = data_all[param1].mean()
  all2 = data_all[param2].mean()
  index = data_analisys[param1].index
  for i in range(len(index)):
    if decrease:
      if i == 0:
        continue
      else:
        if data_analisys[param1][index[i-1]] > data_analisys[param1][index[i]]:
          delta1 =  data_analisys[param1][index[i]] - data_analisys[param1][index[i-1]]
          mean_n += delta1/all1
          delta2 =  data_analisys[param2][index[i]] - data_analisys[param2][index[i-1]]
          parametr += delta2/all2
          #print(delta)
        else:
          continue
    else:
      if i == 0:
        continue
      else:
        if data_analisys[param1][index[i-1]] < data_analisys[param1][index[i]]:
          delta1 = data_analisys[param1][index[i-1]] - data_analisys[param1][index[i]]
          mean_n += delta1/all1
          delta2 = data_analisys[param2][index[i-1]] - data_analisys[param2][index[i]]
          parametr += delta2/all2
          #print(delta)
        else:
          continue
  return mean_n, parametr


def delta( start, end, decrease):
    if decrease:
      return(end - start)/start * 100
    else:
      return (start - end)/start * 100


def mean_kvart(data):
  kvart = math.ceil( len(data)*0.25)

  return data[:kvart].mean(), data[-kvart:].mean()


#с фильтрацией
out = {}
EEG = {}
EMG = {}
Efficiacy = {}
RR = {}
T = {}
EEGall= {}
EMGall = {}
RRall = {}
Tall = {}
EEGkv= {}
EMGkv = {}
RRkv = {}
Tkv = {}
EEGdelta= {}
EMGdelta = {}
RRdelta = {}
Tdelta = {}
time = {}
strategy = {}


with pd.ExcelWriter('efficiacy_filtered.xlsx') as writer:
    queue = 1
    for file in files:
        print(file)
        if file != 'efficiacy_filtered.xlsx':
          try:
            data = pd.read_excel(file, sheet_name='Data', header=0)
            data = data[['Unnamed: 1',  'Unnamed: 4', 'Unnamed: 7', 'Unnamed: 10']]
            data.rename(columns={'Unnamed: 1': 'ALPHA1',
                                'Unnamed: 4': 'EMGINT1',
                                'Unnamed: 7': 'TEMP1',
                                'Unnamed: 10': 'RR1'}, inplace=True)
            data.drop(index=0, inplace=True)
            info = pd.read_excel(file, sheet_name='Info', header=None)

          except:
            print('Проверьте правильность анализируемых файлов, в файле должно быть 2 листа, первый лист Info где описана информация про пациента и второй лист с данными')
            continue
        else:
          continue

        # Имя пациента
        name = (info.iloc[0, 1])
        print(name)

        # Номер сессии
        #session = file[0]
        #session = seance(file)
        session = queue
        queue+=1
        print(name, 'session', session)

        #Удаление артефактов удалить секунду до и секунду после
        std_EMG = data['EMGINT1'].std()
        std_EEG = data['ALPHA1'].std()
        mean_EMG = data['EMGINT1'].mean()
        mean_EEG = data['ALPHA1'].mean()
        max_EEG = mean_EEG + 3*std_EEG
        min_EEG = 0.1
        max_EMG = mean_EMG + 3*std_EMG
        min_EMG = 0
        min_t = 70
        min_RR = 0


        # Удаление артефактов
        data = data[(data['ALPHA1'] >= min_EEG) &
            (data['ALPHA1'] <= max_EEG) &
            (data['EMGINT1'] >= min_EMG) &
            (data['EMGINT1'] <= max_EMG) &
            (data['TEMP1'] >= min_t) &
            (data['RR1'] >= min_RR)]


        # Определение эффективных участков
        daf = pd.DataFrame()
        daf['decrease_EMG'] = (data['EMGINT1'] < data['EMGINT1'].shift()).astype(int)
        daf['increased_EEG'] = (data['ALPHA1'] > data['ALPHA1'].shift()).astype(int)

        index_eff = []
        index_noeff = []
        for i in daf.index:
            if i == 1:
              continue
            if (daf['decrease_EMG'][i] == 1) and (daf['increased_EEG'][i] == 1):
              index_eff.append(i)
            else:
              index_noeff.append(i)
        index_eff

        effective = pd.DataFrame()
        eff_EMG = 0
        eff_RR = 0
        eff_EEG = 0
        eff_t = 0
        data_mean = data.mean()
        try:
          for i in index_eff:
            effective = pd.concat([effective, data.loc[i-1:i]])
            effective = effective.drop_duplicates()
            try:
              eff_EMG += effective['EMGINT1'][i]-effective['EMGINT1'][i-1]
              eff_RR += effective['RR1'][i]-effective['RR1'][i-1]
              eff_EEG += effective['ALPHA1'][i]-effective['ALPHA1'][i-1]
              eff_t += effective['TEMP1'][i]-effective['TEMP1'][i-1]
            except:
              print(f'отсутствуют данные для {i-1} - {i} times')
        except:
          print(f'отсутствуют эффективные участки')
        mean_eff_EMG = eff_EMG / data_mean['EMGINT1']
        mean_eff_RR = eff_RR / data_mean['RR1']
        mean_eff_EEG = eff_EEG / data_mean['ALPHA1']
        mean_eff_t = eff_t / data_mean['TEMP1']

        noeff = pd.DataFrame()
        noeff_EMG = 0
        noeff_RR = 0
        noeff_EEG = 0
        noeff_t = 0
        j = 0
        try:
          for j in index_noeff:
            noeff = pd.concat([noeff, data.loc[j-1:j]])
            noeff = noeff.drop_duplicates()
            try:
              noeff_EMG += noeff['EMGINT1'][j]-noeff['EMGINT1'][j-1]
              noeff_RR += noeff['RR1'][j]-noeff['RR1'][j-1]
              noeff_EEG += noeff['ALPHA1'][j]-noeff['ALPHA1'][j-1]
              noeff_t += noeff['TEMP1'][j]-noeff['TEMP1'][j-1]
            except:
                print(f'отсутствуют данные для {j-1} - {j} times')
        except:
          print(f'отсутствуют неэффективные участки')
        mean_noeff_EMG = noeff_EMG / data_mean['EMGINT1']
        mean_noeff_RR = noeff_RR / data_mean['RR1']
        mean_noeff_EEG = noeff_EEG / data_mean['ALPHA1']
        mean_noeff_t = noeff_t / data_mean['TEMP1']
        print('eff an noeff done')

        table = ['all data', 'success', 'non success']
        for i in table:
          if i ==  'success':
            key = str('s ')
            EMG[str('EMG '+ str(session)+ key)] =  [mean_eff_EMG]
            T[str('t '+ str(session)+ key)] =  [mean_eff_t]
            RR[str('RR '+ str(session)+ key)] = [mean_eff_RR]
            EEG[str('alpha '+ str(session)+ key)] = [mean_eff_EEG]
            #time[str('time '+ str(session)+ key)] = [len(effective)]
            Efficiacy[str('efficiacy '+ str(session))] = [math.log(len(effective)/len(data)*100)]


          if i == 'non success':
            key = str('ns ')
            EMG[str('EMG '+ str(session)+ key )] = [mean_noeff_EMG]
            T[str('t '+ str(session)+ key)] = [mean_noeff_t]
            RR[str('RR '+ str(session)+ key)] = [mean_noeff_RR]
            EEG[str('alpha '+ str(session)+ key)] = [mean_noeff_EEG]
            #time[str('time '+ str(session)+ key)] = [len(noeff)]

        kv1, kv2 = mean_kvart(data)
        EMGkv[str('EMG  b '+ str(session) )] = kv1[1]
        Tkv[str('T b '+ str(session) )] = kv1[2]
        RRkv[str('RR b '+ str(session) )] = kv1[3]
        EEGkv[str('alpha b '+ str(session) )] = kv1[0]
        EMGkv[str('EMG f '+ str(session) )] = kv2[1]
        Tkv[str('T f '+ str(session) )] = kv2[2]
        RRkv[str('RR f '+ str(session) )] = kv2[3]
        EEGkv[str('alpha f '+ str(session) )] = kv2[0]

        delta_value = delta(kv1, kv2, decrease=True)
        EMGdelta[str('EMG delta'+ str(session) )] = delta_value[1]
        Tdelta[str('T delta '+ str(session) )] = delta_value[2]
        RRdelta[str('RR delta '+ str(session) )] = delta_value[3]
        EEGdelta[str('EEG delta '+ str(session) )] = delta_value[0]

        strategy[str('стратегия '+ str(session))] = [[]]

    ind = {'name' : [str(name)]}
    out.update(ind)
    out.update(Efficiacy)

    out.update(EMG)
    out.update(EMGkv)
    out.update(EMGdelta)

    out.update(T)
    out.update(Tkv)
    out.update(Tdelta)

    out.update(EEG)
    out.update(EEGkv)
    out.update(EEGdelta)

    out.update(RR)
    out.update(RRkv)
    out.update(RRdelta)

    out.update(time)
    out.update(strategy)

    df = pd.DataFrame(out)

    df.to_excel(writer,  sheet_name='eff', index = False)
df.head()
