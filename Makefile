# Makefile -- Make It Parallel companion code.
# make         build every chapter's C programs
# make check   check the tools, then run the quick tests (under a minute)
# make cuda    build the CUDA programs (needs NVIDIA's nvcc)
# make clean   remove everything make built

DIRS = $(patsubst %/Makefile,%,$(wildcard code/*/Makefile))

all:
	@for d in $(DIRS); do $(MAKE) -s -C $$d all || exit 1; done
	@echo "built every chapter"

check: all
	sh code/appA/check_tools.sh
	sh tests/quick_checks.sh

cuda:
	$(MAKE) -C code/heatsim cuda
	$(MAKE) -C code/ch14 cuda

clean:
	@for d in $(DIRS); do $(MAKE) -s -C $$d clean; done

.PHONY: all check cuda clean
