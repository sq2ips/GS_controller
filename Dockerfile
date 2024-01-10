FROM ubuntu:22.04

RUN apt-get update && apt-get install -y python3-pip python3-wxgtk4.0 && apt-get autoremove && apt-get clean
RUN pip3 install pyserial

WORKDIR /workspace

COPY . .

CMD [ "python3", "sp2wie_main.py" ]