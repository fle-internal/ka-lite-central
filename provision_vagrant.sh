#!/bin/sh
curl -sL https://deb.nodesource.com/setup_0.12 | sudo bash -
sudo apt-get update
sudo apt-get install -yqq nodejs mysql-server git-core python-mysqldb python python-dev libmysqlclient-dev
sudo apt-get upgrade -y

# Set up mysql user. Highly insecure.
sudo mysql -e "CREATE USER 'dbuser'@'localhost' IDENTIFIED BY 'pass';"
sudo mysql -e "GRANT ALL PRIVILEGES ON * . * TO 'dbuser'@'localhost'; FLUSH PRIVILEGES;"
sudo mysql -udbuser -ppass -e "CREATE DATABASE 'kalite_central_server';"

sudo npm install
sudo npm install -g grunt-cli

pip install -r requirements.txt

echo 'yes\n' | python centralserver/manage.py setup --noinput -u 'admin' -p 'admin' -o 'Dev Central Server' -d 'A central server instance for development.'
python centralserver/manage.py setup
grunt
