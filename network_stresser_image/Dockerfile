FROM ubuntu:16.04
MAINTAINER eranra@il.ibm.com


COPY utils.py /usr/bin/utils.py
RUN chmod 777 /usr/bin/utils.py

COPY traffic_generator.py /usr/bin/traffic_generator.py
RUN chmod 777 /usr/bin/traffic_generator.py

COPY traffic_receiver.py /usr/bin/traffic_receiver.py
RUN chmod 777 /usr/bin/traffic_receiver.py

COPY traffic_receiver_tcp.py /usr/bin/traffic_receiver_tcp.py
RUN chmod 777 /usr/bin/traffic_receiver_tcp.py

COPY traffic_receiver_udp.py /usr/bin/traffic_receiver_udp.py
RUN chmod 777 /usr/bin/traffic_receiver_udp.py


RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y python2.7

