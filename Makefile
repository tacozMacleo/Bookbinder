PY_ENV=env

install:
	python3.11 -m venv ${PY_ENV}
	${PY_ENV}/bin/pip install -r requirements.txt

test-page:
	pdflatex --output-directory ./latex/. ./latex/test_page.tex 
	pdflatex --output-directory ./latex/. ./latex/test_page.tex 
	mv ./latex/test_page.pdf .

clean-all:
	rm --force --recursive ${PY_ENV}
	rm --force --recursive *.pdf
	rm --force --recursive latex/*.aux
	rm --force --recursive latex/*.log
	rm --force --recursive latex/*.pdf
	rm --force --recursive .pytest_cache
	find . -name '__pycache__' -exec rm --force --recursive  {} +
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
