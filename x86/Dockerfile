FROM alpine:latest

RUN apk add --no-cache python
RUN apk add --no-cache python-dev
RUN apk add --no-cache py-pip
RUN apk add --no-cache build-base
RUN apk add --no-cache git
RUN apk add --no-cache musl-dev
RUN apk add --no-cache linux-headers
RUN pip install requests
RUN pip install netifaces
RUN pip install IPy
RUN pip install uptime
RUN pip install pyping

RUN git clone https://github.com/lyndon160/Siren-Agent.git

CMD cd Siren-Agent && python Agent.py
