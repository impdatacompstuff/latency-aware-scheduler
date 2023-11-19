FROM python:3.6-slim
RUN apt-get update && apt-get -y install iperf3
RUN pip3 install --upgrade pip requests kubernetes pythonping iperf3
ADD main.py /
CMD python3 /main.py
