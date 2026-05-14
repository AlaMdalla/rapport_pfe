Fast compile options
====================

Quick build (draft images):

1. Open `main.tex` and ensure the following toggle is set near the graphics packages:

   ```tex
   \newif\iffastcompile
   \fastcompiletrue
   \usepackage{graphicx}
   \iffastcompile
     \setkeys{Gin}{draft=true}
   \fi
   ```

2. Compile normally (this will replace images with bounding boxes and is much faster):

   ```bash
   pdflatex -interaction=nonstopmode -halt-on-error main.tex
   bibtex main || true
   pdflatex main.tex
   pdflatex main.tex
   ```

Final build (full images):

1. Edit `main.tex` and set `\fastcompilefalse`.
2. Re-run the compile commands above to produce the final PDF with images.

Notes:
- Quoting filenames with spaces is handled in the sources (e.g. `"img/archi/single-root related-work-item processing.png"`).
- For the fastest iteration keep `\fastcompiletrue` during writing and switch to `\fastcompilefalse` for the final run.

Compress images before use
-------------------------

You can compress and optimize images into `img/optimized` before generating the final PDF. This preserves originals and reduces compile time and PDF size.

1. Create a virtualenv and install requirements:

```bash
python -m venv .venv
source .venv/bin/activate   # on Windows use `.venv\Scripts\activate`
pip install -r requirements.txt
```

2. Run the compressor (example):

```bash
python scripts/compress_images.py --src img --dst img/optimized --quality 85 --png-palette
```

3. Update image includes to point to `img/optimized/...` (or change the `--dst` to `img` with `--overwrite` if you prefer in-place replacement).

The script supports `--max-width` and `--max-height` to downscale very large images.
