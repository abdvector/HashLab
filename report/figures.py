"""Black-and-white vector figures for the ten-page academic report."""

import math
import subprocess
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, white


class Figure:
    def __init__(self, name, width, height, directory):
        self.path = Path(directory) / (name + '.pdf')
        self.height = height
        self.c = canvas.Canvas(str(self.path), pagesize=(width, height))

    def text(self, x, y, text, size=13, bold=False, align='center'):
        self.c.setFillColor(black)
        self.c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
        for i, line in enumerate(text.split('\n')):
            yy = self.height - y - i * size * 1.25
            if align == 'left':
                self.c.drawString(x, yy, line)
            elif align == 'right':
                self.c.drawRightString(x, yy, line)
            else:
                self.c.drawCentredString(x, yy, line)

    def box(self, x, y, w, h, text, size=13):
        self.c.setStrokeColor(black)
        self.c.setFillColor(white)
        self.c.setLineWidth(1)
        self.c.rect(x, self.height-y-h, w, h, stroke=1, fill=1)
        lines = len(text.split('\n'))
        self.text(x+w/2, y+h/2-(lines-1)*size*.625+size*.32, text, size)

    def diamond(self, x, y, w, h, text):
        self.c.setStrokeColor(black)
        self.c.setFillColor(white)
        p = self.c.beginPath()
        for i, (xx, yy) in enumerate([(x+w/2,y),(x+w,y+h/2),(x+w/2,y+h),(x,y+h/2)]):
            (p.moveTo if i == 0 else p.lineTo)(xx, self.height-yy)
        p.close()
        self.c.drawPath(p, stroke=1, fill=1)
        self.text(x+w/2, y+h/2+4, text, 13)

    def arrow(self, points, label=None, label_at=None):
        self.c.setStrokeColor(black)
        self.c.setLineWidth(1)
        for (x1,y1),(x2,y2) in zip(points,points[1:]):
            self.c.line(x1,self.height-y1,x2,self.height-y2)
        (x1,y1),(x2,y2)=points[-2:]
        angle=math.atan2(y2-y1,x2-x1)
        for delta in (-.5,.5):
            self.c.line(x2,self.height-y2,x2-7*math.cos(angle+delta),self.height-y2+7*math.sin(angle+delta))
        if label:
            self.text(*label_at,label,11)

    def save(self):
        self.c.showPage()
        self.c.save()
        subprocess.run(['pdftoppm','-scale-to','2400','-png','-singlefile',str(self.path),str(self.path.with_suffix(''))],check=True,capture_output=True)
        return self.path.with_suffix('.png')


def create_figures(directory, runs):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    paths={}
    f=Figure('collision',620,205,directory)
    for i,k in enumerate([12,23,34]):
        x=25+i*200
        f.box(x,10,170,48,f'Book ID {k}',16)
        f.arrow([(x+85,58),(x+85,94),(310,94),(310,120)])
    f.box(180,120,260,48,'k mod 11 = 1',16)
    f.text(310,195,'Different IDs share a starting index, not an identity.',13)
    paths['collision']=f.save()

    f=Figure('workflow',620,510,directory)
    f.box(215,5,190,40,'Open HashLab',15)
    f.arrow([(310,45),(310,65)])
    f.diamond(220,65,180,65,'Choose task')
    f.arrow([(220,98),(150,98),(150,150)],'Simulator',(150,87))
    f.arrow([(400,98),(470,98),(470,150)],'Comparison',(475,87))
    for x in [35,355]:
        centre=x+115
        f.box(x,150,230,55,'Choose mode, strategy\nand prime capacity' if x==35 else 'Choose capacity, input\ndistribution and target fill')
        f.arrow([(centre,205),(centre,230)])
        f.box(x,230,230,55,'Enter and validate key\nor book details' if x==35 else 'Generate identical keys\nand absent queries')
        f.arrow([(centre,285),(centre,310)])
        f.box(x,310,230,55,'Run the selected\nhash-table operation' if x==35 else 'Run all three strategies\nat the same checkpoints')
        f.arrow([(centre,365),(centre,390)])
        f.box(x,390,230,60,'Show table, trace\nand matching book' if x==35 else 'Show graph and results;\nallow CSV download')
    f.arrow([(35,420),(12,420),(12,177),(35,177)])
    f.arrow([(585,420),(608,420),(608,177),(585,177)])
    f.text(310,490,'Repeat with another operation or comparison.',12)
    paths['workflow']=f.save()

    f=Figure('tombstone',620,170,directory)
    for row,values in enumerate([['12','23','34'],['Deleted','23','34']]):
        y=5+row*85
        f.text(10,y+30,'Before' if row==0 else 'After',13,align='left')
        for i,value in enumerate(values):
            f.box(100+i*135,y,115,57,f'Slot {i+1}\n{value}',14)
    f.arrow([(215,125),(235,125)])
    f.arrow([(350,125),(370,125)])
    f.text(550,107,'Search 34',13)
    f.text(550,127,'continues',12)
    f.text(550,146,'past slot 1',12)
    paths['tombstone']=f.save()

    f=Figure('book_lookup',620,255,directory)
    for y,text in [(5,'Find book ID 23'),(70,'h(23) = 23 mod 11 = 1'),(135,'Compare 12, then 23: full ID match'),(200,'Python Basics  |  Shelf B3')]:
        f.box(90,y,440,43,text,16)
        if y<200:
            f.arrow([(310,y+43),(310,y+65)])
    paths['book_lookup']=f.save()

    f=Figure('results',850,350,directory)
    for panel,distribution in enumerate(['Random keys','Same initial bucket']):
        x0=64+panel*420; y0=55; pw=330; ph=205
        data=runs[distribution+'_0.9']['rows']
        ymax=4 if panel==0 else 50
        f.text(x0+pw/2,24,distribution,18,True)
        f.text(x0,y0-10,'Average insertion comparisons',15,align='left')
        for tick in range(6):
            frac=tick/5; yy=y0+ph*(1-frac)
            f.c.setStrokeColorRGB(.82,.82,.82)
            f.c.setLineWidth(.5)
            f.c.line(x0,f.height-yy,x0+pw,f.height-yy)
            f.text(x0-9,yy+4,f'{frac*ymax:g}',14,align='right')
            f.text(x0+pw*frac,y0+ph+20,f'{frac:.1f}',14)
        for j,strategy in enumerate(['Separate chaining','Linear probing','Double hashing']):
            points=[(x0+r['Load factor']*pw,y0+ph-r['Insertion comparisons']/ymax*ph) for r in data if r['Strategy']==strategy]
            f.c.setStrokeColor(black); f.c.setLineWidth(1.8)
            f.c.setDash([6,4] if j==1 else ([1,4] if j==2 else []))
            for a,b in zip(points,points[1:]):
                f.c.line(a[0],f.height-a[1],b[0],f.height-b[1])
            f.c.setDash([])
            for xx,yy in points:
                f.c.setFillColor(white if j==1 else black)
                if j==0:
                    f.c.circle(xx,f.height-yy,2.8,stroke=1,fill=1)
                elif j==1:
                    f.c.rect(xx-3.5,f.height-yy-3.5,7,7,stroke=1,fill=1)
                else:
                    p=f.c.beginPath(); p.moveTo(xx,f.height-yy+3.5);p.lineTo(xx-3.5,f.height-yy-3);p.lineTo(xx+3.5,f.height-yy-3);p.close();f.c.drawPath(p,stroke=1,fill=1)
        f.text(x0+pw/2,302,'Load factor',15)
    f.text(425,334,'Chaining: solid / circles    Linear: dashed / squares    Double: dotted / triangles',14)
    paths['results']=f.save()
    return paths
