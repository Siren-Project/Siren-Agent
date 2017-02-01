From python:2.7

RUN pip install requests
RUN pip install netifaces
RUN pip install IPy
RUN pip install uptime
RUN pip install pyping
RUN pip install iperf3
RUN apt-get install iperf3
ADD Agent.py /
ADD config.json /
CMD python /Agent.py
