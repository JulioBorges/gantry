.PHONY: test release

test:
	python3 -m unittest discover -v

release:
	node scripts/ensure-npm-author.mjs
	npm ci
	npm publish
