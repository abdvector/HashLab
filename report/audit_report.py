"""Structural and rendered-PDF checks for the report."""

from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from pypdf import PdfReader
import pdfplumber

root=Path(__file__).resolve().parents[1]
docx=root/'output/report/HashLab_Project_Report.docx'
pdf=docx.with_suffix('.pdf')
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(docx) as z:
    styles=etree.fromstring(z.read('word/styles.xml'))
    for style in styles.findall('w:style',ns):
        if style.get('{'+ns['w']+'}styleId') in ['Title','Heading1','Heading2','Caption']:
            print(etree.tostring(style,pretty_print=True).decode()[-2400:])
    document=etree.fromstring(z.read('word/document.xml'))
    print('Paragraph borders',len(document.findall('.//w:pBdr',ns)))
    print('Inline pictures',len(document.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline')))
r=PdfReader(pdf)
print('Pages',len(r.pages))
with pdfplumber.open(pdf) as pages:
    for i,page in enumerate(pages.pages,1):
        chars=[c for c in page.chars if c['text'].strip()]
        escaped=[c for c in chars if c['x0']<45 or c['x1']>page.width-42 or c['top']<30 or c['bottom']>page.height-17]
        if escaped:
            print('Margin warnings',i,[(c['text'],round(c['x0']),round(c['top'])) for c in escaped[:10]])
        if i==1:
            print('First-page fonts',sorted(set(c['fontname'] for c in chars)))
