# See ARCHITECTURE.md for scope and validation constraints.

all:
	@printf '%s\n' 'Use make test; installation and activation are not enabled.'

test:
	@sh tests/run.sh

patch:
	@sh scripts/export-patches.sh "$(PROJECT)" "$(FEATURE)"

patches: patch

.PHONY: all test patch patches
