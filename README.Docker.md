# Running containerized application

## Prerequisities

Since serial devices are mounted so that only root users can access the device add udev rule that make them readable for all users. On your host machine create a file named `/etc/udev/rules.d/99-serial.rules`. Add following line to this file: `KERNEL=="ttyUSB[0-9]*",MODE="0666"`

To give access to your xserver run: `$ xhost +`

## Running the application

When all this is done you can run the containerized application:

```
$ docker compose up
```

If you would like to run using docker cli first you need to build the image:

```
$ docker build -t groundstation:latest .
```

When it's done run:
```
$ docker run --rm --network host -env DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v /dev:/dev groundstation:latest
```

Still having problems accessing the serial device in `/dev`? Add the `--privileged` flag to above command.