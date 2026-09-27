# Chapter 15 diagrams

`generate_diagrams.py` stores one deterministic scene model for each figure and renders it twice:

- editable `.tldr` source files in this directory;
- self-contained SVG files in `book/images/chapter15/`.

Regenerate from the repository root:

```powershell
python -B -m infographic.chapter15.generate_diagrams
```

The cream paper, hand-drawn navy outline and blue/green/violet/orange sections follow the book's existing visual system. All labels and arrows are vector-rendered from controlled text; no external font, image, credential, model response or raster payload is embedded.

