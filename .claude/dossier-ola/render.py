"""Rend un HTML en PDF via Chrome headless, puis en PNG pour relecture."""
import os, subprocess, sys, shutil, tempfile
import fitz

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HERE = os.path.dirname(os.path.abspath(__file__))

def to_pdf(html, pdf, budget=15000):
    html_abs = os.path.abspath(html)
    pdf_abs = os.path.abspath(pdf)
    url = "file:///" + html_abs.replace("\\", "/")
    profile = os.path.join(tempfile.gettempdir(), "mbc-chrome-deck")
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
           "--allow-file-access-from-files", "--font-render-hinting=none",
           "--hide-scrollbars", "--force-color-profile=srgb",
           f"--user-data-dir={profile}",
           f"--print-to-pdf={pdf_abs}", f"--virtual-time-budget={budget}", url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    if not os.path.exists(pdf_abs):
        print("STDERR:", r.stderr[-2000:]); sys.exit(1)
    return pdf_abs

def report(pdf, png_dir=None, dpi=110):
    d = fitz.open(pdf)
    print(f"{os.path.basename(pdf)} : {d.page_count} pages")
    for i, p in enumerate(d):
        print(f"  p{i+1:02d} {p.rect.width:.2f}x{p.rect.height:.2f} pt "
              f"({p.rect.width/72:.4f}x{p.rect.height/72:.4f} in)")
    fonts = sorted({f[3] for pg in d for f in pg.get_fonts(full=True)})
    print("  polices :", fonts)
    txt = d[0].get_text()[:160].replace("\n", " | ")
    print("  p1 texte :", txt)
    if png_dir:
        os.makedirs(png_dir, exist_ok=True)
        for i, p in enumerate(d):
            p.get_pixmap(dpi=dpi).save(os.path.join(png_dir, f"p{i+1:02d}.png"))
        print(f"  PNG -> {png_dir} ({dpi} dpi)")
    return d

if __name__ == "__main__":
    html = sys.argv[1] if len(sys.argv) > 1 else "test.html"
    pdf = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(html)[0] + ".pdf"
    out = sys.argv[3] if len(sys.argv) > 3 else None
    to_pdf(html, pdf)
    report(pdf, out)
