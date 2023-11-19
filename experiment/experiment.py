from kubernetes import config
from kubernetes import client
import yaml
from os import path
import time
from apscheduler.schedulers.background import BlockingScheduler
import datetime
import sys
import pytz
from time import sleep
from pytz import timezone
import psycopg2

DEPLOYMENT_NR = 10
DATETIME_FORMAT = "%d-%m-%Y_%H-%M-%S"


def run_experiment(k8s_v1_client, test_manifest):
    time.sleep(20)
    time.sleep(60)
    conn, cur = create_db_connection()
    exp_id = create_experiment_row(cur)
    v1_core_client = client.CoreV1Api()

    for i in range(DEPLOYMENT_NR):
        deployment_uid = create_test_deployment(k8s_v1_client, test_manifest, cur, exp_id)
        conn.commit()
        sleep(50)
        get_data(v1_core_client, k8s_v1_client, cur, exp_id, deployment_uid, conn)
        delete_test_deployment(k8s_v1_client)
        time.sleep(10)

    get_logs(v1_core_client, exp_id, cur, conn)
    end_experiment(cur, exp_id)
    # TODO commit konsistieren
    conn.commit()
    print("Final DB changes committed")


def create_test_deployment(k8s_client, manifest_file, cur, exp_id):
    post_deployment(k8s_client, manifest_file)
    deployment = read_deployment()
    deployment_uid = deployment.metadata.uid
    creation_time = format_datetime_eur(deployment.metadata.creation_timestamp)
    create_deployment_row(cur, deployment_uid, creation_time, exp_id)

    print("Deployment created.")
    return deployment_uid



def get_data(v1_core_client, k8s_client, cur, exp_id, deployment_uid, conn):
    pods = v1_core_client.list_namespaced_pod("default", label_selector="app=network-test")

    for i, pod in enumerate(pods.items):
        if pod.status.conditions is None:
            print("Pod {0} doesn't have conditions yet. Rolling back pod table".format(i))
            sql = "DELETE FROM pods WHERE exp_id=\'{0}\'".format(exp_id)
            cur.execute(sql)
            conn.commit()
            sleep(1)
            get_data(v1_core_client, k8s_client, cur, exp_id, deployment_uid, conn)
            return
        conditions = pod.status.conditions
        scheduled_info = False
        for condition in conditions:
            # if the PodScheduled condition exists, it means that the scheduler processed the pod
            if condition.type == "PodScheduled":
                scheduled_info = True

                requests = pod.spec.containers[0].resources.requests

                assigned_node = ""
                if pod.spec.node_name:
                    assigned_node = pod.spec.node_name

                pod_name_parts = pod.metadata.name.split("-")
                pod_name = pod_name_parts[3]

                create_pod_row(cur, exp_id, deployment_uid, pod_name, requests)

                if condition.status == "True":
                    if pod.metadata.creation_timestamp is not None:
                        start_string = ""
                        scheduling_duration = "-1"
                        if pod.status.start_time is not None:
                            start_string = format_datetime_eur(pod.status.start_time)
                            scheduling_duration_timedelta = pod.status.start_time - pod.metadata.creation_timestamp
                            scheduling_duration = scheduling_duration_timedelta / datetime.timedelta(microseconds=1)

                        sql = "UPDATE pods SET start_time=\'{0}\', assigned_node=\'{1}\', scheduling_duration=\'{2}\' " \
                              "WHERE exp_id=\'{3}\' AND pod_name=\'{4}\'" \
                            .format(start_string, assigned_node, scheduling_duration, exp_id, pod_name)
                        cur.execute(sql)
                        conn.commit()

        if not scheduled_info:
            print("Pod " + str(pod.metadata.name) + " didn't have PodScheduled condition.")

    print("Finished writing pod data")


def create_pod_row(cur, exp_id, deployment_uid, pod_name, requests):
    sql = "INSERT INTO pods(exp_id, deployment_uid, pod_name) VALUES (\'{0}\', \'{1}\', \'{2}\');" \
        .format(exp_id,
                deployment_uid,
                pod_name)
    cur.execute(sql)

    metrics = requests.keys()
    for metric in metrics:
        if metric == "example.com/latency-nanos":
            latency_request = get_value(requests[metric])
            sql = "UPDATE pods SET latency_request=\'{0}\' WHERE exp_id=\'{1}\' AND pod_name=\'{2}\'"\
                .format(latency_request, exp_id, pod_name)
            cur.execute(sql)
        if metric == "example.com/tcp-mbpns":
            tcp_request = get_value(requests["example.com/tcp-mbpns"])
            sql = "UPDATE pods SET tcp_mbpns_request=\'{0}\' WHERE exp_id=\'{1}\' AND pod_name=\'{2}\'"\
                .format(tcp_request, exp_id, pod_name)
            cur.execute(sql)
        if metric == "example.com/udp-mbpns":
            udp_request = get_value(requests["example.com/udp-mbpns"])
            sql = "UPDATE pods SET udp_mbpns_request=\'{0}\' WHERE exp_id=\'{1}\' AND pod_name=\'{2}\'"\
                .format(udp_request, exp_id, pod_name)
            cur.execute(sql)
        if metric == "example.com/jitter":
            jitter_request = get_value(requests["example.com/jitter"])
            sql = "UPDATE pods SET jitter_request=\'{0}\' WHERE exp_id=\'{1}\' AND pod_name=\'{2}\'"\
                .format(jitter_request, exp_id, pod_name)
            cur.execute(sql)


def get_value(request_string):
    # latency has quantity_suffix 'M' = mega
    if request_string.endswith('M'):
        request_string = int(request_string.split('M')[0]) * 1000000
    elif request_string.endswith('k'):
        request_string = int(request_string.split('k')[0]) * 1000
    elif request_string.endswith('m'):
        request_string = int(request_string.split('m')[0]) / 1000
    else:
        request_string = int(request_string)
    return request_string


def get_logs(v1_core_client, exp_id, cur, conn):
    api_response = v1_core_client.read_namespaced_pod_log(name="kube-scheduler-uniba-dsg-h5112", namespace='kube-system',
                                              container='scheduler-extender')

    pod_names = []

    lines = api_response.split("\n")
    for line in lines:
        words = line.split()

        if len(words) == 0:
            continue

        scheduling_date = words[0]
        scheduling_time = words[1]
        date_parts = scheduling_date.split("/")
        time_parts = scheduling_time.split(":")
        scheduling_datetime = datetime.datetime(year=int(date_parts[0]), month=int(date_parts[1]),
                                                day=int(date_parts[2]),
                                                hour=int(time_parts[0]), minute=int(time_parts[1]),
                                                second=int(time_parts[2])) \
            .astimezone(pytz.utc)


        # TODO: stimmen die Zeitzonen und Formate überein?
        scheduling_time_formatted = format_datetime_eur(scheduling_datetime)

        metric_str = words[2]
        metric = ""
        if metric_str == "latency":
            metric = "LAT"
        if metric_str == "TCPBandwidth":
            metric = "TCP"
        if metric_str == "UDPBandwidth":
            metric = "UDP"
        if metric_str == "jitter":
            metric = "JIT"

        result = words[3]

        complete_pod_name = words[4]
        print(complete_pod_name)
        name_parts = complete_pod_name.split("-")
        pod_name = name_parts[3]
        pod_names.append(pod_name)

        if result == "error":
            node_name = words[5]
            sql = "INSERT INTO scheduling_results(exp_id, pod_name, node, metric, result, scheduling_time) " \
                  "VALUES (\'{0}\', \'{1}\', \'{2}\', \'{3}\', \'{4}\', \'{5}\') " \
                  "ON CONFLICT (exp_id, pod_name, node, metric) DO UPDATE SET " \
                  "result=EXCLUDED.result, scheduling_time=EXCLUDED.scheduling_time;" \
                .format(exp_id, pod_name, node_name, metric, result, scheduling_time_formatted)
            cur.execute(sql)
            conn.commit()
            continue

        node_name = words[7]
        metric_value = words[8]

        sql = "INSERT INTO scheduling_results(exp_id, pod_name, node, metric, metric_value, result, scheduling_time) " \
              "VALUES (\'{0}\', \'{1}\', \'{2}\', \'{3}\', \'{4}\', \'{5}\', \'{6}\') " \
              "ON CONFLICT (exp_id, pod_name, node, metric) DO UPDATE SET " \
              "metric_value=EXCLUDED.metric_value, result=EXCLUDED.result, scheduling_time=EXCLUDED.scheduling_time;" \
            .format(exp_id, pod_name, node_name, metric, metric_value, result, scheduling_time_formatted)
        cur.execute(sql)
        conn.commit()

    unique_pod_names = list(dict.fromkeys(pod_names))

    expected_pods = DEPLOYMENT_NR * 20
    if len(unique_pod_names) != expected_pods:
        print("Amount of pods not correct: {0} instead of {1}. Rolling back.".format(len(unique_pod_names), expected_pods))
        sql = "DELETE FROM scheduling_results WHERE exp_id=\'{0}\'".format(exp_id)
        cur.execute(sql)
        sql = "DELETE FROM pods WHERE exp_id=\'{0}\'".format(exp_id)
        cur.execute(sql)
        sql = "DELETE FROM deployments WHERE exp_id=\'{0}\'".format(exp_id)
        cur.execute(sql)
        sql = "DELETE FROM experiments WHERE exp_id=\'{0}\'".format(exp_id)
        cur.execute(sql)

    print("Log data written")
    # v1.delete_namespaced_pod("kube-scheduler-uniba-dsg-h5112", namespace='kube-system', grace_period_seconds=0)
    print("Finished. Delete scheduler manually!!!!")


def create_deployment_row(cur, deployment_uid, creation_time, exp_id):
    sql = "INSERT INTO deployments(exp_id, deployment_uid, creation_time) VALUES (\'{0}\', \'{1}\', \'{2}\');" \
        .format(exp_id, deployment_uid, creation_time)
    cur.execute(sql)


def read_deployment():
    app_client = client.AppsV1Api()
    deployment = app_client.read_namespaced_deployment(name='network-test', namespace='default')
    return deployment


def post_deployment(k8s_client, manifest_file):
    with open(path.join(path.dirname("."), manifest_file)) as m:
        dep = yaml.safe_load(m)
        k8s_client.create_namespaced_deployment(
            body=dep, namespace="default")


def delete_test_deployment(k8s_client):
    k8s_client.delete_namespaced_deployment(name="network-test", namespace="default")
    print("Deployment deleted.")


def end_experiment(cur, exp_id):
    end = format_datetime_eur(datetime.datetime.now())
    sql = "UPDATE experiments SET end_time=\'{0}\' WHERE exp_id={1};".format(end, exp_id)
    cur.execute(sql)


def create_experiment_row(cur):
    start = format_datetime_eur(datetime.datetime.now())
    sql = "INSERT INTO experiments(start_time) VALUES (\'{0}\') RETURNING exp_id;".format(start)
    cur.execute(sql)
    exp_id = cur.fetchone()[0]
    print("Experiment id: ", exp_id)
    return exp_id


def create_db_connection():
    conn = psycopg2.connect(host="localhost",
                            port="5432", dbname="scheduling_data", user="postgres", password="2345")
    cur = conn.cursor()
    return conn, cur


def format_datetime_eur(datetime_object):
    return datetime_object.astimezone(timezone('Europe/Berlin')).strftime(DATETIME_FORMAT)


if __name__ == "__main__":
    config.load_kube_config()
    k8s_v1_client = client.AppsV1Api()

    today = datetime.datetime.now().astimezone(pytz.timezone('Europe/Berlin'))
    year = int(today.year)
    month = int(today.month)
    day = int(today.day)

    hour = int(sys.argv[2])
    minute = int(sys.argv[3])

    manifest = str(sys.argv[1])

    scheduler = BlockingScheduler()
    scheduler.add_job(run_experiment, 'date', run_date=datetime.datetime(year, month, day, hour, minute, 0),
                      timezone='Europe/Berlin', args=[k8s_v1_client, manifest])
    scheduler.start()
