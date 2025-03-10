`version: '3.8'
`services:
``  app1:
``    build: .        # This tells Docker Compose to use the Dockerfile in the same directory
``    environment:
``      - APP_NAME=app_0.1
``    ports:
``      - "4200:6969"
`    volumes:`
`      - db-data:/var/lib/mysql/data
` ....                              `
` ....                              `
`volumes:`
`    db-data`

Create using `docker-compose up --build`
Stop and end all the containers of a specific docker-compose `docker-compose down`

Uses [[Docker]].

To create image and start container in detached mode and write all logs to a file.
`$ docker-compose up --build -d &> docker.log
