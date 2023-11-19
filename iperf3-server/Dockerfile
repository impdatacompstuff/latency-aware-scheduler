FROM python:3.6-slim
RUN apt-get update && apt -y install iperf3 && pip3 install iperf3
ADD main.py /
CMD python3 /main.py