# Space Launch Now
## Web Deployment

###Pre-Requisites

* Docker v18.09.7+
* Docker Compose v1.24.1+
* Access to registry.calebjones.dev
* SSL certs via Certbot at /etc/letsencrypt

###Certbot

* AWS Creds for SLN Route 53 at ~/aws/config
* Certbot/Route53 plugin
* Run 'sudo certbot certonly --dns-route53 --email renewals@spacelaunchnow.me --agree-tos -d *.spacelaunchnow.me -d spacelaunchnow.me' 

###Scaling
Edit the docker-compose to fit the size of the VM's being used, change workers and threads of each web instance.