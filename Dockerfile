FROM centos:7.4.1708

MAINTAINER kiop <nick028@foxmail.com>

# set timezone
RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo 'Asia/Shanghai' >/etc/timezone

# add repos
##  add php 7x / mysql / epel repos
#ADD ./files/repos/ /etc/yum.repos.d/

# install php , apache
RUN \
    yum -y install \
        ## add ssh
        openssl openssh-server \
        ## add tools
        install net-tools \
        ## add wget
        wget \
        ## add bzip2
        bzip2 \
        ## python \
        epel-release && \
    yum -y install \
        ## add suprevisor pip
        python2-pip supervisor

## config ssh
RUN \
    ssh-keygen -q -t rsa -b 2048 -f /etc/ssh/ssh_host_rsa_key -N '' \
    && ssh-keygen -q -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -N '' \
    && ssh-keygen -t dsa -f /etc/ssh/ssh_host_ed25519_key  -N '' \
    && sed -i "s/#UsePrivilegeSeparation.*/UsePrivilegeSeparation no/g" /etc/ssh/sshd_config \
    && sed -i "s/UsePAM.*/UsePAM no/g" /etc/ssh/sshd_config \
    && echo 1 | passwd --stdin root \
    && echo root:1|chpasswd

## add pip
ADD files /root/.pip/pip.conf

## add modules
RUN \
    pip install flask-restplus requests

# add files to wwwroot
ADD ./src/  /root/flask

## add supervisor file
ADD files /etc/supervisord.conf

## add start script
ADD files /root/start.sh

WORKDIR /var/www/html/

CMD ["/bin/bash","/root/start.sh"]
