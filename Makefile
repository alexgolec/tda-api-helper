test:
	python3 -m nose $(NOSE_ARGS)

coverage:
	python3 -m coverage run --source=tda_api_helper -m nose
	python3 -m coverage html

clean:
	rm -rf build dist docs-build tda_api.egg-info __pycache__ htmlcov
