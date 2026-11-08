.PHONY: test check status demo eval
test:
	pytest -q
check:
	python scripts/check_ownership.py --range HEAD~1..HEAD
	bash scripts/check_network.sh
status:
	python scripts/build_status.py
demo:
	DEMO=1 uvicorn app:app --reload
eval:
	python -m eval.run_all
