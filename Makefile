NAMESPACE=trade_flow 

build:
	docker build -f Dockerfile -t trade_flow .

run: 
	docker run -it trade_flow trade_flow-environment

shell: 
	docker exec -it trade_flow-environment sh
	