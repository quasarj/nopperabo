.PHONY: build

build: Dockerfile
	docker build . -t tcia/nopperabo:0


run: 
	docker run \
		-it \
		-v ${PWD}:/scripts \
		--network oneposda_default \
		tcia/nopperabo:0

bash:
	docker run \
		-it \
		-v ${PWD}:/scripts \
		--network oneposda_default \
		tcia/nopperabo:0 bash
