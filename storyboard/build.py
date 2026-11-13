"""Build a native editable storyboard, render it and verify the PDF before export."""
import ast,base64,hashlib,json,math,subprocess,textwrap
from pathlib import Path
import fitz
from PIL import Image,ImageDraw,ImageFont
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE,MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN,MSO_ANCHOR
from pptx.oxml.xmlchemy import OxmlElement
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/"storyboard";OUT=HERE/"output";OUT.mkdir(exist_ok=True)
CAP=HERE/"captures";PAGES=json.loads((HERE/"pages.json").read_text())
MANIFEST=json.loads((CAP/"manifest.json").read_text())
SOURCE="8010c2574e95207630fd620b1eb8692235d57278"
REPO="https://github.com/sritharan-blip/ShopImpactAI"
NAVY="101D35";INK="182942";MUTED="50627D";BLUE="3153D5";CYAN="80E7FF";VIOLET="B8A4F5";BG="F3F6FB";LINE="DCE4F0";WHITE="FFFFFF";SOFT="E8EEFA"
prs=Presentation();prs.slide_width=Inches(16);prs.slide_height=Inches(9)
prs.core_properties.title="ShopImpactAI | Application storyboard"
prs.core_properties.subject="User journeys, real interface evidence and backend explanation"
prs.core_properties.author="SRITHARAN N S"
prs.core_properties.keywords="ShopImpactAI, storyboard, Streamlit, TF-IDF, backend, prototype"
bounds=[]
def rgb(s):return RGBColor.from_string(s)
def box(s,x,y,w,h,fill=WHITE,line=None,r=.12):
    sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if r else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid();sh.fill.fore_color.rgb=rgb(fill)
    if line:sh.line.color.rgb=rgb(line);sh.line.width=Pt(.8)
    else:sh.line.fill.background()
    if r:
        try:sh.adjustments[0]=r
        except Exception:pass
    return sh
FONT="/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
BOLD="/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
if not Path(FONT).exists():
    FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf";BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def lines_needed(text,width,size,bold=False):
    f=ImageFont.truetype(BOLD if bold else FONT,round(size*2))
    total=0
    for paragraph in text.split("\n"):
        count=1;line=""
        for word in paragraph.split():
            candidate=(line+" "+word).strip()
            if f.getlength(candidate)>width*144 and line:count+=1;line=word
            else:line=candidate
        total+=count
    return total
def tx(s,text,x,y,w,h,size=18,color=INK,bold=False,align=None,link=None,floor=None):
    size=float(size);floor=floor or size
    while size>floor and lines_needed(text,w,size,bold)*size*1.1>h*72-2:size-=.5
    if lines_needed(text,w,size,bold)*size*1.1>h*72+7:print("TEXT_FIT_REVIEW",len(prs.slides),text[:70],flush=True)
    sh=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=sh.text_frame
    tf.clear();tf.word_wrap=True;tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    tf.vertical_anchor=MSO_ANCHOR.TOP
    for i,line in enumerate(text.split("\n")):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.space_before=Pt(0);p.space_after=Pt(0);p.line_spacing=1.1
        if align is not None:p.alignment=align
        run=p.add_run();run.text=line;run.font.name="Arial";run.font.size=Pt(size);run.font.bold=bold;run.font.color.rgb=rgb(color)
        if link:run.hyperlink.address=link
    bounds.append((len(prs.slides),text[:55],x,y,w,h))
    return sh
def line(s,x1,y1,x2,y2,color=BLUE,width=1.5,arrow=False,bi=False):
    sh=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1),Inches(y1),Inches(x2),Inches(y2))
    sh.line.color.rgb=rgb(color);sh.line.width=Pt(width)
    if arrow:
        end=OxmlElement("a:tailEnd");end.set("type","triangle");sh._element.xpath(".//a:ln")[0].append(end)
    if bi:
        end=OxmlElement("a:headEnd");end.set("type","triangle");sh._element.xpath(".//a:ln")[0].append(end)
    return sh
def src_url(page):
    path=page.get("source","README.md");url=REPO+"/blob/"+SOURCE+"/"+path
    if page.get("function"):
        try:
            node=next(n for n in ast.walk(ast.parse((ROOT/path).read_text())) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==page["function"])
            url+="#L"+str(node.lineno)
        except Exception:pass
    return url
def footer(s,page,n,dark=False):
    line(s,.6,8.46,15.4,8.46,"344665" if dark else LINE,.6)
    c="BAC8DF" if dark else MUTED
    label=page.get("source","README.md")
    if page.get("function"):label+=" / "+page["function"]+"()"
    tx(s,"SOURCE  "+label,.65,8.58,12.9,.2,10.5,c,link=src_url(page))
    tx(s,f"{n:02d} / {len(PAGES):02d}",14.4,8.56,1,.23,12,c,align=PP_ALIGN.RIGHT)
def new(page,n,dark=False):
    s=prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid();s.background.fill.fore_color.rgb=rgb(NAVY if dark else BG)
    tx(s,"SHOPIMPACTAI  /  APPLICATION STORYBOARD",.65,.28,10,.25,10.5,"A9BBD9" if dark else MUTED,True)
    label=page.get("route","SYSTEM & EXPLANATION")
    if page.get("scene"):label+="  /  SCENE "+page["scene"]
    tx(s,label,9.0,.28,6.4,.25,10.5,CYAN if dark else BLUE,True,align=PP_ALIGN.RIGHT)
    tx(s,page["title"],.65,.82,14.75,.6,30,WHITE if dark else INK,True)
    sub=page.get("subtitle")
    if sub:tx(s,sub,.68,1.48,14.5,.42,16,"BFCCE1" if dark else MUTED)
    footer(s,page,n,dark)
    notes=s.notes_slide.notes_text_frame
    if notes:notes.text="Source reviewed: "+src_url(page)+"\n"+json.dumps(page,ensure_ascii=False,indent=2)
    return s
def image_fit(s,name,x,y,w,h,frame=True,marks=False):
    info=MANIFEST[name];path=CAP/info["file"];im=Image.open(path);iw,ih=im.size
    if frame:
        box(s,x,y,w,h,WHITE,LINE,.06)
        line(s,x+.12,y+.25,x+w-.12,y+.25,LINE,.6)
        tx(s,"REAL UI  /  SYNTHETIC DEMONSTRATION DATA",x+.2,y+.07,w-.4,.15,8.5,MUTED,True)
        y+=.34;h-=.44;x+=.12;w-=.24
    scale=min(w/iw,h/ih);pw,ph=iw*scale,ih*scale;px,py=x+(w-pw)/2,y+(h-ph)/2
    pic=s.shapes.add_picture(str(path),Inches(px),Inches(py),width=Inches(pw),height=Inches(ph))
    try:pic._element.xpath(".//p:cNvPr")[0].set("descr","Actual ShopImpactAI "+name.replace("_"," ")+" interface; synthetic demonstration data.")
    except Exception:pass
    if marks:
        for m in info["marks"][:2]:
            ax,ay=px+m["x"]*pw,py+m["y"]*ph
            mx=max(px+.16,min(px+pw-.16,ax-.28));my=max(py+.16,min(py+ph-.16,ay-.2))
            line(s,mx,my,ax,ay,BLUE,1.4)
            sh=s.shapes.add_shape(MSO_SHAPE.OVAL,Inches(mx-.135),Inches(my-.135),Inches(.27),Inches(.27))
            sh.fill.solid();sh.fill.fore_color.rgb=rgb(CYAN);sh.line.color.rgb=rgb(BLUE);sh.line.width=Pt(.7)
            tx(s,str(m["n"]),mx-.1,my-.10,.2,.2,10,INK,True,align=PP_ALIGN.CENTER)
    return info
def card(s,label,body,x,y,w,h,dark=False,number=None):
    fill="1B2C49" if dark else WHITE;edge="3C5375" if dark else LINE
    box(s,x,y,w,h,fill,edge,.08)
    if number:
        tx(s,number,x+.2,y+.18,.6,.4,24,CYAN if dark else BLUE,True)
        xx=x+.95;ww=w-1.15
    else:xx=x+.24;ww=w-.48
    tx(s,label,xx,y+.18,ww,.27,11.5,CYAN if dark else BLUE,True)
    tx(s,body,xx,y+.55,ww,h-.68,18,WHITE if dark else INK,floor=16)
def table(s,rows,x,y,width,colwidths,header=None,rowh=1.0,dark=False):
    yy=y
    if header:
        box(s,x,yy,width,.45,"243B5E" if dark else "E1E9F8",None,0)
        xx=x
        for word,cw in zip(header,colwidths):
            tx(s,word,xx+.15,yy+.11,cw-.3,.24,12,CYAN if dark else BLUE,True)
            xx+=cw
        yy+=.45
    for i,row in enumerate(rows):
        box(s,x,yy,width,rowh,("182943" if i%2==0 else "20324D") if dark else (WHITE if i%2==0 else "EAF0FA"),None,0)
        xx=x
        for j,(word,cw) in enumerate(zip(row,colwidths)):
            tx(s,word,xx+.15,yy+.16,cw-.3,rowh-.25,17,WHITE if dark else INK,bold=j==0,floor=15.5)
            xx+=cw
        yy+=rowh
    return yy
# A restrained original gradient backdrop, used only for the cover.
cover_bg=OUT/"cover-background.png"
im=Image.new("RGB",(1920,1080));d=ImageDraw.Draw(im)
for yy in range(1080):
    t=yy/1080;d.line((0,yy,1920,yy),fill=(10+int(5*t),20+int(5*t),40+int(15*t)))
im.save(cover_bg)
for n,page in enumerate(PAGES,1):
    typ=page["type"];dark=typ in ("cover","engine","math","checkout")
    s=new(page,n,dark) if typ!="cover" else prs.slides.add_slide(prs.slide_layouts[6])
    if typ=="cover":
        s.shapes.add_picture(str(cover_bg),0,0,width=prs.slide_width,height=prs.slide_height)
        tx(s,"PRODUCT  /  EXPERIENCE  /  SYSTEM",.8,.58,9,.3,12,CYAN,True)
        tx(s,"ShopImpactAI",.8,1.25,14.4,1,54,WHITE,True)
        tx(s,"Application\nstoryboard",.85,2.6,6.8,1.65,43,WHITE,True)
        tx(s,page["strap"],.9,4.62,5.7,1.2,21,"C3D0E6")
        box(s,.9,6.24,4.85,.55,"203451","4A648C",.12)
        tx(s,"USER JOURNEY + BACKEND EXPLANATION",1.12,6.42,4.45,.2,11,CYAN,True)
        image_fit(s,page["image"],7.55,2.7,7.6,4.85,False)
        tx(s,page["author"],.9,7.28,7,.35,20,WHITE,True)
        tx(s,"13 NOVEMBER 2026  /  EXAMINER EDITION",.92,7.82,8,.25,12,"B8C7E1")
        footer(s,{"source":"README.md"},n,True)
        continue
    if typ=="scene":
        tx(s,"USER GOAL  "+page["goal"],.7,1.46,14.6,.49,15.5,MUTED)
        info=image_fit(s,page["image"],.65,2.12,9.9,5.65,True,True)
        sections=[("USER ACTION","action"),("SYSTEM RESPONSE","response"),("BEHIND THE SCREEN","backend")]
        font_size=18.0
        while True:
            heights=[.68+lines_needed(page[k],4.02,font_size)*font_size*1.1/72 for _,k in sections]
            if sum(heights)+.20<=5.65 or font_size<=15.5:break
            font_size-=.5
        yy=2.12
        for (label,key),hh in zip(sections,heights):
            box(s,10.85,yy,4.5,hh,WHITE,LINE,.08)
            tx(s,label,11.09,yy+.18,4.02,.25,11.5,BLUE,True)
            tx(s,page[key],11.09,yy+.55,4.02,hh-.63,font_size,INK)
            yy+=hh+.10
        marks=info["marks"][:2]
        legend="   /   ".join(str(m["n"])+" "+m["label"] for m in marks) or "Task capture: "+page["image"].replace("_"," ")
        tx(s,legend,.75,7.94,14.5,.25,11.5,MUTED)
    elif typ=="context":
        for i,(label,body) in enumerate(page["cards"]):
            card(s,label,body,.7+(i%2)*7.5,2.25+(i//2)*2.45,7.1,2.16,number=f"{i+1:02d}")
        tx(s,"The app turns reflection into visible tasks, while making its assumptions explicit.",.85,7.55,14,.45,20,BLUE,True)
    elif typ=="journey":
        for i,text in enumerate(page["main"]):
            card(s,text.split(" / ")[0],text.split(" / ")[1],.65+i*3.0,2.2,2.72,1.55,number=None)
            if i<4:line(s,3.4+i*3,2.98,3.62+i*3,2.98,BLUE,1.2,True)
        card(s,page["branch"][0],page["branch"][1],.75,4.35,7.1,2.03)
        card(s,page["branch"][2],page["branch"][3],8.15,4.35,7.1,2.03)
        tx(s,page["note"],.85,7.1,14.3,.8,17,MUTED)
    elif typ=="architecture":
        positions=[(.8,2.35,3.45,1.5),(5.2,2.35,5.2,1.5),(11.4,2.35,3.8,1.5),(2.5,5.05,5.0,1.5),(8.5,5.05,5.6,1.5)]
        for (label,body),pos in zip(page["nodes"],positions):card(s,label,body,*pos)
        line(s,4.3,3.1,5.15,3.1,BLUE,1.5,True,True)
        line(s,10.45,3.1,11.35,3.1,BLUE,1.5,True,True)
        line(s,6.6,3.9,5.0,5.0,BLUE,1.5,True,True)
        line(s,9.0,3.9,11.0,5.0,BLUE,1.5,True,True)
        tx(s,"Input events and rendered UI updates",.9,4.18,13.9,.3,14,MUTED,align=PP_ALIGN.CENTER)
        tx(s,page["note"],.85,7.16,14.3,.82,16.5,MUTED)
    elif typ=="engine":
        for i,(label,body) in enumerate(page["steps"]):
            card(s,label,body,.65+(i%3)*5.0,2.12+(i//3)*2.13,4.72,1.91,True)
        box(s,.75,6.65,14.5,.65,"2D4264","5879A9",.06)
        tx(s,page["formula"],.95,6.87,14.1,.28,19,CYAN,True,align=PP_ALIGN.CENTER)
        tx(s,"TF-IDF detail: idf(t) = ln((1 + N)/(1 + df(t))) + 1; tf = 1 + ln(count); vectors use L2 normalisation.",.85,7.48,14.3,.3,13.5,"C7D3E8")
        tx(s,page["note"],.85,7.86,14.2,.4,12.5,"C7D3E8")
    elif typ=="math":
        for i,(label,equation,result) in enumerate(page["equations"]):
            y=2.2+i*1.46;box(s,.75,y,9.4,1.23,"1C304D","3E5B80",.08)
            tx(s,label,1,y+.15,8.9,.25,11.5,CYAN,True)
            tx(s,equation,1,y+.57,6.2,.33,18,WHITE)
            tx(s,result,7.05,y+.52,2.85,.55,22,CYAN,True,align=PP_ALIGN.RIGHT)
        table(s,page["record"],10.55,2.2,4.65,[2.65,2.0],["FIELD","VALUE"],.62,True)
        tx(s,page["note"],.85,6.95,14.2,1.05,17,"C7D3E8")
    elif typ=="checkout":
        for i,(label,body) in enumerate(page["steps"]):
            yy=2.05+i*1.13
            box(s,.75,yy,8.05,1.04,"1B2C49","3C5375",.08)
            tx(s,label,1.0,yy+.12,7.55,.27,16,CYAN,True)
            tx(s,body,1.0,yy+.46,7.55,.50,16,WHITE)
        table(s,page["facts"],9.3,2.2,5.95,[2.15,3.8],["TRACE","RECORDED RESULT"],1.05,True)
        tx(s,page["note"],9.45,6.95,5.6,1.25,14.5,"C7D3E8")
    elif typ=="backup":
        image_fit(s,page["image"],.75,2.1,4.05,5.7,True)
        for i,(label,body) in enumerate(page["stages"]):
            card(s,label,body,5.05+(i%2)*5.2,2.2+(i//2)*2.28,4.9,2.02)
        tx(s,page["note"],5.15,6.95,9.9,1.02,16.5,MUTED)
    elif typ=="state":
        for i,(label,body) in enumerate(page["entities"]):
            card(s,label,body,.75+(i%2)*7.5,2.18+(i//2)*2.12,7.1,1.87)
        tx(s,page["note"],.85,6.98,14.2,1.05,18,MUTED)
    elif typ=="accessibility":
        image_fit(s,"overview_dark",.65,2.03,7.25,4.35,True)
        image_fit(s,"mobile",8.2,2.03,2.65,4.35,True)
        tx(s,"Same product, adapted layout",.85,6.59,10,.35,17,BLUE,True)
        yy=2.1;font_size=16.0
        for label,body in page["points"]:
            hh=lines_needed(body,4.1,font_size)*font_size*1.1/72
            tx(s,label,11.15,yy,4.1,.25,11,BLUE,True)
            tx(s,body,11.15,yy+.33,4.1,hh+.05,font_size,INK)
            yy+=hh+.50
        tx(s,"Decorative layers move. Readable text and control backgrounds stay coordinated.",.85,7.2,9.95,.82,18,MUTED)
    elif typ=="testing":
        table(s,page["rows"],.7,2.1,14.6,[2.7,2.7,9.2],["CHECK","SCOPE","WHAT IT SUPPORTS"],.91)
        tx(s,page["note"],.85,7.32,14.2,.72,16,MUTED)
        tx(s,"Original source CI evidence",.85,8.08,8,.2,11,BLUE,link=REPO+"/actions/runs/43191405112")
    elif typ=="limits":
        table(s,page["rows"],.7,2.2,14.6,[6.1,8.5],["IMPLEMENTED PROTOTYPE","FUTURE PRODUCTION WORK"],1.0)
        tx(s,"The design demonstrates a coherent user experience; production guarantees require additional infrastructure and validation.",.85,7.84,14.1,.35,16,MUTED)
    elif typ=="closing":
        for i,(num,label,body) in enumerate(page["tasks"]):
            card(s,label,body,.75+(i%2)*7.5,2.1+(i//2)*1.68,7.1,1.45,number=num)
        tx(s,"Reviewed source: main at "+SOURCE[:12]+"  |  Captures: 13 November 2026  |  All profiles and transactions are synthetic.",.85,7.64,14.2,.5,13,MUTED)
        tx(s,"Open repository and source",.85,8.13,8,.2,11,BLUE,link=REPO+"/tree/"+SOURCE)
    else:raise RuntimeError("Unknown page type "+typ)
# Ensure the visual objects themselves are on the slide; text-fit warnings are reviewed in rendered output.
assert len(prs.slides)==28
for n,lab,x,y,w,h in bounds:
    assert min(x,y)>=0 and x+w<=16.01 and y+h<=9.01,(n,lab,x,y,w,h)
ppt=OUT/"ShopImpactAI_Storyboard_SRITHARAN_NS.pptx";prs.save(ppt)
profile=(OUT/"lo-profile").resolve().as_uri()
subprocess.run(["libreoffice","--headless","-env:UserInstallation="+profile,"--convert-to","pdf","--outdir",str(OUT),str(ppt)],check=True,timeout=120)
pdf=OUT/"ShopImpactAI_Storyboard_SRITHARAN_NS.pdf";assert pdf.exists()
doc=fitz.open(pdf);assert len(doc)==len(PAGES)
doc.set_toc([[1,p["title"],i+1] for i,p in enumerate(PAGES)])
doc.set_metadata({"title":"ShopImpactAI | Application storyboard","author":"SRITHARAN N S","subject":"Real UI evidence, user journey and backend explanation","keywords":"ShopImpactAI, storyboard, Streamlit, TF-IDF, prototype"})
saved=OUT/"verified.pdf";doc.save(saved,garbage=4,deflate=True);doc.close();saved.replace(pdf)
doc=fitz.open(pdf);issues=[]
for i,page in enumerate(doc):
    for block in page.get_text("dict")["blocks"]:
        for ln in block.get("lines",[]):
            for sp in ln["spans"]:
                x0,y0,x1,y1=sp["bbox"]
                if x0<-.5 or y0<-.5 or x1>page.rect.width+.5 or y1>page.rect.height+.5:issues.append([i+1,sp["text"],sp["bbox"]])
assert not issues,issues
alltext="\n".join(p.get_text() for p in doc)
for token in ["ShopImpactAI","0.38","TF-IDF","128.31","session","500"]:assert token in alltext,token
thumbs=[]
for i,page in enumerate(doc):
    pix=page.get_pixmap(matrix=fitz.Matrix(.36,.36),alpha=False)
    im=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
    canvas=Image.new("RGB",(im.width,im.height+26),"#E4EAF4");canvas.paste(im,(0,0))
    dd=ImageDraw.Draw(canvas);dd.text((10,im.height+5),f"{i+1:02d}  {PAGES[i]['title'][:50]}",fill="#17223B")
    thumbs.append(canvas)
cols=4;rows=math.ceil(len(thumbs)/cols);tw,th=thumbs[0].size
montage=Image.new("RGB",(cols*(tw+12)+12,rows*(th+12)+12),"#CBD5E6")
for i,im in enumerate(thumbs):montage.paste(im,(12+(i%cols)*(tw+12),12+(i//cols)*(th+12)))
buffer=__import__("io").BytesIO();montage.save(buffer,format="JPEG",quality=82)
print("MONTAGE:"+base64.b64encode(buffer.getvalue()).decode(),flush=True)
for pagenum in (4,8,11,23,25):
    page=doc[pagenum-1];pix=page.get_pixmap(matrix=fitz.Matrix(1.1,1.1),alpha=False);im=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
    buffer=__import__("io").BytesIO();im.save(buffer,format="JPEG",quality=86)
    print("PAGE_PREVIEW:"+str(pagenum)+":"+base64.b64encode(buffer.getvalue()).decode(),flush=True)
doc.close()
print("VERIFICATION:"+json.dumps({"pages":28,"text_spans_outside_pages":issues,"source":SOURCE,"captures":list(MANIFEST),"pdf_bytes":pdf.stat().st_size,"pptx_bytes":ppt.stat().st_size}),flush=True)
for kind,path in [("PDF",pdf),("PPTX",ppt)]:
    data=path.read_bytes();encoded=base64.b64encode(data).decode()
    print("FILE_META:"+json.dumps({"kind":kind,"name":path.name,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}),flush=True)
    for i in range(0,len(encoded),24000):print("FILE_CHUNK:"+kind+":"+str(i//24000).zfill(4)+":"+encoded[i:i+24000],flush=True)
