PROJECT?=fortesenselabs/trade_flow
REGISTRY?=ghcr.io/
IMAGE?=${REGISTRY}${PROJECT}
GIT_TAG:=$(shell git rev-parse --abbrev-ref HEAD)
IMAGE_FULL?=${IMAGE}:${GIT_TAG}

.PHONY: install
install:
	BUILD_MODE=release poetry install --with dev,test --all-extras

.PHONY: install-debug
install-debug:
	BUILD_MODE=debug poetry install --with dev,test --all-extras --sync

.PHONY: install-docs
install-docs:
	BUILD_MODE=debug poetry install --with docs

.PHONY: install-just-deps
install-just-deps:
	poetry install --with dev,test --all-extras --no-root

.PHONY: install-just-deps-all
install-just-deps-all:
	poetry install --with dev,test,docs --all-extras --no-root

.PHONY: build
build:
	BUILD_MODE=release poetry run python build.py

.PHONY: build-debug
build-debug:
	BUILD_MODE=debug poetry run python build.py

.PHONY: build-wheel
build-wheel:
	BUILD_MODE=release poetry build --format wheel

.PHONY: build-wheel-debug
build-wheel-debug:
	BUILD_MODE=debug poetry build --format wheel

.PHONY: clean
clean:
	git clean -fxd

.PHONY: format
format:
	(cd nautilus_core && cargo +nightly fmt)

.PHONY: pre-commit
pre-commit:
	pre-commit run --all-files

.PHONY: ruff
ruff:
	ruff check . --fix

.PHONY: outdated
outdated:
	(cd nautilus_core && cargo outdated && poetry show --outdated)

.PHONY: update cargo-update
update: cargo-update
	poetry update
	poetry install --with dev,test --all-extras --no-root

.PHONY: docs
docs: docs-python docs-rust

.PHONY: docs-python
docs-python: install-docs
	poetry run sphinx-build -M markdown ./docs/api_reference ./api_reference

.PHONY: docs-rust
docs-rust:
	(cd nautilus_core && RUSTDOCFLAGS="--enable-index-page -Zunstable-options" cargo +nightly doc --all-features --no-deps --workspace --exclude tokio-tungstenite)

.PHONY: clippy
clippy:
	(cd nautilus_core && cargo clippy --fix --all-targets --all-features -- -D warnings -W clippy::pedantic -W clippy::nursery -W clippy::unwrap_used -W clippy::expect_used)

.PHONY: clippy-nightly
clippy-nightly:
	(cd nautilus_core && cargo +nightly clippy --fix --all-targets --all-features --allow-dirty --allow-staged -- -D warnings -W clippy::pedantic -W clippy::nursery -W clippy::unwrap_used -W clippy::expect_used)

.PHONY: cargo-build
cargo-build:
	(cd nautilus_core && cargo build --release --all-features)

.PHONY: cargo-update
cargo-update:
	(cd nautilus_core && cargo update && cargo install cargo-nextest && cargo install cargo-llvm-cov)

.PHONY: cargo-test
cargo-test:
	@if ! cargo nextest --version >/dev/null 2>&1; then \
		echo "cargo-nextest is not installed. You can install it using 'cargo install cargo-nextest'"; \
		exit 1; \
	fi
	RUST_BACKTRACE=1 && (cd nautilus_core && cargo nextest run --workspace --exclude tokio-tungstenite)

.PHONY: cargo-test-coverage
cargo-test-coverage:
	@if ! cargo nextest --version >/dev/null 2>&1; then \
		echo "cargo-nextest is not installed. You can install it using 'cargo install cargo-nextest'"; \
		exit 1; \
	fi
	@if ! cargo llvm-cov --version >/dev/null 2>&1; then \
		echo "cargo-llvm-cov is not installed. You can install it using 'cargo install cargo-llvm-cov'"; \
		exit 1; \
	fi
	RUST_BACKTRACE=1 && (cd nautilus_core && cargo llvm-cov nextest run --workspace --exclude tokio-tungstenite)

.PHONY: cargo-bench
cargo-bench:
	(cd nautilus_core && cargo bench)

.PHONY: cargo-doc
cargo-doc:
	(cd nautilus_core && cargo doc)

.PHONY: docker-build
docker-build: clean
	docker pull ${IMAGE_FULL} || docker pull ${IMAGE}:nightly ||  true
	docker build -f .docker/trade_flow.dockerfile --platform linux/x86_64 -t ${IMAGE_FULL} .

.PHONY: docker-build-force
docker-build-force:
	docker build --no-cache -f .docker/trade_flow.dockerfile -t ${IMAGE_FULL} .

.PHONY: docker-push
docker-push:
	docker push ${IMAGE_FULL}

.PHONY: docker-build-jupyter
docker-build-jupyter:
	docker build --build-arg GIT_TAG=${GIT_TAG} -f .docker/jupyterlab.dockerfile --platform linux/x86_64 -t ${IMAGE}:jupyter .

.PHONY: docker-push-jupyter
docker-push-jupyter:
	docker push ${IMAGE}:jupyter

.PHONY: start-services
start-services:
	docker-compose -f .docker/docker-compose.yml up -d

.PHONY: stop-services
stop-services:
	docker-compose -f .docker/docker-compose.yml down

.PHONY: pytest
pytest:
	bash scripts/test.sh

.PHONY: pytest-coverage
pytest-coverage:
	bash scripts/test-coverage.sh

.PHONY: test-examples
test-examples:
	bash scripts/test-examples.sh

.PHONY: install-talib
install-talib:
	bash scripts/install-talib.sh

.PHONY: install-nautilus-cli
install-cli:
	(cd nautilus_core && cargo install --path cli --bin nautilus --force)



# NAMESPACE=trade_flow 

# build:
# 	docker build -f Dockerfile -t trade_flow .

# run: 
# 	docker run -it trade_flow trade_flow-environment

# shell: 
# 	docker exec -it trade_flow-environment sh
	

# GPU_IMAGE?="trade_flow:latest-gpu"
# CPU_IMAGE?="trade_flow:latest"
# SHM_SIZE?="3.0gb" # TODO: Automate me!

# clean:
# 	find . | grep -E '(__pycache__|\.pyc|\.pyo$$)' | xargs rm -rf

# test:
# 	pytest tests/

# test-parallel:
# 	pytest --workers auto tests/

# doctest:
# 	pytest --doctest-modules trade_flow/

# docs-build:
# 	$(MAKE) -C docs html

# docs-clean:
# 	$(MAKE) -C docs clean
# 	rm -rf docs/source/api

# docs-serve:
# 	$(SHELL) -C cd docs/build/html
# 	python3 -m webbrowser http://localhost:8000/docs/build/html/index.html
# 	python3 -m http.server 8000

# build-cpu:
# 	docker build -t ${CPU_IMAGE} .

# build-gpu:
# 	docker build -t ${GPU_IMAGE} . --build-arg gpu_tag="-gpu"

# build-cpu-if-not-built:
# 	if [ ! $$(docker images -q ${CPU_IMAGE}) ]; then $(MAKE) build-cpu; fi;

# build-gpu-if-not-built:
# 	if [ ! $$(docker images -q ${GPU_IMAGE}) ]; then $(MAKE) build-gpu; fi;

# run-notebook: build-cpu-if-not-built
# 	docker run -it --rm -p=8888:8888 -p=6006:6006 -v ${PWD}/examples:/examples --shm-size=${SHM_SIZE} ${CPU_IMAGE} jupyter notebook --ip='*' --port=8888 --no-browser --allow-root ./examples/

# run-docs: build-cpu-if-not-built
# 	if [ $$(docker ps -aq --filter name=trade_flow_docs) ]; then docker rm $$(docker ps -aq --filter name=trade_flow_docs); fi;
# 	docker run -t --name trade_flow_docs --shm-size=${SHM_SIZE} ${CPU_IMAGE} make docs-build && make docs-serve
# 	python3 -m webbrowser http://localhost:8000/docs/build/html/index.html

# run-tests: build-cpu-if-not-built
# 	docker run -it --rm --shm-size=${SHM_SIZE} ${CPU_IMAGE} make test

# run-notebook-gpu: build-gpu-if-not-built
# 	docker run -it --rm -p=8888:8888 -p=6006:6006 -v ${PWD}/examples:/examples --shm-size=${SHM_SIZE} ${GPU_IMAGE} jupyter notebook --ip='*' --port=8888 --no-browser --allow-root /examples/

# run-docs-gpu: build-gpu-if-not-built
# 	if [ $$(docker ps -aq --filter name=trade_flow_docs) ]; then docker rm $$(docker ps -aq --filter name=trade_flow_docs); fi;
# 	docker run -t --name trade_flow_docs --shm-size=${SHM_SIZE} ${GPU_IMAGE} make docs-build && make docs-serve
# 	python3 -m webbrowser http://localhost:8000/docs/build/html/index.html

# run-tests-gpu: build-gpu-if-not-built
# 	docker run -it --rm --shm-size=${SHM_SIZE} ${GPU_IMAGE} make test

# package:
# 	rm -rf dist
# 	python3 setup.py sdist
# 	python3 setup.py bdist_wheel

# test-release: package
# 	python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# release: package
# 	python3 -m twine upload dist/*