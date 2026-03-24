LATEXMK ?= latexmk
LATEXMKRC := $(CURDIR)/latexmkrc

.PHONY: memo clean

memo:
	mkdir -p build
	cd memo && $(LATEXMK) -r $(LATEXMKRC) memo.tex

clean:
	$(LATEXMK) -r $(LATEXMKRC) -C memo/memo.tex
	rm -rf build
