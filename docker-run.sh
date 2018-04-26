set -e

#nginx will run as a deamon
nginx 

#flask will run interactively
python /usr/share/nginx/server.py

