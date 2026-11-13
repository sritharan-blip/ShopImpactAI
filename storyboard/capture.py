"""Capture synthetic UI evidence without modifying app source or persistent data."""
import json,io,time,subprocess,sys
from pathlib import Path
from urllib.request import urlopen
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"storyboard"/"captures";OUT.mkdir(parents=True,exist_ok=True)
manifest={}
def healthy(p):
    errors=p.locator('[data-testid="stException"]')
    assert errors.count()==0,errors.all_inner_texts()
def reset(p):
    p.evaluate("""window.scrollTo(0,0);document.querySelector('[data-testid="stMain"]')?.scrollTo(0,0);
    const s=document.querySelector('[data-testid="stSidebar"]');if(s)for(const e of [s,...s.querySelectorAll('div')])if(/auto|scroll/.test(getComputedStyle(e).overflowY))e.scrollTo(0,0);""")
def snap(p,name,points=(),focus=None,side=False):
    healthy(p)
    if focus:focus.scroll_into_view_if_needed()
    else:reset(p)
    p.wait_for_timeout(250)
    for b in p.locator('[data-testid="stToast"] button').all():
        try:b.click(timeout=800)
        except Exception:pass
    raw=p.screenshot(animations="disabled")
    image=Image.open(io.BytesIO(raw)).convert("RGB")
    if side:
        b=p.locator('[data-testid="stSidebar"] [data-testid="stExpander"]').filter(has_text="Data backup").bounding_box()
        clip=(int(b["x"])-5,int(b["y"])-8,int(b["x"]+b["width"])+5,int(b["y"]+b["height"])+8)
    else:
        b=p.locator('[data-testid="stMain"]').bounding_box()
        clip=(int(b["x"])+15,55,image.width-15,image.height-10)
    clip=(max(0,clip[0]),max(0,clip[1]),min(image.width,clip[2]),min(image.height,clip[3]))
    marks=[]
    for i,(label,loc) in enumerate(points,1):
        try:
            box=loc.bounding_box(timeout=1000)
            x=(box["x"]+box["width"]/2-clip[0])/(clip[2]-clip[0])
            y=(box["y"]+box["height"]/2-clip[1])/(clip[3]-clip[1])
            if .01<x<.99 and .01<y<.99:marks.append({"n":i,"label":label,"x":x,"y":y})
        except Exception:pass
    image.crop(clip).save(OUT/(name+".jpg"),quality=88,optimize=True)
    manifest[name]={"file":name+".jpg","marks":marks,"size":image.crop(clip).size}
    print("CAPTURED "+name,flush=True)
def nav(p,label,title=None):
    s=p.locator('[data-testid="stSidebar"]')
    s.get_by_text(label,exact=False).first.click()
    if title:p.get_by_role("heading",name=title,exact=True).wait_for()
    p.wait_for_timeout(200);healthy(p)
def seed(p):
    p.goto("http://127.0.0.1:8519")
    p.locator(".si-hero").wait_for()
    p.get_by_role("button",name="Load demo data",exact=True).click()
    p.locator(".si-hero small").filter(has_text="9 purchases").wait_for()
def combo(p,label,option):
    p.keyboard.press("Tab")
    p.wait_for_timeout(800)
    for attempt in range(4):
        try:
            p.get_by_role("combobox",name=label,exact=True).click(force=True)
            p.get_by_role("option",name=option,exact=True).click(force=True,timeout=2500)
            p.wait_for_timeout(500)
            return
        except Exception:
            p.keyboard.press("Escape")
            p.wait_for_timeout(600)
    raise RuntimeError("Could not select "+label+" -> "+option)
server=subprocess.Popen([sys.executable,"-m","streamlit","run","ShopImpactAI.py","--server.address","127.0.0.1","--server.port","8519","--server.headless","true","--server.fileWatcherType","none"],cwd=ROOT,stdout=subprocess.DEVNULL)
try:
    for i in range(100):
        try:
            if urlopen("http://127.0.0.1:8519/_stcore/health",timeout=1).status==200:break
        except OSError:time.sleep(.2)
    else:raise RuntimeError("Server did not start")
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel="chrome",headless=True)
        context=browser.new_context(viewport={"width":1600,"height":1050},device_scale_factor=1)
        p=context.new_page();seed(p)
        snap(p,"overview_day",[("Monthly snapshot",p.locator('[data-testid="stMetric"]').first),("Decision lab",p.get_by_role("button",name="Try Decision lab",exact=True))])
        p.get_by_text("Midnight",exact=True).click()
        p.wait_for_function('getComputedStyle(document.documentElement).getPropertyValue("--si-page").trim()==="#070C19"')
        snap(p,"overview_dark",[("Live monthly cards",p.locator(".si-float-card").first),("Budget",p.locator('[data-testid="stMetric"]').first)])
        nav(p,"Discover products","Find things made to last.")
        p.get_by_role("textbox",name="Describe what you need",exact=True).fill("repairable laptop for studying")
        p.get_by_role("textbox",name="Describe what you need",exact=True).press("Enter")
        p.wait_for_timeout(400)
        snap(p,"discover",[("Shopping intent",p.get_by_role("textbox",name="Describe what you need",exact=True)),("Explainable matches",p.get_by_text("Your smart matches",exact=True))])
        nav(p,"Decision lab","A little pause. A better decision.")
        p.get_by_role("textbox",name="What caught your eye?",exact=True).fill("A useful jacket")
        combo(p,"Purchase category","Sustainable apparel / second-hand")
        p.get_by_role("button",name="Save a pause plan",exact=True).click()
        p.get_by_text("Saved. Revisit on",exact=False).wait_for()
        snap(p,"decision",[("Usage assumptions",p.get_by_role("slider",name="How often will you use it each week?",exact=True)),("Cost per use",p.locator(".si-decision-result"))])
        nav(p,"Mindful wishlist","Pause now. Choose with intention.")
        snap(p,"wishlist",[("Saved idea",p.get_by_text("A useful jacket",exact=False).first),("Revisit plans",p.locator('[data-testid="stMetric"]').last)])
        nav(p,"Log a purchase","Log a purchase")
        p.get_by_role("textbox",name="Product",exact=True).fill("Refurbished headphones")
        combo(p,"Category","Electronics")
        p.get_by_role("spinbutton",name="Price ($)",exact=True).fill("100")
        p.get_by_role("checkbox",name="I chose a greener alternative",exact=True).check()
        p.get_by_role("button",name="Add to my impact log",exact=True).click()
        p.get_by_text("Refurbished headphones added",exact=False).wait_for()
        snap(p,"log",[("Validated purchase",p.get_by_role("textbox",name="Product",exact=True)),("Scenario choice",p.get_by_role("checkbox",name="I chose a greener alternative",exact=True)),("Save to ledger",p.get_by_role("button",name="Add to my impact log",exact=True))])
        nav(p,"Impact analytics","Your impact, at a glance")
        snap(p,"analytics",[("Actual ledger totals",p.locator('[data-testid="stMetric"]').first),("Pace comparison",p.get_by_text("Month-end pace check",exact=True))])
        nav(p,"Swap studio","Keep the thing. Lower the impact.")
        p.get_by_role("textbox",name="What are you shopping for?",exact=True).fill("Everyday headphones")
        p.get_by_role("textbox",name="What are you shopping for?",exact=True).press("Enter")
        snap(p,"swaps",[("Scenario inputs",p.get_by_role("textbox",name="What are you shopping for?",exact=True)),("Estimated difference",p.get_by_text("Your comparison",exact=True))])
        nav(p,"Eco rewards","Eco rewards")
        snap(p,"rewards",[("Weekly challenge",p.get_by_text("This week's low-impact challenge",exact=True)),("Progress",p.get_by_text("Milestone progress",exact=True))])
        nav(p,"Overview");p.locator(".si-hero").wait_for()
        sidebar=p.locator('[data-testid="stSidebar"]')
        sidebar.get_by_text("Data backup",exact=True).click()
        p.wait_for_timeout(250)
        snap(p,"backup",side=True,focus=sidebar.get_by_text("Data backup",exact=True))
        nav(p,"Log a purchase","Log a purchase")
        p.get_by_text("Import an existing purchase log",exact=True).click()
        csv=b"product,category,price,date\nRefill bottle,Home & living,32,\nInvalid item,Electronics,NaN,\nFuture item,Electronics,10,2999-01-01\n"
        # The purchase uploader is outside the sidebar; target its input directly.
        p.locator('[data-testid="stMain"] input[type="file"]').set_input_files({"name":"examiner-demo.csv","mimeType":"text/csv","buffer":csv})
        p.get_by_role("button",name="Validate and import",exact=True).click()
        p.get_by_text("Some rows were skipped:",exact=False).wait_for()
        snap(p,"csv_validation",[("Import validation",p.get_by_role("button",name="Validate and import",exact=True)),("Feedback",p.get_by_text("Some rows were skipped:",exact=False))])
        # Optional commerce route starts in a separate synthetic Streamlit session.
        checkout=browser.new_context(viewport={"width":1600,"height":1050},device_scale_factor=1)
        q=checkout.new_page();seed(q)
        q.get_by_text("Midnight",exact=True).click()
        q.wait_for_function('getComputedStyle(document.documentElement).getPropertyValue("--si-page").trim()==="#070C19"')
        nav(q,"My profile","Make this space yours.")
        q.get_by_role("textbox",name="Your name",exact=True).fill("Maya Demo")
        q.get_by_role("textbox",name="Email for your demo order summary",exact=True).fill("maya@example.com")
        q.get_by_role("button",name="Save local profile",exact=True).click()
        q.get_by_text("Welcome, Maya Demo.",exact=False).wait_for()
        snap(q,"profile",[("Session identity",q.get_by_role("textbox",name="Your name",exact=True)),("Privacy preference",q.get_by_role("checkbox",name="Use my purchase history to personalize local recommendations",exact=True))])
        nav(q,"Discover products","Find things made to last.")
        q.locator(".st-key-product_refurb-phone button").click()
        heading=q.get_by_role("heading",name="Certified refurbished smartphone",level=2,exact=True)
        heading.wait_for();heading.scroll_into_view_if_needed()
        quantity=q.get_by_role("spinbutton",name="Quantity",exact=True)
        quantity.fill("2");quantity.press("Tab");q.wait_for_timeout(600)
        snap(q,"product_details",[("Demo product factor",q.get_by_text("Compared with category average",exact=True)),("Quantity",quantity)],focus=heading)
        q.get_by_role("button",name="Add to cart",exact=True).click()
        nav(q,"Cart & checkout","Your shopping cart")
        q.get_by_role("textbox",name="Delivery city",exact=True).fill("Demo Town")
        q.get_by_role("textbox",name="Postal code",exact=True).fill("000000")
        q.get_by_role("checkbox",name="I understand this is a non-binding demo order.",exact=True).check()
        snap(q,"cart",[("Quantity control",q.locator(".si-qty")),("Non-binding checkout",q.get_by_role("button",name="Place demo order",exact=True))])
        q.get_by_role("button",name="Place demo order",exact=True).click()
        q.get_by_role("heading",name="Orders & tracking",exact=True).wait_for()
        snap(q,"orders",[("Recorded demo status",q.get_by_text("Demo status",exact=True)),("Manual simulation",q.get_by_role("button",name="Advance demo to preparing",exact=True))])
        nav(q,"Help & returns","Here for the whole journey.")
        q.get_by_role("button",name="Create demo request",exact=True).click()
        q.get_by_text("It has not been sent to a retailer.",exact=False).wait_for()
        snap(q,"returns",[("Return preference",q.get_by_text("What would you prefer?",exact=True)),("Session request",q.get_by_role("button",name="Create demo request",exact=True))])
        q.get_by_role("tab",name="Customer support",exact=True).click()
        q.get_by_role("textbox",name="Tell us a little more",exact=True).fill("Demo question: how is my category impact estimate calculated?")
        q.get_by_role("button",name="Save demo support request",exact=True).click()
        q.get_by_text("No support team was contacted.",exact=False).wait_for()
        snap(q,"support",[("Support message",q.get_by_role("textbox",name="Tell us a little more",exact=True)),("Local save",q.get_by_role("button",name="Save demo support request",exact=True))])
        nav(p,"Overview");p.locator(".si-hero").wait_for()
        button=p.locator('[data-testid="stSidebarCollapseButton"] button')
        if button.count() and button.is_visible():button.click()
        p.set_viewport_size({"width":390,"height":900});p.wait_for_timeout(300)
        Image.open(io.BytesIO(p.screenshot(animations="disabled"))).convert("RGB").save(OUT/"mobile.jpg",quality=88)
        manifest["mobile"]={"file":"mobile.jpg","marks":[],"size":[390,900]}
        browser.close()
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2))
finally:
    server.terminate();server.wait(timeout=10)
