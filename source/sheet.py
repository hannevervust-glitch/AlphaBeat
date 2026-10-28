import json
from PIL import Image, ImageDraw, ImageFont
T=json.load(open('out/nodes.json')); Lj=json.load(open('letters.json'))
mono=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',15)
big=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',34)
cw,ch,cols=520,430,4; rows=9
im=Image.new('RGB',(cols*cw+40,rows*ch+40),'white'); d=ImageDraw.Draw(im)
s=0.30
for i,c in enumerate([k for k in Lj if not k.startswith('_')]):
    ox=30+(i%cols)*cw; oy=20+(i//cols)*ch
    Y=lambda y: oy+40+(750-y)*s
    for lv,y in [('T',750),('I',625),('X',500),('M',250),('B',0),('D',-250)]:
        d.line([(ox,Y(y)),(ox+cw-60,Y(y))],fill=(215,220,225) if lv!='M' else (170,175,180),width=1)
        d.text((ox+cw-55,Y(y)-8),lv,font=mono,fill=(150,150,150))
    w=T[c]['width']; X=lambda x: ox+20+x*s*1.15
    pts=[(X(x),Y(y)) for x,y in T[c]['points']]
    d.line(pts,fill=(0,0,0),width=6,joint='curve')
    for x,y in [(0,250)]+T[c]['nodes']:
        d.ellipse([X(x)-5,Y(y)-5,X(x)+5,Y(y)+5],fill='white',outline=(30,30,30),width=2)
    d.text((ox,oy),c,font=big,fill=(20,20,20))
    recipe=' '.join(f"{k}({x:g},{l})" for k,x,l,*_ in Lj[c])
    lines=[]; cur=''
    for tok in recipe.split(' '):
        if len(cur)+len(tok)>52: lines.append(cur); cur=''
        cur+=tok+' '
    lines.append(cur)
    for j,l in enumerate(lines): d.text((ox,oy+ch-46+j*17),l,font=mono,fill=(70,70,70))
im.save('out/Alphabeat-construction-sheet.png')
