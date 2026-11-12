"""Optional real-Chrome checks. Install playwright, then run this file.

Uses an isolated browser context with demo data only. Saves screenshots as CI
artifacts; small encoded previews make remote visual review possible as well.
"""
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
OUTPUT = ROOT / 'test-results'
OUTPUT.mkdir(exist_ok=True)


def capture(page, name):
    page.evaluate("window.scrollTo(0,0); document.querySelector('[data-testid=\"stMain\"]')?.scrollTo(0,0)")
    raw = page.screenshot(path=str(OUTPUT / (name + '.png')), animations='disabled')
    image = Image.open(io.BytesIO(raw)).convert('RGB')
    image.thumbnail((1100, 900))
    data = io.BytesIO()
    image.save(data, format='JPEG', quality=75)
    print('PREVIEW:' + name + ':' + base64.b64encode(data.getvalue()).decode(), flush=True)


def assert_no_errors(page):
    assert page.locator('[data-testid="stException"]').count() == 0, page.locator('body').inner_text()


def assert_primary_contrast(page):
    colors = page.locator('button[data-testid="stBaseButton-primary"]').filter(has_text='Log a purchase').evaluate('b=>({bg:getComputedStyle(b).backgroundColor,fg:getComputedStyle(b.querySelector("p")).color})')
    def luminance(value):
        channels = [int(v) / 255 for v in value.strip('rgb()').split(',')]
        return sum(weight * (v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4)
                   for weight, v in zip([.2126, .7152, .0722], channels))
    a, b = sorted([luminance(colors['bg']), luminance(colors['fg'])])
    assert (b + .05) / (a + .05) >= 4.5, colors


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
        page = browser.new_page(viewport={'width': 1440, 'height': 1100}, device_scale_factor=1)
        page.goto('http://127.0.0.1:8519')
        page.locator('.si-hero').wait_for()
        page.get_by_role('button', name='Load demo data', exact=True).click()
        page.locator('.si-hero small').filter(has_text='9 purchases').wait_for()
        page.wait_for_function("document.querySelector('.si-hero-art img')?.naturalWidth > 0")
        assert_no_errors(page)
        assert_primary_contrast(page)
        print('CONTROLS:' + json.dumps(page.locator('button').evaluate_all('(buttons)=>buttons.filter(b=>b.textContent.includes("Midnight")||b.textContent.includes("Daylight")).map(b=>({text:b.textContent,testid:b.dataset.testid,role:b.getAttribute("role"),html:b.outerHTML.slice(0,1000)}))')), flush=True)
        capture(page, 'daylight-overview')
        page.get_by_text('Midnight', exact=True).click()
        page.wait_for_function("getComputedStyle(document.documentElement).getPropertyValue('--si-page').trim() === '#0B1415'")
        assert_no_errors(page)
        assert_primary_contrast(page)
        capture(page, 'midnight-overview')
        page.get_by_text('Discover products', exact=True).click()
        page.get_by_text('Your smart matches', exact=True).wait_for()
        assert_no_errors(page)
        capture(page, 'midnight-discover')
        page.locator('[data-testid="stSidebar"]').get_by_text('Log a purchase', exact=True).click()
        page.get_by_role('textbox', name='Product', exact=True).wait_for()
        assert_no_errors(page)
        controls = page.locator('[data-testid="stSelectbox"] [role="combobox"]').evaluate_all('els=>els.map(e=>({background:getComputedStyle(e).backgroundColor,html:e.outerHTML.slice(0,500)}))')
        print('FORM_CONTROLS:' + json.dumps(controls), flush=True)
        assert controls and all(c['background'] == 'rgb(28, 44, 43)' for c in controls), controls
        capture(page, 'midnight-form')
        page.locator('[data-testid="stSidebar"]').get_by_text('Overview', exact=True).click()
        page.locator('.si-hero').wait_for()
        page.set_viewport_size({'width': 390, 'height': 844})
        # Streamlit may collapse the sidebar at this width; close it if still open.
        close_sidebar = page.locator('[data-testid="stSidebarCollapseButton"] button')
        if close_sidebar.count() and close_sidebar.is_visible():
            close_sidebar.click()
        page.wait_for_timeout(300)
        assert_no_errors(page)
        width = page.evaluate('({viewport:innerWidth,document:document.documentElement.scrollWidth})')
        assert width['document'] <= width['viewport'] + 2, width
        capture(page, 'mobile-midnight')
        page.emulate_media(reduced_motion='reduce')
        motion = page.locator('.si-marquee-track').evaluate('(e) => getComputedStyle(e).animationName')
        assert motion == 'none', motion
        browser.close()
    print('Real Chrome checks passed: themes, catalog, form, mobile, reduced motion.', flush=True)
finally:
    server.terminate()
    server.wait(timeout=10)
