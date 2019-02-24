docker_name=strack_git_hook
docker_tag=test/$(docker_name)
# restart ->  always , no
docker_restart_policy=always
net_type=mcv
net_ip=192.168.31.210
port=80
supervisord=9000

#bin
chrome_bin="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

# echo helps
help:
	@echo 'Here is the command list:'
	@echo '------------------------'
	@cat Makefile |grep '^\w.*:$$'

ssh:
	@ssh root@$(net_ip)

view:
	@start '' $(chrome_bin) $(net_ip):$(port)/login

view_supervisord:
	@start '' $(chrome_bin) $(net_ip):$(supervisord)

build:
	@docker build . -t $(docker_tag)

create_no_bridge:
	@docker run -d --restart=${docker_restart_policy} --name $(docker_name) \
		$(docker_tag)

create:
	@docker run -d --restart=${docker_restart_policy} --name $(docker_name) \
		--net=$(net_type) --ip=$(net_ip) \
		$(docker_tag)

connect_bridge:
	@docker network connect bridge ${docker_name}

stop:
	@docker stop $(docker_name)

start:
	@docker start $(docker_name)

restart:
	@docker restart $(docker_name)

enter:
	@docker exec -it $(docker_name) /bin/bash

up:
	@make build
	@make create

force-up:
	@make down
	@make up

down:
	@make stop
	@make rm

rm:
	@docker rm $(docker_name)

log:
	@docker logs $(docker_name)



