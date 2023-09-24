prepare:
	test -d .venv || python -m venv .venv
	.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
	yarn install
lint:
	PATH=./node_modules/.bin:$PATH SKIP=pytest,biome,taplo pre-commit run --all-files
test:
	.venv/bin/pytest
deploy:
	#!/bin/sh
	cd ~/src/bin/booklogger || exit 1
	old_id="$(git rev-parse HEAD)"
	git pull
	new_id="$(git rev-parse HEAD)"
	if [ $old_id != $new_id ]; then
		doas /usr/sbin/rcctl restart booklogger
	fi
