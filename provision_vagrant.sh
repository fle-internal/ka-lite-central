#!/bin/sh
curl -sL https://deb.nodesource.com/setup_0.12 | bash -
echo 'mysql-server mysql-server/root_password password root' | debconf-set-selections
echo 'mysql-server mysql-server/root_password_again password root' | debconf-set-selections
apt-get update
apt-get install -yqq nodejs mysql-server-5.5 git-core python-mysqldb python python-pip python-dev libmysqlclient-dev
apt-get upgrade -y
easy_install -U pip

# Set up mysql user. Highly insecure.
mysql -uroot -proot -e "CREATE USER 'dbuser'@'localhost' IDENTIFIED BY 'pass';"
mysql -uroot -proot -e "GRANT ALL PRIVILEGES ON * . * TO 'dbuser'@'localhost'; FLUSH PRIVILEGES;"
mysql -udbuser -ppass -e "CREATE DATABASE kalite_central_server;"

cd /vagrant/

npm install
npm install -g grunt-cli

pip install -r requirements.txt

echo "DEBUG=True" >> centralserver/local_settings.py
