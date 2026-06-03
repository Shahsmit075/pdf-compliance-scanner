import fitz  # PyMuPDF
import sys
import os

def render_pdf(pdf_path, output_dir):
    print(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    if len(doc) == 0:
        print("Error: PDF has no pages!")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        img_path = os.path.join(output_dir, f"page_{page_num}.png")
        pix.save(img_path)
        print(f"Page {page_num} rendered and saved to: {img_path}")

if __name__ == "__main__":
    pdf_p = sys.argv[1] if len(sys.argv) > 1 else "scratch/test_output.pdf"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "scratch/rendered_pages"
    render_pdf(pdf_p, out_dir)
