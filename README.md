# Social Media Marketplace
This project was made for course "Foundation of Computer Security" hence the whole website is made and the setup is done with security in mind.  
For this repository, I have changed few things and have not included the fail2ban setup here.

### Overview
- **Frontend**: React application served via NGINX.
- **Backend**: Django application with ASGI support for WebSockets.
- **Caching**: Redis for caching and WebSocket support.
- **Production-Ready**: Configured with NGINX, Docker, and security headers.
- **Environment Variables**: Securely manage sensitive data using .env.
- **Security**: Implements security headers, CORS policies, and non-root user configurations.
- **Scalable**: Easily deployable with Docker Compose.

### Security
-	Frontend, backend and Redis (for messaging) is running under container, so it is very hard to break out of the container.
-	The website runs on HTTPS with TLS 1.2/1.3
-	Web is running on Nginx with many security configuration along with its default.
-	If there are too many request from the same IP address to the server in a certain time limit, user would receive “Too many request” error.
-	Any attachment (apart from message attachment image and videos) can only max be of 2MB.
-	No suspicious file upload would be allowed, eg. php, exe, sh, etc.
-	All the passwords are stored as hashes with salt.
-	Messages and attachments use public/private keys with RSA cryptography for encryption.
-	Only localhost ports are available to the backend port or redis or container.
-	and a lot more.....

### Notes
- Media files are stored in /var/www/media on the host machine.
- The backend service waits for Redis to be ready before starting.
- WebSocket support is enabled for real-time features.

### Setup
1.	Download nginx, nginx-common, docker, python, docker-compose, postgresql package for Ubuntu.
2.	In /etc/nginx/nginx.conf put the nginx.conf file from the front-facing-nginx-conf dir.
3.	Now setup postgresql and connect it to the Django backend by putting its detail in the settings.py
4.	Create an .env file in the root dir  
   `SECRET_KEY=your_django_secret_key
  	DB_NAME=your_database_name
  	DB_USER=your_database_user
  	DB_PASSWORD=your_database_password
  	EMAIL_HOST_USER=your_email_user
  	EMAIL_HOST_PASSWORD=your_email_password
  	ENCRYPTION_KEY=your_encryption_key`  
6.	Now run following on the root dir  
`$ sudo systemctl start docker  
$ docker-compose –f docker-compose.prod.yaml up –build  `
(This would build and start the containers for frontend, backend and redis)
7.	Create a superuser admin in django container
$ docker-compose exec backend python manage.py createsuperuser 
