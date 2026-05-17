import PyPDF2
from pathlib import Path

pdf_path = Path(r'c:\Users\raoui\OneDrive\Bureau\TechKids\techkids-hub\pfe (5).pdf')
out_path = Path('pfe_extracted.txt')

reader = PyPDF2.PdfReader(str(pdf_path))
pages = [page.extract_text() or '' for page in reader.pages]
text = '\n\n'.join(pages)

out_path.write_text(text, encoding='utf-8')
print(f'Extracted {len(pages)} pages to {out_path}')
