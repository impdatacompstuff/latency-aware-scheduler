import requests
from time import sleep
from kubernetes import config
from kubernetes import client
from pythonping import ping
import iperf3


def main():
    print("Application started :)")

    config.load_incluster_config()
    print("after incluster config")

    v1 = client.CoreV1Api()

    # TODO: udp/tcp request parallelisieren? -> nein weil ich damit potentiell mein netzwerk saturiere (die messungen beeinflussen sich gegenseitig)
    while True:
        # list all nodes
        nodes = v1.list_node()
        print("after list nodes")

        pods = v1.list_namespaced_pod("default", label_selector="name=iperf3-server")
        print("after get pods")

        pod_host_port = pods.items[0].spec.containers[0].ports[0].host_port
        print("pod hostport: %d", pod_host_port)

        for node in nodes.items:
            name = node.metadata.name
            node_ip = get_node_ip(node)
            print("node " + name + " found with ip: " + node_ip)

            for pod in pods.items:
                print(pod.metadata.name)
                if pod.spec.node_name == name:
                    print("sending requests to " + node_ip)
                    measure_latency(name, node_ip)
                    measure_bandwidth_per_TCP(node_ip, pod_host_port, name)
                    measure_UDP_bandwidth_and_jitter(node_ip, pod_host_port, name)
                    break


def measure_latency(node_name, node_ip):
    r = ping(node_ip)
    if r.success():
        avg_rtt = r.rtt_avg
        requests.post(
            "http://localhost:8080/write-metrics/nodes/" + node_name + "/example.com~1latency-nanos",
            json=avg_rtt)
        print("post request for node " + node_name + " with avg rtt %.8f sent" % avg_rtt)
    else:
        print("Error sending ping")


def measure_bandwidth_per_TCP(node_ip, host_port, node_name):
    tcp_client = iperf3.Client()
    tcp_client.reverse = True
    tcp_client.duration = 1
    tcp_client.server_hostname = node_ip
    tcp_client.port = host_port
    print("sending tcp request to node ip {0} port {1}".format(node_ip, host_port))
    tcp_result = tcp_client.run()
    if tcp_result.error:
        print(tcp_result)
    else:
        print('TCP Megabits per second for node {0} : (Mbps)  {1}'.format(node_name, tcp_result.sent_Mbps))
        requests.post(
            "http://localhost:8080/write-metrics/nodes/" + node_name + "/example.com~1tcp-mbpns",
            json=tcp_result.sent_Mbps)
    del tcp_client


def measure_UDP_bandwidth_and_jitter(node_ip, host_port, node_name):
    udp_client = iperf3.Client()
    udp_client.reverse = True
    udp_client.duration = 1
    udp_client.protocol = 'udp'
    udp_client.blksize = 1324
    udp_client.server_hostname = node_ip
    udp_client.port = host_port
    print("sending udp request to node ip {0} port {1}".format(node_ip, host_port))
    udp_result = udp_client.run()
    if udp_result.error:
        print(udp_result)
    else:
        print('UDP Megabits per second for node {0} : (Mbps)  {1}'.format(node_name, udp_result.Mbps))
        print('    Jitter ms for node {0} : (ms)  {1}'.format(node_name, udp_result.jitter_ms))
        requests.post(
            "http://localhost:8080/write-metrics/nodes/" + node_name + "/example.com~1udp-mbpns",
            json=udp_result.Mbps)
        requests.post(
            "http://localhost:8080/write-metrics/nodes/" + node_name + "/example.com~1jitter",
            json=udp_result.jitter_ms)
    del udp_client


def get_node_ip(node):
    node_ip = ""
    for address in node.status.addresses:
        if address.type == "InternalIP":
            node_ip = address.address
    return node_ip


if __name__ == "__main__":
    main()
