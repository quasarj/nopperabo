.PHONY: build

default: build

masker/dist/masker-1.0.0-py3-none-any.whl:
	cd masker && \
	rye build

build: Dockerfile masker/dist/masker-1.0.0-py3-none-any.whl
	docker build . -t tcia/nopperabo:0

run: 
	docker run \
		-it \
		-v ${PWD}:/scripts \
		--network oneposda_default \
		--rm \
		tcia/nopperabo:0

bash:
	docker run \
		-it \
		-v ${PWD}:/scripts \
		--network oneposda_default \
		tcia/nopperabo:0 bash
