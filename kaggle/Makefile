COMP=arc-prize-2024

.PHONY: help check-kaggle-cli submissions-list dataset-update

default: help

help:
	@echo "== Docs: https://github.com/Kaggle/kaggle-api/blob/main/docs/README.md =="
	@echo "== Available targets: =="
	@grep -oP '^[a-zA-Z0-9_-]+(?=:)' Makefile | sort -u

help-create:
	@echo "== To create a dataset: =="
	@echo "cd arc"
	@echo "kaggle datasets init -p rbc/"
	@echo "(then edit rbc/dataset-metadata.json)"
	@echo "rm -rf rbc/__pycache__"
	@echo "kaggle datasets create -p rbc/  --keep-tabular -r tar"

check-kaggle-cli:
	@command -v kaggle >/dev/null 2>&1 || { echo >&2 "Kaggle CLI is not installed. Please install it to proceed."; exit 1; }
	@kaggle competitions list >/dev/null 2>&1 || { echo >&2 "Kaggle CLI is not responding. Please check your ~/.kaggle and network."; exit 1; }
	@echo Kaggle CLI is installed and works fine!

submissions-list: check-kaggle-cli
	kaggle competitions submissions $(COMP)

push: check-kaggle-cli
ifeq ($(msg),)
	$(error "Error: 'msg' is not defined. Please define 'msg' like so: make push msg='Add boolfunc.py'")
endif
	# if [ -n "$$(git status --porcelain)" ]; then \
	# 	read -p "The git repo seems unclean, proceed? (y/n) " ans; \
	# 	echo $$yn; \
	# 	ans=$${ans:-n} && 
	# else \
	# 	git rev-parse HEAD > rbc-src/rbc/commit_sha.txt
	kaggle datasets version -d -p rbc-src -r tar -m "$(msg)"

degit: ## removes .git and change it to .git-orig
	@find etc/ -type d -name ".git" -execdir mv {} {}-orig \; -prune

engit: ## creates .git
	@find etc/ -type d -name ".git-orig" -execdir sh -c 'mv "$$1" "$$(echo $$1 | sed "s/-orig//")"' _ {} \; -prune