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
		--rm \
		tcia/nopperabo:0 --hostname tcia-posda-rh-1.ad.uams.edu --token e9a63bc2-bfa5-4299-afb3-c844fb2ef38b --debug true

test:
	docker run \
		-it \
		--rm \
		tcia/nopperabo:0 --help
bash:
	docker run \
		-it \
		-v ${PWD}:/scripts \
		--network oneposda_default \
		tcia/nopperabo:0 bash
