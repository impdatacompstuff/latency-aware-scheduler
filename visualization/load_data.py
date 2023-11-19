import datetime
from operator import itemgetter
import seaborn as sns
import matplotlib.pyplot as plt
import psycopg2
import pandas as pd
import pandas.io.sql as sqlio

DATETIME_FORMAT = "%d-%m-%Y_%H-%M-%S"


def load_all_metrics_assignments_and_requests_per_node(from_exclusive_exp_id, until_exclusive_exp_id):
    conn, cur = create_db_connection()
    start_times = get_exp_id_start_dict(cur, from_exclusive_exp_id, until_exclusive_exp_id)
    measurements = get_scheduling_results(cur, from_exclusive_exp_id, until_exclusive_exp_id)
    pods = get_pods(cur, from_exclusive_exp_id, until_exclusive_exp_id)
    pod_rows = create_pod_rows(start_times, pods)
    requests = get_resource_requests(cur, from_exclusive_exp_id, until_exclusive_exp_id)
    df = get_all_metrics_per_node_with_pod_requests_and_assignments_df(measurements, start_times, requests, pod_rows)

    return df


def load_pod_assignments_per_node(from_exclusive_exp_id, until_exclusive_exp_id):
    conn, cur = create_db_connection()
    start_times = get_exp_id_start_dict(cur, from_exclusive_exp_id, until_exclusive_exp_id)

    pod_rows = []
    nodes = ["uniba-dsg-h5113", "uniba-dsg-h5114", "uniba-dsg-h5115"]
    for node in nodes:
        pods_for_node = get_pods_by_assigned_node(cur, node, from_exclusive_exp_id, until_exclusive_exp_id)
        rows = create_pod_rows_for_node(start_times, node, pods_for_node)
        pod_rows.extend(rows)

    df = pd.DataFrame(pod_rows)

    return df


def load_metric_and_request_per_node(metric, from_exclusive_exp_id, until_exclusive_exp_id):
    conn, cur = create_db_connection()
    start_times = get_exp_id_start_dict(cur, from_exclusive_exp_id, until_exclusive_exp_id)
    measurements = get_scheduling_results_by_metric(cur, metric, from_exclusive_exp_id, until_exclusive_exp_id)
    request = get_resource_request(cur, metric, from_exclusive_exp_id, until_exclusive_exp_id)
    df = get_metric_per_node_with_pod_request_df(metric, measurements, start_times, request)

    return df


def load_metric_per_node(metric, from_exclusive_exp_id, until_exclusive_exp_id):
    conn, cur = create_db_connection()
    start_times = get_exp_id_start_dict(cur, from_exclusive_exp_id, until_exclusive_exp_id)
    measurements = get_scheduling_results_by_metric(cur, metric, from_exclusive_exp_id, until_exclusive_exp_id)
    df = get_metric_per_node_df(measurements, start_times)

    return df


def load_all_metrics_per_node(from_exclusive_exp_id, until_exclusive_exp_id):
    conn, cur = create_db_connection()
    start_times = get_exp_id_start_dict(cur, from_exclusive_exp_id, until_exclusive_exp_id)
    measurements = get_scheduling_results(cur, from_exclusive_exp_id, until_exclusive_exp_id)
    df = get_all_metrics_per_node_df(measurements, start_times)
    return df


def get_metric_per_node_df(measurements, start_times):
    timed_measurements = []
    for measurement in measurements:
        measurement_time = measurement[7]
        exp_id = measurement[0]
        minute = calculate_relative_time(start_times[str(exp_id)], measurement_time)
        row = {"exp_id": exp_id, "min": minute, "node": measurement[2], "metric_value": measurement[4]}
        timed_measurements.append(row)
    # print(lat_measurements)
    df = pd.DataFrame(timed_measurements)
    return df


def get_all_metrics_per_node_df(measurements, start_times):
    timed_measurements = []

    for measurement in measurements:
        measurement_time = measurement[7]
        exp_id = measurement[0]
        minute = calculate_relative_time(start_times[str(exp_id)], measurement_time)
        node = measurement[2]
        metric = measurement[3]
        metric_value = measurement[4]
        if metric == 'TCP' or metric == 'UDP':
            metric_value = float(metric_value)/1000.0

        metric_label = ""
        if metric == "LAT":
            metric_label = "latency [ms]"
        if metric == "TCP":
            metric_label = "TCP bandwidth [Mbits/sec]"
        if metric == "UDP":
            metric_label = "UDP bandwidth [Mbits/sec]"
        if metric == "JIT":
            metric_label = "jitter [ms]"

        row = {"exp_id": exp_id, node: minute, metric_label: metric_value}
        timed_measurements.append(row)
    print(timed_measurements[0])
    df = pd.DataFrame(timed_measurements)
    return df


def get_metric_per_node_with_pod_request_df(metric, measurements, start_times, request):
    united_measurements = []

    if metric == 'TCP' or metric == 'UDP':
        request = float(request)/1000.0

    for measurement in measurements:
        measurement_time = measurement[7]
        exp_id = measurement[0]
        minute = calculate_relative_time(start_times[str(exp_id)], measurement_time)

        metric_value = measurement[4]
        if metric == 'TCP' or metric == 'UDP':
            metric_value = float(metric_value)/1000.0

        row = {"curve": "node", "min": minute, "node": measurement[2], "metric_value": metric_value}
        row1 = {"curve": "request", "min": minute, "node": measurement[2], "metric_value": request}
        united_measurements.append(row)
        united_measurements.append(row1)
    # print(lat_measurements)

    final_request_row1 = {"curve": "request", "min": 11.26, "node": "uniba-dsg-h5113", "metric_value": request}
    final_request_row2 = {"curve": "request", "min": 11.26, "node": "uniba-dsg-h5114", "metric_value": request}
    final_request_row3 = {"curve": "request", "min": 11.26, "node": "uniba-dsg-h5115", "metric_value": request}
    united_measurements.append(final_request_row1)
    united_measurements.append(final_request_row2)
    united_measurements.append(final_request_row3)
    df = pd.DataFrame(united_measurements)
    return df


def get_all_metrics_per_node_with_pod_requests_and_assignments_df(measurements, start_times, requests, pod_rows):
    united_measurements = pod_rows
    for measurement in measurements:
        measurement_time = measurement[7]
        exp_id = measurement[0]
        minute = calculate_relative_time(start_times[str(exp_id)], measurement_time)
        row = {"curve": "node", measurement[2]: minute, measurement[3]: measurement[4]}
        row1 = {"curve": "request", measurement[2]: minute, measurement[3]: requests[measurement[3]]}
        united_measurements.append(row)
        united_measurements.append(row1)

    return pd.DataFrame(united_measurements)


def get_all_metrics_with_pod_requests_and_assignments_for_node_df(node_name, measurements, start_times, requests,
                                                                  pod_rows):
    united_measurements = pod_rows
    for measurement in measurements:
        measurement_time = measurement[7]
        exp_id = measurement[0]
        minute = calculate_relative_time(start_times[str(exp_id)], measurement_time)
        # {"curve": "node", "node": node_name, "min": minute, "metric": "POD", "value": assignments}
        row = {"curve": "node", "node": node_name, "min": minute, "metric": measurement[3], "value": measurement[4]}
        row1 = {"curve": "request", "node": node_name, "min": minute, "metric": measurement[3],
                "value": requests[measurement[3]]}
        united_measurements.append(row)
        united_measurements.append(row1)

    return pd.DataFrame(united_measurements)


def create_pod_rows(start_times, pods):
    pod_rows = []
    # TODO count assignment per node
    assignments = 0

    unassigned_pods = []
    for pod in pods:
        if pod[3] is None:
            unassigned_pods.append(pod)

    for pod in unassigned_pods:
        pods.remove(pod)

    sorted_pods = sorted(pods, key=itemgetter(3))

    row1 = {"curve": "node", "uniba-dsg-h5113": 0, "POD": assignments}
    row2 = {"curve": "node", "uniba-dsg-h5114": 0, "POD": assignments}
    row3 = {"curve": "node", "uniba-dsg-h5115": 0, "POD": assignments}
    pod_rows.append(row1)
    pod_rows.append(row2)
    pod_rows.append(row3)

    for pod in sorted_pods:
        exp_id = pod[0]
        minute = calculate_relative_time(start_times[str(exp_id)], pod[3])
        node = pod[4]
        assignments = assignments + 1
        row = {"curve": "node", node: minute, "POD": assignments}
        pod_rows.append(row)
        # print(row)

    return pod_rows


def create_pod_rows_for_nodes(start_times, pods_for_node):
    pod_rows = []


def create_pod_rows_for_node(start_times, node_name, pods):
    pod_rows = []
    assignments = 0

    unassigned_pods = []
    for pod in pods:
        if pod[3] is None:
            unassigned_pods.append(pod)

    for pod in unassigned_pods:
        pods.remove(pod)

    sorted_pods = sorted(pods, key=itemgetter(3))

    initial_row = {"curve": "node", "node": node_name, "min": 0, "metric_value": assignments}
    pod_rows.append(initial_row)

    for pod in sorted_pods:
        exp_id = pod[0]
        minute = calculate_relative_time(start_times[str(exp_id)], pod[3])
        assignments = assignments + 1
        row = {"curve": "node", "node": node_name, "min": minute, "metric_value": assignments}
        pod_rows.append(row)
        print(row)

    final_row = {"curve": "node", "node": node_name, "min": 11.26, "metric_value": assignments}
    pod_rows.append(final_row)

    return pod_rows


def get_resource_request(cur, metric, from_exclusive_exp_id, until_exclusive_exp_id):
    metric_request = ""
    if metric == "LAT":
        metric_request = "latency_request"
    if metric == "TCP":
        metric_request = "tcp_mbpns_request"
    if metric == "UDP":
        metric_request = "udp_mbpns_request"
    if metric == "JIT":
        metric_request = "jitter_request"

    sql = "SELECT {0} FROM pods WHERE exp_id>{1} AND exp_id<{2};" \
        .format(metric_request, from_exclusive_exp_id, until_exclusive_exp_id)
    cur.execute(sql)
    requests = cur.fetchall()
    requests = list(dict.fromkeys(requests))

    if len(requests) != 1:
        print("Pod requests for {} are not the same!".format(metric))
        exit(1)

    request_value = requests[0][0]
    # print("Request: ", requests[0][0])
    return request_value


def get_resource_requests(cur, from_exclusive_exp_id, until_exclusive_exp_id):
    metric_request_pairs = {}
    metrics = ["LAT", "JIT", "TCP", "UDP"]

    for metric in metrics:
        request = get_resource_request(cur, metric, from_exclusive_exp_id, until_exclusive_exp_id)
        metric_request_pairs[metric] = request

    return metric_request_pairs


def get_scheduling_results_by_metric(cur, metric, from_exclusive_exp_id, until_exclusive_exp_id):
    sql = "SELECT * FROM scheduling_results WHERE exp_id>{0} AND exp_id<{1} AND metric=\'{2}\';" \
        .format(from_exclusive_exp_id, until_exclusive_exp_id, metric)
    cur.execute(sql)
    measurements = cur.fetchall()
    return measurements


def get_scheduling_results(cur, from_exclusive_exp_id, until_exclusive_exp_id):
    sql = "SELECT * FROM scheduling_results WHERE exp_id>{0} AND exp_id<{1};" \
        .format(from_exclusive_exp_id, until_exclusive_exp_id)
    cur.execute(sql)
    measurements = cur.fetchall()
    return measurements


def get_pods(cur, from_exclusive_exp_id, until_exclusive_exp_id):
    sql = "SELECT * FROM pods WHERE exp_id>{0} AND exp_id<{1};" \
        .format(from_exclusive_exp_id, until_exclusive_exp_id)
    cur.execute(sql)
    pods = cur.fetchall()
    return pods


def get_pods_by_assigned_node(cur, node_name, from_exclusive_exp_id, until_exclusive_exp_id):
    sql = "SELECT * FROM pods WHERE exp_id>{0} AND exp_id<{1} AND assigned_node=\'{2}\';" \
        .format(from_exclusive_exp_id, until_exclusive_exp_id, node_name)
    cur.execute(sql)
    pods = cur.fetchall()
    return pods


def get_exp_id_start_dict(cur, from_exclusive_exp_id, until_exclusive_exp_id):
    sql = "SELECT * FROM experiments WHERE exp_id>{0} AND exp_id<{1};" \
        .format(from_exclusive_exp_id, until_exclusive_exp_id)
    cur.execute(sql)
    experiments = cur.fetchall()
    start_times = {}
    for experiment in experiments:
        exp_id = experiment[0]
        start = experiment[1]
        start_times[str(exp_id)] = start
    return start_times


def calculate_relative_time(start, measurement_time):
    start_datetime = datetime.datetime.strptime(start, DATETIME_FORMAT)
    measurement_datetime = datetime.datetime.strptime(measurement_time, DATETIME_FORMAT)
    minute = measurement_datetime - start_datetime
    return minute.seconds / 60


def create_db_connection():
    conn = psycopg2.connect(host="141.13.5.112",
                            port="5432", dbname="scheduling_data", user="postgres", password="2345")
    cur = conn.cursor()
    return conn, cur


def draw_metric_request_assignments_graph_for_metric(data):
    sns.set_style("ticks")
    rel = sns.relplot(
        data=data,
        kind="line",
        col="node",
        x="min",
        y="metric_value",
        hue="curve",
        drawstyle='steps-post'
    )

    return rel


def draw_assignments_graph_for_nodes(data):
    sns.set_style("ticks")
    rel = sns.relplot(
        data=data,
        kind="line",
        col="node",
        x="min",
        y="metric_value",
        drawstyle='steps-post'
    )

    return rel


def draw_metric_request_graph(data):
    sns.set_style("ticks")
    rel = sns.relplot(
        data=data,
        kind="line",
        col="node",
        x="min", y="metric_value", hue="curve"
    )

    return rel


def draw_metric_graph(data):
    sns.set_style("ticks")
    rel = sns.relplot(
        data=data,
        kind="line",
        col="metric",
        x="min", y="metric_value", hue="exp_id"
    )
    # rel.fig.subplots_adjust(top=.8)
    # rel.fig.suptitle('Natural LAT')

    return rel


if __name__ == "__main__":
    for i in range(102, 103):
        lat_for_nodes = load_metric_and_request_per_node("LAT", i-1, i+1)
        rel = draw_metric_request_assignments_graph_for_metric(lat_for_nodes)
        rel.set(ylabel="latency [ms]")
        rel.fig.subplots_adjust(top=.8)
        rel.fig.suptitle('Latency Metrics per Node for exp_id ' + str(i))
        #
        # rel.savefig('Latency_Metrics_per_Node_for_exp_id_' + str(i) + '.png')

    # for i in range(97, 98):
    #     tcp_for_nodes = load_metric_and_request_per_node("TCP", i-1, i+1)
    #     rel = draw_metric_request_assignments_graph_for_metric(tcp_for_nodes)
    #     rel.set(ylabel="TCP bandwidth [Mbits/sec]")
    #     rel.fig.subplots_adjust(top=.8)
    #     rel.fig.suptitle('TCP Metrics per Node for exp_id ' + str(i))
    #
    #     rel.savefig('TCP_Metrics_per_Node_for_exp_id_' + str(i) + '.png')
    #
    # for i in range(97, 98):
    #     udp_for_nodes = load_metric_and_request_per_node("UDP", i-1, i+1)
    #     rel = draw_metric_request_assignments_graph_for_metric(udp_for_nodes)
    #     rel.set(ylabel="UDP bandwidth [Mbits/sec]")
    #     rel.fig.subplots_adjust(top=.8)
    #     rel.fig.suptitle('UDP Metrics per Node for exp_id ' + str(i))
    #
    #     rel.savefig('UDP_Metrics_per_Node_for_exp_id_' + str(i) + '.png')
    #
    # for i in range(97, 98):
    #     jit_for_nodes = load_metric_and_request_per_node("JIT", i-1, i+1)
    #     rel = draw_metric_request_assignments_graph_for_metric(jit_for_nodes)
    #     rel.set(ylabel="jitter [ms]")
    #     rel.fig.subplots_adjust(top=.8)
    #     rel.fig.suptitle('Jitter Metrics per Node for exp_id ' + str(i))
    #
    #     rel.savefig('JIT_Metrics_per_Node_for_exp_id_' + str(i) + '.png')
    #
    # for i in range(97, 98):
    #     pods_for_nodes = load_pod_assignments_per_node(i-1, i+1)
    #     rel = draw_assignments_graph_for_nodes(pods_for_nodes)
    #     rel.set(ylabel="number of pod assignments")
    #     rel.fig.subplots_adjust(top=.8)
    #     rel.fig.suptitle('Pod Assignments per Node for exp_id ' + str(i))
    # #
    #     rel.savefig('Pod_Assignments_per_Node_for_exp_id_' + str(i) + '.png')

    # nat_lat = load_metric_per_node("LAT", 56, 68)
    # draw_metric_graph(nat_lat)

    # everything = load_all_metrics_assignments_and_requests_per_node(31, 33)
    # g = sns.PairGrid(everything, y_vars=["LAT", "JIT", "TCP", "UDP", "POD"],
    #                  x_vars=["uniba-dsg-h5113", "uniba-dsg-h5114", "uniba-dsg-h5115"], hue="curve")

    # pal_hls = sns.color_palette().as_hex()
    # print(pal_hls)
    # all_metrics_without_requests = load_all_metrics_per_node(89, 91)
    # g = sns.PairGrid(all_metrics_without_requests, y_vars=["latency [ms]", "jitter [ms]", "TCP bandwidth [Mbits/sec]", "UDP bandwidth [Mbits/sec]"],
    #                  x_vars=["uniba-dsg-h5113", "uniba-dsg-h5114", "uniba-dsg-h5115"], hue="exp_id", palette=['#1f77b4'])
    # g.map(sns.lineplot, drawstyle='steps-post')
    # g.fig.subplots_adjust(top=.9, left=.125)
    # g.fig.suptitle('Natural Metrics per Node for exp_id 90')
    # g.savefig('Natural_Metrics_per_Node_for_exp_id_90.png')
    # print(g.axes)
    # print(everything.columns)

    # plt.fill_between("uniba-dsg-h5113", "LAT", color="red")
    # for metric_axes in g.axes:
    #     for node_axes in metric_axes:
    #         threshold = 0.75
    #         node_axes.fill_between("uniba-dsg-h5113", 0, 400, where )
    # g.fig.subplots_adjust(top=.9, left=.125)
    # g.fig.suptitle('Netem Metrics Grid per Node for exp_id 15')
    # g.savefig('Netem_Metrics_Grid_per_Node_for_exp_id_15.png')
    plt.show()
