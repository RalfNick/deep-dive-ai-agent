# Chapter 14 diagrams

`generate_diagrams.py` contains the single scene model for every figure. The same nodes, labels, colors, coordinates, and edges are rendered into:

- editable `.tldr` sources in this directory;
- self-contained SVG files in `book/images/chapter14/`.

Regenerate from the repository root:

```powershell
.\.venv\Scripts\python.exe -B -m infographic.chapter14.generate_diagrams
```

The diagrams use synthetic teaching data and contain no external resources, raster payloads, credentials, personal identifiers, or hidden reasoning.
