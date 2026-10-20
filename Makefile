all:
	@printf '%s\n' 'Use make test to validate; make install installs without activating a session.'

install:
	@sh scripts/install.sh

test:
	@sh tests/run.sh

patch:
	@sh scripts/export-patches.sh "$(PROJECT)" "$(FEATURE)"

patches: patch

.PHONY: all install test patch patches
