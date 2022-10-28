"""
    energy.py
    Support rutines for DAGs. Application: electricity demand forecasting.
"""
import traceback
# psycopg2: python package to deal with a postgres database
# pip install psycopg2
import psycopg2
from psycopg2.extras import execute_values
    
import numpy as np
import pandas as pd

from datetime import datetime

import urllib.request
import json

##-----------------------------------------------------------------------------------------------------------
## AS far as I understood, it's not good to catch run time failures because the DAG will end up without error.
## SO, let the errors go so Airflow task will end with error and the next task will not execute.
##-----------------------------------------------------------------------------------------------------------
def build_postgres_cnxn(database, host, user, password, port=5432, string_connection=None, verbose=True):
    error_txt = ''
    process_ok = True
    cnxn = None
    cursor = None
    if (not host or not user or not password) and not string_connection:
        process_ok = False
        error_txt = 'ERROR build_postgres_cnxn: Error trying to Build DB connexion: you missed to send host, user or password, or string connection. ' +\
                    ' host: ' + (host if host else 'Missed. ') +\
                    ' user: ' + (user if user else 'Missed.') +\
                    ' password: ' + (password if password else 'Missed.') +\
                    ' String Connection: ' + (string_connection if string_connection else 'Missed.')
        if verbose:
            print(error_txt)
    else:
        if not database:
            if verbose:
                print('WARNING build_postgres_cnxn: no database name provided.')
        try:
            if not string_connection:
                cnxn = psycopg2.connect(database=database, host=host, user=user, password=password, port=port)
            else:
                cnxn = psycopg2.connect(string_connection)
            cursor = cnxn.cursor()
            if verbose:
                print('INFO Module build_postgres_cnxn: DB Connection to host', host, 'Ok')
        except Exception as err:
            process_ok = False
            formatted_lines = traceback.format_exc().splitlines()
            txt = ' '.join(formatted_lines)
            if not string_connection:
                if verbose:
                    print('ERROR build_postgres_cnxn: Error connectig to database host: ' + host + ' user ' +\
                      user + ' port: ' + str(port) +'\n' + txt)
            else:
                if verbose:
                    print('ERROR build_postgres_cnxn: Error connectig to database string_connection: ' + string_connection +'\n' + txt)
    return process_ok, cnxn, cursor

def pg_select_to_pandas(cursor, sql_query):
    error_txt = ''
    process_ok = True
    df = pd.DataFrame()
    if (not cursor or not sql_query):
        process_ok = False
        error_txt = 'ERROR pg_select_to_pandas: No cursor or Query sent as parameter. ' +\
              ' cursor: ' + (' received.' if cursor else ' missed,') +\
              ' query: ' + (sql_query if sql_query else ' missed.')
        print(error_txt)
    else:
        try:
            cursor.execute(sql_query)
            data = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(data=data, columns=colnames)
            print('INFO pg_select_to_pandas: query executed Ok. Number of records returned: ' + str(df.shape[0]))
        except Exception as err:
            process_ok = False
            formatted_lines = traceback.format_exc().splitlines()
            txt = ' '.join(formatted_lines)
            error_txt = 'ERROR pg_select_to_pandas: Error executing query on host: ' + cursor.connection.info.host + ' database ' +\
                  cursor.connection.info.dbname + ' query: ' + sql_query +'\n' + txt
            print(err)
    return process_ok, error_txt, df

def _url_request_to_pandas(_request, verbose=True):
    error_txt = ''
    process_ok = True
    df = pd.DataFrame()
    if (not _request):
        process_ok = False
        error_txt = 'ERROR api_request_to_pandas: No API statement provided.'
        if verbose:
            print(error_txt)
    else:
        try:
            response = urllib.request.urlopen(_request)
            data = response.read()
            encoding = response.info().get_content_charset('utf-8')
            response.close()
            JSON_object = json.loads(data.decode(encoding))
            df = pd.json_normalize(JSON_object)
            if verbose:
                print('INFO api_request_to_pandas: API request executed Ok. Number of records returned: ' + str(df.shape[0]))
        except Exception as err:
            process_ok = False
            formatted_lines = traceback.format_exc().splitlines()
            txt = ' '.join(formatted_lines)
            error_txt = 'ERROR api_request_to_pandas: Error requesting API: ' + _request +'\n' + txt
    return process_ok, error_txt, df

def is_holiday(date=datetime.now(), verbose=True):
    is_a_holiday = 0
    _request = 'http://nolaborables.com.ar/api/v2/feriados/'+str(date.year)
    process_ok, error_txt, df_holidays = _url_request_to_pandas(_request, verbose)
    if not process_ok:
        if verbose:
            print('ERROR is_holiday. ' + error_txt)
    else:
        is_a_holiday = int(df_holidays[(df_holidays.dia==date.day) & (df_holidays.mes==date.month)].shape[0] > 0)
        if verbose:
            print('INFO is_holiday. URL request for ' + str(date) + ' Ok.')
    return process_ok, error_txt, is_a_holiday

#*************************************************************
# ROUTINES for DAGs
#*************************************************************
def _pg_query_regions_to_pandas(database, host, user, password, port, sql_query):
    process_ok, cnxn, cursor = build_postgres_cnxn(database='user', host='local_pgdb', user='user', password='admin', port=5432)
    if process_ok:
        process_ok, df = pg_select_to_pandas(cursor, sql_query)
        cnxn.close()
    return process_ok, df

def _get_hourly_demand(date, database, host, user, password, port, verbose=True):
    import sys
    print('Pandas Version:', pd.__version__)
    print('Python Version:', sys.version)
    print('Fecha:', date)
    process_ok = True
    if not date:
        date=datetime.now()
    verbose=True
    error_txt = ''
    process_ok, cnxn, cursor = build_postgres_cnxn(database=database, host=host, user=user, password=password, port=port, verbose=verbose)
    if not process_ok:
        if verbose:
            print(error_txt)
    else:
        date = date.date()
        _request = 'https://api.cammesa.com/demanda-svc/demanda/ObtieneDemandaYTemperaturaRegionByFecha?fecha='+str(date)+'&id_region=1002'
        process_ok, error_txt, df_demand = _url_request_to_pandas(_request, verbose)
        if not process_ok:
            if verbose:
                print(error_txt)
                cnxn.close()
        else:
            df_demand.fecha = pd.to_datetime(df_demand.fecha.astype(str).str[:19], format='%Y-%m-%d %H:%M:%S')
            df_demand = df_demand[df_demand.fecha.dt.minute==0]
            if df_demand.shape[0]==0:
                if verbose:
                    print('INFO get_hourly_demand - No Data to upsert. Date: ' + str(date))
            else:
                # demand values can come as Nan --> exclude those records.
                df_demand.dropna(axis=0, subset=['dem'], inplace=True)
                df_demand.dem = df_demand.dem.astype(int)
                df_demand['day_of_week'] = df_demand.fecha.dt.dayofweek
                process_ok, error_txt, is_a_holiday = is_holiday(date, verbose=verbose)
                if not process_ok:
                    if verbose:
                        print(error_txt)
                    cnxn.close()
                else:
                    df_demand['is_holiday'] = is_a_holiday
                    tup = [tuple(np.append(np.append([1002], r), ['COLMO', datetime.now(), 'COLMO', datetime.now()])) \
                            for r in df_demand.to_numpy()]
                    sql = 'INSERT INTO cammesa_db.hourly_demand '+\
                        '(region_code, timestamp, hourly_demand, hourly_temp, day_of_week, is_holiday, create_user, create_date, '+\
                        'update_user, update_date) VALUES %s ON CONFLICT (region_code, timestamp) DO UPDATE '+\
                        'SET hourly_demand=EXCLUDED.hourly_demand, hourly_temp=EXCLUDED.hourly_temp, day_of_week=EXCLUDED.day_of_week, '+\
                        'is_holiday=EXCLUDED.is_holiday, update_user=EXCLUDED.update_user, update_date=EXCLUDED.update_date;'
                    execute_values(cursor, sql, tup)
                    cnxn.commit()
                    print('INFO get_hourly_demand - ' + str(len(tup)) + ' records were upserted. Table cammesa_db.hourly_demand.')
        cnxn.close()
    return process_ok

    