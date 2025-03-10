# Image

**'image'** is a lightweight, stand-alone, and executable package including everything needed to run a piece of software: the code, runtime, libraries, environment variables, and dependencies.

### view available images:
`>> docker images` 
`REPOSITORY   TAG       IMAGE ID   CREATED   SIZE`

### create image
`>> docker build -t <IMAGE_TAG_NAME>:<VERSION> <DOCKERFILE_DIRECTORY>`

- `-t` : assign tag
- `-o` : Output destination
- `-f` : Name of the Dockerfile (default: "PATH/Dockerfile")
### delete image:
`>> docker rmi <image_id_or_repository:tag>`
- `-f`: force remove
### remove All Unused Images:
`>> docker image prune
- `-a`: **all unused images** (not just dangling ones)

# Container

- Isolated environment with own filesystem, networking, and process space, but it shares the host's OS kernel. 
- A **container** is a running instance of a Docker image. It is the execution environment where your application runs.
- **Can be Started, Stopped, and Deleted**: You can stop a container (it goes into a "stopped" state), restart it, or delete it.
- ##### **IMPORTANT**: Stopping or restarting container resets its data.
### view containers:
`>> docker ps`
`CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAME`

- `-a`: list all
### create container from an image:
`>> docker run -p <exposed_port_outside>:<inside_port_to_attach> <image_tag_name>:<version>`

- **`-d`**: Runs the container in the background (detached mode) {will print a long string i.e. contianer_id}
- `-p` : binds the port 'outside_port':'inside_port'
### stop container:
`>> docker stop <contianer-id>

### remove container:
`docker rm <contianer-id1> <contianer-id2>`
### logs:
`>> docker logs <container_id_or_name>`

# Volume

- To create persistence, like when using database. When we change/stop/restart or use different container, even may it have mysql, it wouldn't have the data that was in previous database.

Types of volumes:
1. Mapped volume
`>> docker run -v <host_vol_dir>:<container_vol_dir>`
	Specified target container directory for volume

2. Anonymous volume
`docker run -v <container_vol_dir>
	Docker would automatically create a persistent host dir under `/var/lib/docker/volumes/random-hash/_data`

3. Named volume
`docker run -v <name>:<container_vol_dir>
	Similar to anonymous but here we can use it by name as it wouldn't be a random-hash, such as create a volume `-v db-data:/var/lib/mysql/data


# Dockerfile

Just an example:
`FROM python:3.9-slim
``
`WORKDIR /app
`COPY index.html /app/index.html
`COPY favicon.ico /app/favicon.ico
`COPY server.py /app/server.py

`EXPOSE 6969

`CMD python server.py


