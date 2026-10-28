from PIL import Image, ImageDraw, ImageFont
f=ImageFont.truetype('out/Alphabeat.otf',90); m=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
im=Image.new('RGB',(1500,1110),'white'); d=ImageDraw.Draw(im)
lines=['abcdefghijklm','nopqrstuvwxyz','0123456789','hanne 1984','techno is alive']
y=40
for L in lines:
    d.text((40,y),L,font=m,fill=(120,120,120)); d.text((40,y+30),L,font=f,fill=(0,0,0)); y+=210
im.save('out/specimen.png')
