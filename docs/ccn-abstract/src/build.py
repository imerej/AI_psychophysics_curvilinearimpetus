import re,sys,shutil,os,subprocess
from xml.sax.saxutils import escape
sys.path.insert(0,os.path.dirname(__file__)); import content as C
T=sys.argv[1]; OUT=sys.argv[2]; FIG=sys.argv[3]; W=os.path.join(os.path.dirname(os.path.abspath(__file__)),'_build')
shutil.rmtree(W,ignore_errors=True); subprocess.run(['unzip','-q',T,'-d',W],check=True)
subprocess.run(['find',W,'-type','l','-delete'])
x=open(W+'/word/document.xml',encoding='utf8').read()
ps=re.findall(r'<w:p[ >].*?</w:p>|<w:tbl>.*?</w:tbl>',x,re.S)
body_start=x.index('<w:body>')+len('<w:body>'); final_sect=re.search(r'<w:sectPr(?:(?!<w:sectPr).)*</w:sectPr>\s*</w:body>',x,re.S).group(0)
def runs(text,base=''):
    out=[]
    for tok in re.split(r'(\[\[.*?\]\]|\*[^*]+\*)',text):
        if not tok: continue
        rp=base
        if tok.startswith('[['): tok=tok[2:-2]; rp+='<w:highlight w:val="yellow"/>'; tok='['+tok+']'
        elif tok.startswith('*') and tok.endswith('*') and len(tok)>2: tok=tok[1:-1]; rp+='<w:i/><w:iCs/>'
        out.append(f'<w:r>{"<w:rPr>"+rp+"</w:rPr>" if rp else ""}<w:t xml:space="preserve">{escape(tok)}</w:t></w:r>')
    return ''.join(out)
def para(ppr,text,base=''): return f'<w:p><w:pPr>{ppr}</w:pPr>{runs(text,base)}</w:p>'
# front matter
title=para('<w:pStyle w:val="Title"/>',C.TITLE,'<w:szCs w:val="28"/>')
hv='<w:rFonts w:ascii="Helvetica" w:hAnsi="Helvetica"/>'
auth=para('<w:pStyle w:val="Authorname"/>',C.AUTHORS,hv)+para('<w:pStyle w:val="Affiliation"/>',C.AFFIL,hv)+\
  para('<w:pStyle w:val="Affiliation"/>',C.EMAIL,'<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/><w:sz w:val="18"/><w:szCs w:val="18"/>')
abs_p=re.sub(r'(<w:pPr>.*?</w:pPr>).*',r'\1',ps[5],flags=re.S)
abs_p=abs_p+runs(C.ABSTRACT,'<w:b w:val="0"/><w:bCs w:val="0"/>')+'</w:p>'
out=[title,auth,ps[2],ps[3],ps[4],abs_p]
prev=None; fig_rid='rIdFig1'
for kind,text in C.BODY:
    if kind=='H1': out.append(para('<w:pStyle w:val="Heading1"/>',text))
    elif kind=='H2': out.append(para('<w:pStyle w:val="Heading2"/>',text))
    elif kind=='P':
        if prev=='H1': out.append(para('<w:ind w:firstLine="0"/>',text))
        elif prev=='H2': out.append(para('<w:pStyle w:val="NormalSectionStart"/>',text))
        else: out.append(para('',text))
    elif kind=='REF': out.append(para('<w:ind w:left="187" w:hanging="187"/>',text))
    elif kind=='CAP': out.append(para('<w:pStyle w:val="Figure"/><w:spacing w:before="60" w:after="200"/><w:jc w:val="both"/>',text))
    elif kind=='FIG':
        cx,cy=int(3.35*914400),int(3.45*914400)
        out.append(f'<w:p><w:pPr><w:keepNext/><w:spacing w:before="200" w:line="240" w:lineRule="auto"/><w:ind w:firstLine="0"/><w:jc w:val="center"/></w:pPr><w:r><w:rPr><w:noProof/></w:rPr><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:docPr id="501" name="Figure 1" descr="Tracked LTX-Video paths for one tube, and bar chart of curving responses by tube shape for LTX-Video, V-JEPA 2 and published human data."/><wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr><a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="501" name="figure1.png"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{fig_rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')
    prev=kind
x=x[:body_start]+''.join(out)+final_sect+'</w:document>'
open(W+'/word/document.xml','w',encoding='utf8').write(x)
shutil.copy(FIG,W+'/word/media/figure1.png')
r=open(W+'/word/_rels/document.xml.rels').read()
r=r.replace('</Relationships>',f'<Relationship Id="{fig_rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/figure1.png"/></Relationships>')
open(W+'/word/_rels/document.xml.rels','w').write(r)
ct=W+'/[Content_Types].xml'; c=open(ct).read().replace('wordprocessingml.template.main+xml','wordprocessingml.document.main+xml'); open(ct,'w').write(c)
# drop unused template images? keep media referenced elsewhere (footer). 
if os.path.exists(OUT): os.remove(OUT)
subprocess.run(f'cd {W} && zip -qXr {OUT} .',shell=True,check=True)
print('written',OUT)
