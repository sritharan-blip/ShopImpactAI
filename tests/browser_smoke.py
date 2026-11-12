"""Real Chrome checks, including contrast sampled throughout appearance changes."""
import base64
import io
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shopimpact.theme import PALETTES
OUTPUT = ROOT / 'test-results'
OUTPUT.mkdir(exist_ok=True)

# Composite CSS backgrounds through the ancestor chain, then audit the actual
# foregrounds, rather than assuming that a primary button implies readable text.
AUDIT = r'''() => {
  const rgba = s => {let a=(s.match(/[\d.]+/g)||[]).map(Number);return a.length>=3?[a[0],a[1],a[2],a.length>3?a[3]:1]:[0,0,0,0]};
  const over=(a,b)=>a.slice(0,3).map((v,i)=>v*a[3]+b[i]*(1-a[3]));
  const lum=a=>a.map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((n,v,i)=>n+v*[.2126,.7152,.0722][i],0);
  window.auditContrast=()=>{
    const base=rgba(getComputedStyle(document.querySelector('.stApp')).backgroundColor),bad=[];
    for(const e of document.querySelectorAll('h1,h2,h3,p,small,.si-impact,[role="combobox"],[role="spinbutton"],[data-testid="stMetricValue"],[style*="color:"]')){
      const r=e.getBoundingClientRect();if(!r.width||!r.height||r.bottom<0||r.top>innerHeight||getComputedStyle(e).visibility==='hidden')continue;
      if(e.closest('button:disabled,[aria-disabled="true"]'))continue;
      let fg=rgba(getComputedStyle(e).color);if(fg[3]===0)continue;
      const layers=[];let opacity=1;for(let p=e;p;p=p.parentElement){const s=getComputedStyle(p);layers.push(rgba(s.backgroundColor));opacity*=+s.opacity;}
      if(opacity===0)continue;fg[3]*=opacity;
      let bg=base.slice(0,3);for(const layer of layers.reverse())bg=over(layer,bg);
      fg=over(fg,bg);const a=lum(fg),b=lum(bg),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
      const large=(parseFloat(getComputedStyle(e).fontSize)>=24),minimum=large?3:4.5;
      if(ratio<minimum-.02)bad.push({text:(e.textContent||e.value||e.getAttribute('aria-label')||'').trim().slice(0,65),ratio:+ratio.toFixed(2),foreground:fg,background:bg});
    }return bad;
  };
  window.startContrastWatch=()=>{window.contrastFailures=[];window.contrastRunning=true;const until=performance.now()+1500;
    function frame(){const bad=window.auditContrast();if(bad.length&&window.contrastFailures.length<15)window.contrastFailures.push(...bad.slice(0,3));
      if(performance.now()<until)requestAnimationFrame(frame);else window.contrastRunning=false;}requestAnimationFrame(frame);};
}'''


def capture(page, name):
    page.evaluate("""window.scrollTo(0,0);document.querySelector('[data-testid="stMain"]')?.scrollTo(0,0);
      const sidebar=document.querySelector('[data-testid="stSidebar"]');
      if(sidebar)for(const e of [sidebar,...sidebar.querySelectorAll('div')])
        if(/auto|scroll/.test(getComputedStyle(e).overflowY))e.scrollTo(0,0);""")
    data = page.screenshot(path=str(OUTPUT / (name + '.png')), animations='disabled')
    image = Image.open(io.BytesIO(data)).convert('RGB')
    image.thumbnail((1240, 1000))
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=82)
    print('PREVIEW:' + name + ':' + base64.b64encode(buffer.getvalue()).decode(), flush=True)


def healthy(page):
    assert page.locator('[data-testid="stException"]').count() == 0, page.locator('body').inner_text()


def switch(page, mode):
    page.evaluate('window.startContrastWatch()')
    page.get_by_text(mode, exact=True).click()
    page.wait_for_function('(expected)=>getComputedStyle(document.documentElement).getPropertyValue("--si-page").trim()===expected',
                           arg=PALETTES[mode == 'Midnight']['page'])
    page.wait_for_function('window.contrastRunning===false')
    failures = page.evaluate('window.contrastFailures')
    assert not failures, json.dumps({'mode': mode, 'failures': failures})
    healthy(page)


server = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', 'ShopImpactAI.py',
    '--server.address', '127.0.0.1', '--server.port', '8519', '--server.headless', 'true',
    '--server.fileWatcherType', 'none'], cwd=ROOT, stdout=subprocess.DEVNULL)
try:
    for attempt in range(100):
        try:
            with urlopen('http://127.0.0.1:8519/_stcore/health', timeout=1) as response:
                if response.status == 200:
                    break
        except OSError:
            time.sleep(.2)
    else:
        raise RuntimeError('Test server did not start')
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1600, 'height': 1100}, device_scale_factor=1)
        page.goto('http://127.0.0.1:8519')
        page.locator('.si-hero').wait_for()
        page.get_by_role('button', name='Load demo data', exact=True).click()
        page.locator('.si-hero small').filter(has_text='9 purchases').wait_for()
        page.evaluate(AUDIT)
        assert page.locator('.si-float-card').count() == 3
        assert page.locator('.si-hero').evaluate('(e)=>getComputedStyle(e).backdropFilter') != 'none'
        for mode in ['Midnight', 'Daylight']:
            switch(page, mode)
        capture(page, 'daylight-overview')
        switch(page, 'Midnight')
        capture(page, 'midnight-overview')
        page.get_by_text('Discover products', exact=True).click()
        page.get_by_text('Your smart matches', exact=True).wait_for()
        healthy(page)
        assert not page.evaluate('window.auditContrast()'), page.evaluate('window.auditContrast()')
        capture(page, 'midnight-discover')
        sidebar = page.locator('[data-testid="stSidebar"]')
        sidebar.get_by_text('Log a purchase', exact=True).click()
        page.get_by_role('textbox', name='Product', exact=True).wait_for()
        for mode in ['Daylight', 'Midnight']:
            switch(page, mode)
        capture(page, 'midnight-form')
        combo = page.get_by_role('combobox', name='Category', exact=True)
        combo.click()
        page.get_by_role('option', name='Electronics', exact=True).wait_for()
        assert not page.evaluate('window.auditContrast()'), page.evaluate('window.auditContrast()')
        capture(page, 'midnight-dropdown')
        page.keyboard.press('Escape')
        sidebar.get_by_text('Decision lab', exact=True).click()
        page.get_by_text('A little pause. A better decision.', exact=True).wait_for()
        page.get_by_role('textbox', name='What caught your eye?', exact=True).fill('A useful jacket')
        page.get_by_role('combobox', name='Purchase category', exact=True).click()
        page.get_by_role('option', name='Sustainable apparel / second-hand', exact=True).click()
        page.get_by_role('button', name='Save a pause plan', exact=True).click()
        page.get_by_text('Saved. Revisit on', exact=False).wait_for()
        healthy(page)
        assert not page.evaluate('window.auditContrast()'), page.evaluate('window.auditContrast()')
        caption = page.get_by_text('Explore cost per use, check your budget, and give a purchase time before you decide.', exact=True)
        print('CAPTION:' + json.dumps(caption.evaluate('e=>{const a=[];for(let p=e;p&&a.length<5;p=p.parentElement){const s=getComputedStyle(p);a.push({tag:p.tagName,testid:p.dataset.testid,color:s.color,opacity:s.opacity});}return a;}')), flush=True)
        capture(page, 'decision-lab')
        sidebar.get_by_text('Overview', exact=True).click()
        page.locator('.si-hero').wait_for()
        collapse = page.locator('[data-testid="stSidebarCollapseButton"] button')
        if collapse.count() and collapse.is_visible():
            collapse.click()
        page.set_viewport_size({'width': 390, 'height': 844})
        page.wait_for_timeout(350)
        healthy(page)
        width = page.evaluate('({viewport:innerWidth,document:document.documentElement.scrollWidth})')
        assert width['document'] <= width['viewport'] + 2, width
        hidden_values = page.locator('.si-hero-art').evaluate('''root=>{
          const cards=[...root.querySelectorAll('.si-float-card')],bad=[];
          cards.forEach((card,i)=>{const a=card.querySelector('strong').getBoundingClientRect();
            cards.slice(i+1).forEach(other=>{const b=other.getBoundingClientRect();
              if(Math.min(a.right,b.right)>Math.max(a.left,b.left)+2&&Math.min(a.bottom,b.bottom)>Math.max(a.top,b.top)+2)bad.push(card.textContent);});});return bad;}''')
        assert not hidden_values, hidden_values
        capture(page, 'mobile-midnight')
        page.emulate_media(reduced_motion='reduce')
        assert page.locator('.si-sphere').evaluate('(e)=>getComputedStyle(e).animationName') == 'none'
        assert page.locator('.si-marquee-track').evaluate('(e)=>getComputedStyle(e).animationName') == 'none'
        browser.close()
    print('Chrome passed: glass, repeated switching with frame-sampled contrast, dropdowns, Decision lab, mobile and reduced motion.', flush=True)
finally:
    server.terminate()
    server.wait(timeout=10)
