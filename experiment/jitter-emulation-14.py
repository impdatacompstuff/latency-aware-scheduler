import subprocess
from apscheduler.schedulers.background import BlockingScheduler
from time import sleep
import datetime
from datetime import date 
import sys
import pytz

def delete_netem():
    result = subprocess.run(["tc", "qdisc", "del", "dev", "eth0", "root", "netem"])
    if result.stderr:
        print(result.stderr)

    print("netem deleted")


def create_network_traffic(delay, jitter):
    print("jitter emulation started")
    delay_ms = "".join([str(delay), "ms"])
    jitter_ms = "".join([str(jitter), "ms"])
    print("delay: {0} jitter: {1}", delay_ms, jitter_ms)
    # TODO: is node ip changed?
    subprocess.run(["tc", "qdisc", "add", "dev", "eth0", "root", "netem", "delay", delay_ms, jitter_ms])


def change_network_traffic(delay, jitter):
    delay_ms = "".join([str(delay), "ms"])
    jitter_ms = "".join([str(jitter), "ms"])
    print("delay: {0} jitter: {1}", delay_ms, jitter_ms)
    subprocess.run(["tc", "qdisc", "replace", "dev", "eth0", "root", "netem", "delay", delay_ms, jitter_ms])
    print("delay: {0} jitter: {1}", delay_ms, jitter_ms)


def network_traffic():
    delete_netem()
    create_network_traffic(0, 100)
    sleep(10)

    latency = 0
    for jitter in range(90, -10, -10):
        change_network_traffic(latency, jitter)
        sleep(10)

    delete_netem()


if __name__ == "__main__":
    today = datetime.datetime.now().astimezone(pytz.timezone('Europe/Berlin'))
    year = int(today.year)
    month = int(today.month)
    day = int(today.day)

    hour = int(sys.argv[1])
    minute = int(sys.argv[2])

    scheduler = BlockingScheduler()
    scheduler.add_job(network_traffic, 'date', run_date=datetime.datetime(year, month, day, hour, minute, 0), timezone='Europe/Berlin')
    scheduler.start()
    