bdist:
	python setup.py bdist_wheel

clean:
	rm -rf dist
	rm -rf build

test:
	cd tests && py.test

release: test bdist
