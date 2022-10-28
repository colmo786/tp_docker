# Cronguru: https://crontab.guru/between-certain-hours
from datetime import datetime, timedelta

# The DAG object; we'll need this to instantiate a DAG
from airflow import DAG
# Operators; we need this to operate!
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
# Email when fail: https://stackoverflow.com/questions/51726248/airflow-dag-customized-email-on-any-of-the-task-failure
#from airflow.operators.email_operator import EmailOperator
#from airflow.utils.trigger_rule import TriggerRule

from energy import _get_hourly_demand, _calculate_hourly_demand_forecast

# These args will get passed on to each operator
# You can override them on a per-task basis during operator initialization
default_args = {
    'owner': 'energy',
    'depends_on_past': False,
    'start_date': datetime(2022, 10, 26),
    'email': ['colmo786@gmail.com'],
    'email_on_failure': False, # to send an e-mail after task fail, you should config SMTP in airflow.cfg and set this to True
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
    # 'wait_for_downstream': False,
    # 'dag': dag,
    # 'sla': timedelta(hours=2),
    # 'execution_timeout': timedelta(seconds=300),
    # 'on_failure_callback': some_function,
    # 'on_success_callback': some_other_function,
    # 'on_retry_callback': another_function,
    # 'sla_miss_callback': yet_another_function,
    # 'trigger_rule': 'all_success'
}

# define the python function
def get_hourly_demand(**kwargs):
    database = Variable.get("ENERGY_DB")
    host = Variable.get("ENERGY_DB_HOST")
    user = Variable.get("ENERGY_DB_USER")
    password = Variable.get("ENERGY_DB_PASS")
    port = Variable.get("ENERGY_DB_PORT")
    process_ok = _get_hourly_demand(date=kwargs['execution_date'], database=database, host=host
                    , user=user, password=password, port=port, verbose=True)
    print('INFO get_hourly_demand execution: ', kwargs['execution_date'])
    if not process_ok:
        raise ValueError()
    return

def calculate_hourly_demand_forecast(**kwargs):
    database = Variable.get("ENERGY_DB")
    host = Variable.get("ENERGY_DB_HOST")
    user = Variable.get("ENERGY_DB_USER")
    password = Variable.get("ENERGY_DB_PASS")
    port = Variable.get("ENERGY_DB_PORT")
    print('INFO calculate_hourly_demand_forecast execution init: ', kwargs['execution_date'])
    process_ok, error_txt = _calculate_hourly_demand_forecast(database=database, host=host, user=user, password=password
                                                              , port=port, n_lookback=48, n_forecast=24, verbose=True)
    if not process_ok:
        print('ERROR calculate_hourly_demand_forecast. ' + error_txt)
        raise ValueError()
    return

# define the DAG
dag = DAG(
    'ENG_hourly_process_v1',
    default_args=default_args,
    description='Queries Cammesa API to get electricity demand for the actual date. Inserts or update hourly information into Postgres DB. Calculates next 24 hours forecast',
    # Having the schedule_interval as None means Airflow will never automatically schedule a run of the Dag.
    # you can schedule it manually via the trigger button in the Web UI
    #schedule_interval=None
    schedule_interval='5 * * * *' # Every hour at minute 5
)

# define tasks
t1 = PythonOperator(
    task_id='get_hourly_demand',
    python_callable= get_hourly_demand,
    provide_context=True,
    #op_kwargs = {'date': context[execution_date], 'database': 'user', 'host': 'local_pgdb', 'user': 'user', 'password': 'admin', 'port': 5432
    #    , 'verbose': 'True'},
    dag=dag,
)

t2 = PythonOperator(
    task_id='calculate_hourly_demand_forecast',
    python_callable= calculate_hourly_demand_forecast,
    provide_context=True,
    dag=dag,
)

t1 >> t2