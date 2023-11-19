import subprocess
from apscheduler.schedulers.background import BlockingScheduler
from time import sleep
import datetime
import sys
import pytz

# 1. assigning qdisc
"tc qdisc add dev eth0 root handle 1: hfsc"
# 2. create class hierarchy
"tc class add dev eth0 parent 1: classid 1:1 hfsc sc rate 100mbit ul rate 100mbit"
"tc qdisc add dev eth0 parent 1:1 handle 2 netem delay 150ms"

# oder:
# enp0s3
"tc qdisc add dev enp0s3 root handle 1:0 htb"
"tc class add dev enp0s3 parent 1:0 classid 1:1 htb rate 1mbit ceil 1.5mbit"
"tc qdisc add dev enp0s3 parent 1:1 handle 10:0 netem delay 150ms"

def delete_netem():
    result = subprocess.run(["tc", "qdisc", "del", "dev", "eth0", "root", "netem"])
    if result.stderr:
        print(result.stderr)

    print("netem deleted")


def create_network_traffic(delay, rate):
    print("network emulation started")
    buf_pkts = 33
    bdp_bytes = (delay / 1000.0) * (rate * 1000000.0 / 8.0)
    bdp_pkts = bdp_bytes / 1500
    limit_pkts = str(bdp_pkts + buf_pkts)
    delay_ms = "".join([str(delay), "ms"])
    rate_mbit = "".join([str(rate), "Mbit"])
    print("delay: {0} rate: {1}", delay_ms, rate_mbit)
    subprocess.run(["tc", "qdisc", "add", "dev", "eth0", "root", "netem", "delay", delay_ms, "rate", rate_mbit, "limit",
                    limit_pkts])
    print("delay: {0} rate: {1}", delay_ms, rate_mbit)


def change_network_traffic(delay, rate):
    buf_pkts = 33
    bdp_bytes = (delay / 1000.0) * (rate * 1000000.0 / 8.0)
    bdp_pkts = bdp_bytes / 1500
    limit_pkts = str(bdp_pkts + buf_pkts)
    delay_ms = "".join([str(delay), "ms"])
    rate_mbit = "".join([str(rate), "Mbit"])
    subprocess.run(
        ["tc", "qdisc", "replace", "dev", "eth0", "root", "netem", "delay", delay_ms, "rate", rate_mbit, "limit",
         limit_pkts])
    print("delay: {0} rate: {1}", delay_ms, rate_mbit)
def network_traffic():
    delete_netem()
    create_network_traffic(0, 100000)
    sleep(12)

    rate = 90000
    for latency in range(10, 110, 100):
        change_network_traffic(latency, rate)
        rate = rate - 10000
        sleep(62)

    sleep(60)

    delete_netem()

if __name__ == "__main__":
    today = datetime.datetime.now().astimezone(pytz.timezone('Europe/Berlin'))
    year = int(today.year)
    month = int(today.month)
    day = int(today.day)

    hour = int(sys.argv[1])
    minute = int(sys.argv[2])

    scheduler = BlockingScheduler()
    scheduler.add_job(network_traffic, 'date', run_date=datetime.datetime(year, month, day, hour, minute, 0),
                      timezone='Europe/Berlin')
    scheduler.start()
