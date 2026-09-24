.PHONY: examples check paper reproduce

examples:
	python3 -m examples.run --output-dir results

check:
	python3 -m unittest discover -s tests -v

paper: paper/paper.pdf

paper/paper.pdf: paper/paper.md paper/references.md results/summary.md
	pandoc paper/paper.md paper/references.md results/summary.md \
		--standalone --pdf-engine=xelatex \
		-V 'monofont=DejaVu Sans Mono' -V 'monofontoptions=Scale=0.75' \
		-o paper/paper.pdf

reproduce: examples check
	$(MAKE) paper
