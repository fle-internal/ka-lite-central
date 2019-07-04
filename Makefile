setup:
	cd centralserver; python manage.py setup

clean:
	docker container prune -f --filter "label=kalitecentral"
	docker image prune -f --filter "label=kalitecentral"

UID := $(shell id -u)
GID := $(shell id -g)
PWD := $(shell pwd)

docker-build:
	docker build -t "kalitecentral" --build-arg buildtime_uid=$(UID) --build-arg buildtime_gid=$(GID) -f base.dockerfile .

docker-run:
	docker run --user $(UID) -v $(PWD)/:/docker/mnt -it --net host "kalitecentral"

assets: docker-build docker-run
