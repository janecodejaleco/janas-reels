#!/usr/bin/env python3
"""JANAS BTC: animated, localized 6x8s Reels. No paid API; GitHub Actions friendly.
These are procedural motion graphics, NOT diffusion-generated AI footage.
"""
import argparse, asyncio, json, math, os, random, shutil, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, features

HERE = Path(__file__).resolve().parent
OUT = HERE/'saida_cinematica'
W,H,FPS,SECS = 720,1280,20,8
ART_Y=630
COLORS={'gold':(255,196,91),'cyan':(73,221,244),'red':(251,93,95)}
FONT_DIR=Path('/usr/share/fonts/truetype/noto')


def call(*cmd):
 p=subprocess.run([str(x) for x in cmd],capture_output=True,text=True)
 if p.returncode: raise RuntimeError(' '.join(map(str,cmd[:4]))+'\n'+p.stderr[-2000:])
 return p.stdout.strip()


def fonts(lang,size,bold=False):
 name='NotoSans'
 suffix='Bold' if bold else 'Regular'
 fallback=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
 options=([fallback] if lang=='he' else [FONT_DIR/f'{name}-{suffix}.ttf'])+[fallback]
 for fn in options:
  if fn.exists():return ImageFont.truetype(str(fn),size)
 return ImageFont.load_default()


def textline(draw,xy,text,font,color,lang='en',anchor=None,stroke_width=0,stroke_fill=None):
 kw={'font':font,'fill':color,'stroke_width':stroke_width}
 if stroke_fill is not None:kw['stroke_fill']=stroke_fill
 if lang=='he' and features.check('raqm'): kw['direction']='rtl'
 if anchor:kw['anchor']=anchor
 draw.text(xy,text,**kw)


def width(draw,text,font,lang):
 kw={'direction':'rtl'} if lang=='he' and features.check('raqm') else {}
 b=draw.textbbox((0,0),text,font=font,**kw)
 return b[2]-b[0]


def wrap(draw,text,font,lang,maxw=605):
 words=text.split();out=[];line=''
 for word in words:
  candidate=(line+' '+word).strip()
  if width(draw,candidate,font,lang)>maxw and line:
   out.append(line);line=word
  else: line=candidate
 if line:out.append(line)
 return out


def fitwrap(draw,text,lang,start=57,maxrows=3,maxw=610):
 for size in range(start,24,-2):
  f=fonts(lang,size,True);lines=wrap(draw,text,f,lang,maxw)
  if len(lines)<=maxrows:return f,lines
 return fonts(lang,25,True),wrap(draw,text,fonts(lang,25,True),lang,maxw)


def alpha(a,b,p):return round(a+(b-a)*p)

def color(c,fac):return tuple(max(0,min(255,int(v*fac))) for v in c)

def glowing_circle(d,x,y,r,c,core=True):
 for mult,fac in [(2.3,.11),(1.8,.16),(1.45,.23),(1.18,.42)]:
  rr=int(r*mult);d.ellipse((x-rr,y-rr,x+rr,y+rr),outline=color(c,fac),width=max(1,int(r*.11)))
 d.ellipse((x-r,y-r,x+r,y+r),outline=c,width=max(2,int(r*.075)))
 if core:d.ellipse((x-r//3,y-r//3,x+r//3,y+r//3),fill=color(c,.68))

def perspective_bill(d,x,y,scale,c):
 ww=int(340*scale);hh=int(205*scale)
 poly=[(x-ww//2+28,y-hh//2),(x+ww//2,y-hh//2-18),(x+ww//2-24,y+hh//2),(x-ww//2,y+hh//2+16)]
 d.polygon(poly,fill=(15,53,55),outline=c,width=6)
 d.line([(x-ww//2+50,y-hh//2+28),(x+ww//2-60,y-hh//2+11)],fill=color(c,.65),width=2)
 f=fonts('pt',72,True);textline(d,(x-123,y-57),'R$ 100',f,(232,238,222))
 for a in range(6):
  yy=y-hh//2+25+a*25
  d.line([(x+ww//2-90,yy),(x+ww//2-48,yy)],fill=(42,111,109),width=2)

def cart(d,x,y,c,t):
 # Parallax market shelves, and a cart with slowly vanishing goods
 for a in range(4):
  xx=x-300+a*180+int(13*math.sin(t*2+a))
  d.rectangle((xx,y-200,xx+85,y-150),outline=color(c,.32),width=3)
  d.rectangle((xx,y-135,xx+85,y-85),outline=color(c,.24),width=3)
 d.line((x-220,y-45,x-160,y-45,x-105,y+110,x+190,y+110),fill=c,width=10,joint='curve')
 d.line((x-120,y+110,x-92,y+172,x+164,y+172,x+190,y+110),fill=color(c,.8),width=6)
 for xx in [x-65,x+142]:glowing_circle(d,xx,y+192,17,c,False)
 for i in range(4):
  ww=62;xx=x-92+i*62
  yy=y-135+int(25*math.sin(t+i*.6));f=1-0.12*i
  d.rounded_rectangle((xx,yy,xx+ww-5,yy+80),radius=8,fill=color(c,.25+f*.20),outline=c,width=3)

def drawn_graph(d,x,y,c,t,n=12):
 pts=[]
 for i in range(n):
  ang=i*math.tau/n+t*.26;radius=210+24*math.sin(t+i*1.2)
  pts.append((int(x+radius*math.cos(ang)),int(y+radius*.73*math.sin(ang))))
 for i,(px,py) in enumerate(pts):
  for j in (1,4):
   tx,ty=pts[(i+j)%n];d.line((px,py,tx,ty),fill=color(c,.19),width=2)
  d.line((px,py,x,y),fill=color(c,.23),width=2)
 for i,(px,py) in enumerate(pts):
  glowing_circle(d,px,py,8 if i%3 else 11,c,True)
 glowing_circle(d,x,y,84,c,False)

def globe(d,x,y,c,t):
 rad=220;glowing_circle(d,x,y,rad,c,False)
 d.ellipse((x-rad+3,y-rad+3,x+rad-3,y+rad-3),fill=(11,30,51),outline=color(c,.45),width=3)
 for i in range(1,7):
  rr=int(rad*math.sin(i*math.pi/7))
  yy=int(y+rad*math.cos(i*math.pi/7))
  d.arc((x-rr,yy-20,x+rr,yy+20),0,180,fill=color(c,.28),width=2)
 for i in [-3,-2,-1,0,1,2,3]:
  xx=int(x+math.cos(i/3*math.pi/2)*rad*.8)
  ww=max(8,int(rad*.18*abs(math.sin(i+.1+t*.12))))
  d.arc((xx-ww,y-rad,xx+ww,y+rad),65,295,fill=color(c,.35),width=2)
 # stylized continent ridges, not geographical boundary claims
 for i in range(19):
  aa=i*.39+t*.065;rx=(118+27*math.sin(i*1.9));ry=70+30*math.cos(i*1.3)
  a=(int(x+rx*math.sin(aa)),int(y+ry*math.cos(aa)+42*math.sin(i*.5)))
  b=(a[0]+int(25*math.cos(aa)),a[1]+int(17*math.sin(aa)))
  d.line((a,b),fill=color(c,.7),width=5)
 for step in range(2):
  aa=t*.25+step*2.5
  px=x+int(165*math.cos(aa));py=y+int(90*math.sin(aa))
  glowing_circle(d,px,py,9,(255,228,176))

def key(d,x,y,c,t):
 x+=int(math.sin(t*.9)*20);y+=int(math.cos(t*.7)*9)
 d.ellipse((x-160,y-75,x-32,y+53),outline=c,width=22)
 d.ellipse((x-129,y-44,x-65,y+20),outline=color(c,.45),width=5)
 d.line((x-32,y-11,x+208,y-11),fill=c,width=28)
 d.line((x+160,y-11,x+160,y+70),fill=c,width=27)
 d.line((x+205,y-11,x+205,y+54),fill=c,width=23)
 for i in range(3):
  d.arc((x-195-i*18,y-110-i*16,x+260+i*18,y+105+i*16),30,100,fill=color(c,.22),width=4)

def blocked(d,x,y,c,t):
 red=COLORS['red'];w=440;h=300
 d.rounded_rectangle((x-w//2,y-h//2,x+w//2,y+h//2),radius=21,fill=(12,25,44),outline=(69,99,118),width=4)
 d.rectangle((x-w//2,y-h//2,x+w//2,y-h//2+36),fill=(38,53,72))
 for i in range(3):d.ellipse((x-w//2+17+i*25,y-h//2+12,x-w//2+30+i*25,y-h//2+25),fill=(100+i*20,125,133))
 glitch=int(6*math.sin(t*9))
 d.rounded_rectangle((x-176+glitch,y-54,x+176+glitch,y+80),radius=12,fill=(66,21,36),outline=red,width=5)
 textline(d,(x-137+glitch,y-25),'ACCESS DENIED',fonts('en',32,True),(255,222,223))
 d.line((x-155,y+112,x+80,y+112),fill=color(c,.65),width=5)
 d.line((x-155,y+131,x+155,y+131),fill=color(c,.32),width=3)

def vault(d,x,y,c,t):
 for i in range(5):
  r=190-i*31; d.ellipse((x-r,y-r,x+r,y+r),outline=color(c,.22+i*.15),width=10)
 for i in range(8):
  a=i*math.tau/8+t*.12;xx=x+179*math.cos(a);yy=y+179*math.sin(a)
  d.ellipse((xx-13,yy-13,xx+13,yy+13),fill=(186,191,184),outline=c,width=2)
 for i in range(4):
  a=i*math.pi/2+t*.18;dx=100*math.cos(a);dy=100*math.sin(a)
  d.line((x-dx,y-dy,x+dx,y+dy),fill=c,width=8)
 glowing_circle(d,x,y,28,c)

def wallet(d,x,y,c,t):
 d.rounded_rectangle((x-225,y-155,x+235,y+130),radius=29,fill=(22,40,66),outline=c,width=6)
 d.rounded_rectangle((x+70,y-55,x+239,y+49),radius=18,fill=(12,25,47),outline=color(c,.72),width=5)
 d.ellipse((x+138,y-21,x+180,y+20),outline=c,width=7)
 for i in range(4):d.line((x-185,y-60+40*i,x+25,y-60+40*i),fill=color(c,.24+.11*i),width=5)
 for i in range(3):
  a=t+i*2.2;xx=x-280+50*math.sin(a);yy=y+140+26*math.cos(a)
  glowing_circle(d,xx,yy,5,c,False)

def stamp(d,x,y,c,t):
 d.rounded_rectangle((x-230,y-195,x+240,y+195),radius=11,fill=(218,226,219),outline=color(c,.58),width=5)
 for i in range(6):
  yy=y-145+i*39;d.line((x-178,yy,x+180,yy),fill=(120,140,144),width=4)
 d.rounded_rectangle((x-154,y-12,x+169,y+90),radius=6,outline=(171,45,55),width=9)
 textline(d,(x-137,y+1),'08.11.2023',fonts('en',39,True),(139,32,43))
 textline(d,(x-164,y-155),'ILLUSTRATION / ILUSTRAÇÃO',fonts('en',18,True),(118,56,69))

def titlepanel(d,title,lang,accent,t,step):
 # Animation slides in horizontally, then holds; no text in busy central area
 f,lines=fitwrap(d,title,lang,58,2,610)
 rise=int(35*max(0,1-t*2.4))
 yy=252+rise;dy=66 if f.size>=46 else 55
 for s in lines:
  w=width(d,s,f,lang)
  x=max(25,(W-w)//2)
  textline(d,(x+2,yy+3),s,f,(5,9,21),lang,stroke_width=4,stroke_fill=(5,9,21))
  textline(d,(x,yy),s,f,(242,247,248),lang)
  yy+=dy
 # underlined tag
 d.rounded_rectangle((W//2-125,yy+7,W//2+125,yy+12),radius=2,fill=accent)

def fit_subtitle(d,s,lang,accent,progress):
 fs=31 if lang!='he' else 30
 f=fonts(lang,fs,True)
 lines=wrap(d,s,f,lang,606)
 if len(lines)>3:
  f=fonts(lang,27,True);lines=wrap(d,s,f,lang,620)
 # Text block is in Instagram-safe area, above controls at bottom
 base=950 if len(lines)>=3 else 970
 h=49*len(lines)+30
 d.rounded_rectangle((36,base-15,W-36,base+h),radius=18,fill=(10,22,35),outline=color(accent,.36),width=2)
 for i,line in enumerate(lines):
  w=width(d,line,f,lang);x=max(45,(W-w)//2)
  textline(d,(x,base+i*49),line,f,(242,244,246),lang)
 d.rectangle((46,base+h-8,46+int((W-92)*progress),base+h-4),fill=accent)


def background(accent):
 # Precomputed composited gradients and framing, reused on all frames of one Reel.
 img=Image.new('RGB',(W,H));d=ImageDraw.Draw(img)
 for y in range(H):
  v=y/H;d.line((0,y,W,y),fill=(round(5+9*v),round(14+13*v),round(29+16*v)))
 for i in range(16):
  x=(i*67+17)%W
  d.line((x,160,x,1040),fill=(16,37,53),width=1)
 for y in range(160,1050,62):d.line((20,y,W-20,y),fill=(13,32,51),width=1)
 # dramatic cinematic vertical tech rails
 d.rectangle((0,0,12,H),fill=color(accent,.34))
 d.line((32,0,32,H),fill=color(accent,.18),width=2)
 d.rectangle((W-12,0,W,H),fill=color(accent,.22))
 d.rounded_rectangle((45,59,323,129),radius=12,fill=(21,37,55),outline=color(accent,.52),width=2)
 textline(d,(61,74),'JANAS BTC',fonts('en',35,True),(245,248,244))
 return img


def motif(d,kind,x,y,c,t,step):
 # All motifs occupy the same 2.5D world and meet at the same glowing portal.
 if kind=='bill':perspective_bill(d,x,y,1+0.03*math.sin(t*1.2),c)
 elif kind=='cart':cart(d,x,y,c,t)
 elif kind=='particles':
  perspective_bill(d,x,y,.69,c)
  rr=random.Random(44+step)
  for i in range(130):
   a=i*2.399+rr.random()*.3;r=46+(i%13)*19+t*11;xx=x+int(math.cos(a)*r);yy=y+int(math.sin(a)*r*.82)
   d.ellipse((xx,yy,xx+3+(i%4),yy+3+(i%4)),fill=color(c,.32+0.13*(i%4)))
 elif kind=='politics':
  for j,(name,off) in enumerate([('LULA',-150),('BOLSONARO',160)]):
   xx=x+off;d.rounded_rectangle((xx-133,y+65,xx+134,y+181),radius=14,fill=(32,41,63),outline=color(c,.65),width=5)
   f=fonts('en',39 if j==0 else 28,True);tw=width(d,name,f,'en')
   textline(d,(xx-tw//2,y+96),name,f,(242,247,244))
  d.line((x,y+175,x,y-190),fill=color(c,.42),width=8)
  glowing_circle(d,x,y-193,18,c)
 elif kind=='network':
  drawn_graph(d,x,y,c,t);textline(d,(x-59,y-75),'₿',fonts('en',135,True),(249,214,124))
 elif kind=='clock':
  glowing_circle(d,x,y,205,c,False)
  for i in range(12):
   a=i*math.pi/6;d.line((x+170*math.cos(a),y+170*math.sin(a),x+188*math.cos(a),y+188*math.sin(a)),fill=c,width=6)
  for angle,l,w in [(t*.4+2.6,130,11),(-t*.83+1.4,168,6)]:d.line((x,y,x+int(l*math.cos(angle)),y+int(l*math.sin(angle))),fill=(245,245,238),width=w)
  glowing_circle(d,x,y,16,c)
 elif kind=='globe':globe(d,x,y,c,t)
 elif kind=='toll':
  for j in range(3):
   xx=x-240+j*240;d.line((xx,y-215,xx,y+194),fill=color(c,.6),width=9)
   d.line((xx-64,y-55+int(15*math.sin(t+j)),xx+58,y-55),fill=(239,116,107),width=11)
  glowing_circle(d,x+int(180*math.sin(t*.55)),y+115,36,c)
 elif kind=='blocked':blocked(d,x,y,c,t)
 elif kind=='transfer':
  globe(d,x,y,c,t)
  for i in range(5):
   p=((t*.25+i*.22)%1);xx=x-245+round(490*p);yy=y+120-int(190*math.sin(math.pi*p))
   glowing_circle(d,xx,yy,7,c)
 elif kind=='split':
  for xx,s in [(x-154,'₿'),(x+154,'USDC')]:
   glowing_circle(d,xx,y,105,c,False)
   f=fonts('en',90 if s=='₿' else 43,True);ww=width(d,s,f,'en')
   textline(d,(xx-ww//2,y-49 if s=='₿' else y-27),s,f,(235,246,242))
  d.line((x-50,y,x+50,y),fill=c,width=5)
 elif kind=='nodes':drawn_graph(d,x,y,c,t,16)
 elif kind=='vault':vault(d,x,y,c,t)
 elif kind=='wallet':wallet(d,x,y,c,t)
 elif kind=='key':key(d,x,y,c,t)
 elif kind=='border':
  globe(d,x,y,c,t)
  d.line((x,y-250,x,y+250),fill=(255,79,92),width=8)
  textline(d,(x-110,y+228),'BORDER',fonts('en',38,True),(255,190,196))
 elif kind=='dossier':stamp(d,x,y,c,t)
 elif kind=='intel':
  drawn_graph(d,x,y,c,t,11)
  d.rounded_rectangle((x-179,y-60,x+179,y+72),radius=13,fill=(24,35,48),outline=c,width=4)
  textline(d,(x-137,y-23),'REUTERS',fonts('en',47,True),(236,242,248))
  textline(d,(x-66,y+38),'2023',fonts('en',22,True),c)
 else:globe(d,x,y,c,t)


def draw_scene_frame(base,lang,info,scene,idx,fi):
 k,headline,narr=scene;c=COLORS[info['accent']]
 t=fi/FPS; phase=fi/(SECS*FPS);x=W//2+int(10*math.sin(t*.7));y=ART_Y+int(9*math.sin(t*.8))
 im=base.copy();d=ImageDraw.Draw(im)
 # Parallax streak field and distant particles; each scene shares a common camera axis.
 for p in range(34):
  a=p*2.39996;depth=70+(p*61)%385
  px=360+int(math.cos(a)*depth + 24*math.sin(t*.32+p))
  py=650+int(math.sin(a)*depth*.9 + (t*12*(1+p%3))%85-45)
  radius=1+(p%3)
  d.ellipse((px-radius,py-radius,px+radius,py+radius),fill=color(c,.2+(p%5)*.13))
 # continuous rotating portal as connective tissue from scene to scene
 for j in range(3):
  radius=340+j*43+int(14*math.sin(t+j))
  d.arc((x-radius,y-radius,x+radius,y+radius),20+int(t*18)+j*95,170+int(t*18)+j*95,fill=color(c,.17+j*.11),width=3)
 motif(d,k,x,y,c,t,idx)
 # A shared energy portal dilates at the end of every 8-second clip, establishing continuity
 portal=max(0,(phase-.88)/.12)
 intro=max(0,1-phase/.11)
 if portal>0 or intro>0:
  rr=int(35+360*max(portal,intro))
  for j in range(4):
   r=rr+j*31;d.ellipse((x-r,y-r,x+r,y+r),outline=color(c,.35-j*.07),width=8)
 # Kinetic headlines, progress and upper aesthetic framing
 d.rounded_rectangle((520,77,675,121),radius=9,fill=(20,38,53),outline=color(c,.35),width=2)
 textline(d,(532,88),info['label'],fonts(lang,18 if lang=='he' else 19,True),(216,229,233),lang)
 d.line((43,158,W-43,158),fill=color(c,.25),width=2)
 titlepanel(d,headline,lang,c,t,idx)
 d.rounded_rectangle((46,1142,674,1148),radius=3,fill=(33,53,71))
 d.rounded_rectangle((46,1142,46+int(628*(idx+phase)/6),1148),radius=3,fill=c)
 textline(d,(48,1167),f'EP 01   /   {idx+1:02d}:06',fonts('en',22,True),(168,185,202))
 textline(d,(525,1167),'JANASBTC',fonts('en',20,True),c)
 parts=narr.split(' ');half=max(1,round(len(parts)*.52));phrase=' '.join(parts[:half]) if phase<.49 else ' '.join(parts[half:])
 fit_subtitle(d,phrase,lang,c,(phase%(.50))/.50)
 return im


def tts_audio(text,voice,out):
 import edge_tts
 async def go():
  for attempt in range(4):
   try:
    await edge_tts.Communicate(text,voice,rate='+10%').save(str(out));return
   except Exception:
    if attempt==3:raise
    await asyncio.sleep(2*(attempt+1))
 asyncio.run(go())


def duration(path):
 return float(call('ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',path))


def audio_for_scene(text,voice,path,quiet=False):
 raw=path.with_suffix('.mp3');wav=path.with_suffix('.wav')
 if quiet:
  call('ffmpeg','-y','-f','lavfi','-i','anullsrc=r=44100:cl=mono','-t',str(SECS),'-c:a','pcm_s16le',wav)
 else:
  tts_audio(text,voice,raw)
  src=duration(raw);speed=max(1.0,src/7.65)
  if speed>1.55:print(f'WARNING: fast narration {src:.1f}s => x{speed:.2f}',flush=True)
  call('ffmpeg','-y','-i',raw,'-af',f'atempo={speed:.5f},apad,atrim=0:{SECS},afade=t=out:st=7.85:d=0.15','-ar','44100','-ac','1',wav)
 return wav


def encode_scene(lang,info,scene,idx,work,base,quiet=False,frames_limit=None):
 audio=audio_for_scene(scene[2],info['voice'],work/f'audio_{idx+1:02d}',quiet)
 dest=work/f'clip_{idx+1:02d}.mp4';count=frames_limit or (SECS*FPS)
 cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(audio),'-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-t',str(count/FPS),'-movflags','+faststart',str(dest)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 try:
  for fi in range(count):
   img=draw_scene_frame(base,lang,info,scene,idx,fi)
   p.stdin.write(img.tobytes())
  p.stdin.close();errors=p.stderr.read().decode(errors='replace')
  code=p.wait()
  if code:raise RuntimeError('Error ffmpeg: '+errors[-1500:])
 except Exception:
  try:p.kill()
  except Exception:pass
  raise
 return dest


def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--only',choices=['pt','es','en','ru','he'])
 ap.add_argument('--fake-tts',action='store_true',help='Preview/diagnostics only: silent videos; never publish.')
 ap.add_argument('--test-frames',type=int,default=0,help='Technical test: encode N frames of each scene')
 ap.add_argument('--scenes',type=int,choices=[1,2,3,4,5,6],default=6)
 ap.add_argument('--validate',action='store_true')
 args=ap.parse_args()
 data=json.loads((HERE/'episodios_01.json').read_text(encoding='utf-8'))
 assert set(data)=={'pt','es','en','ru','he'}
 for lang,v in data.items():
  assert len(v['scenes'])==6 and all(len(x)==3 and all(x) for x in v['scenes'])
 if args.validate:
  print('VALIDATED: 5 unique regional videos, 30 narrated visual scenes.');return
 OUT.mkdir(exist_ok=True)
 for lang in ([args.only] if args.only else ['pt','es','en','ru','he']):
  v=data[lang];work=OUT/lang;work.mkdir(exist_ok=True)
  print('RENDER',lang,v['title'],flush=True)
  base=background(COLORS[v['accent']]);clips=[]
  for i,scene in enumerate(v['scenes'][:args.scenes]):
   clips.append(encode_scene(lang,v,scene,i,work,base,quiet=args.fake_tts,frames_limit=args.test_frames or None))
   print('CLIP',lang,i+1,'OK',flush=True)
  if args.scenes==6 and not args.test_frames:
   listfile=work/'segments.txt';listfile.write_text(''.join(f"file '{p.name}'\n" for p in clips))
   output=OUT/f'JANAS_BTC_REEL_01_{lang.upper()}.mp4'
   call('ffmpeg','-y','-f','concat','-safe','0','-i',listfile,'-c','copy','-movflags','+faststart',output)
   print('COMPLETE',output,'duration',duration(output),flush=True)
 (OUT/'ROTEIROS_E_LEGENDAS.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 (OUT/'LEIA_PRIMEIRO.txt').write_text('JANAS BTC | CINEMATIC REELS\n5 temas, 5 vídeos completos, 6 cenas de até 8s.\nEstilo: motion graphics procedural com efeito 2.5D, NÃO vídeo gerativo por IA.\nAs imagens da investigação de 2023 são ilustrações, não documentos autênticos.\nConsulte fontes oficiais antes de publicar denúncias ou acusações.\n',encoding='utf-8')

if __name__=='__main__':main()