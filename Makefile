NAMESPACE=trade-flow

build:
	docker build -f Dockerfile -t fortesenselabsmt .

run: build
	docker run --rm -dit -p 9000:9000 --name fortesenselabsmt -v fortesenselabsmt:/data fortesenselabsmt

shell: 
	docker exec -it fortesenselabsmt sh

users: build
	docker exec -it fortesenselabsmt adduser novouser
	
startkube:
	minikube start

stopkube:
	minikube stop

delete:
	kubectl delete --all deployments
	minikube delete