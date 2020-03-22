bdist:
	python setup.py bdist_wheel

clean:
	rm -rf dist
	rm -rf build
	rm -rf quakestats.egg-info

lint:
	flake8 quakestats

test: lint
	cd tests && py.test

release: test bdist

changelog:
	gitchangelog > CHANGELOG.MD

git_hooks:
	@if ! [[ -L .git/hooks/pre-commit ]]; then \
		echo "Installing git pre-commit hook"; \
		ln -fs ../../git/pre-commit .git/hooks/pre-commit; \
	fi
