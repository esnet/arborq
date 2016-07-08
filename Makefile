test: init
	venv/bin/py.test tests

init:
	if [ ! -d ./venv ]; then \
		virtualenv --prompt="(arborq)" venv; \
		venv/bin/pip install --upgrade pip; \
		venv/bin/pip install -e .[test]; \
	fi

clean:
	rm -rf ./venv
