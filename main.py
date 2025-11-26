#!/usr/bin/env python3
"""
AccessControl_Final.py
Created on: 2025-11-22
Author: Stefano Selmin
"""

import ujson as json, os, ubinascii, time
from machine import Pin, I2C
import ssd1306
from cryptolib import aes
import picoweb, uasyncio as asyncio

AES_KEY = b'1234567890abcdef'
JSON_FILE = "db.enc"

# ----------------------------
# CRYPTO
# ----------------------------
class Crypto:
    def __init__(self, key):
        self.cipher = aes(key, 1)
    def encrypt(self, data):  # str -> hex
        pad_len = 16 - len(data)%16
        data += chr(pad_len)*pad_len
        return ubinascii.hexlify(self.cipher.encrypt(data.encode())).decode()
    def decrypt(self, enc_hex):
        enc = ubinascii.unhexlify(enc_hex)
        dec = self.cipher.decrypt(enc)
        pad_len = dec[-1]
        return dec[:-pad_len].decode()

crypto = Crypto(AES_KEY)

# ----------------------------
# DB
# ----------------------------
def load_db():
    if JSON_FILE not in os.listdir(): return []
    with open(JSON_FILE) as f: return json.loads(crypto.decrypt(f.read()))
def save_db(data):
    with open(JSON_FILE,"w") as f: f.write(crypto.encrypt(json.dumps(data)))

db = load_db()

# ----------------------------
# DISPLAY & ROTARY
# ----------------------------
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
enc_a, enc_b = Pin(32, Pin.IN), Pin(33, Pin.IN)
btn = Pin(25, Pin.IN, Pin.PULL_UP)

menu_level=0
current_index=0
current_category=None
current_entry=None
user_categories=[]

# ----------------------------
# DISPLAY FUNCTIONS
# ----------------------------
def show_categories(): 
    oled.fill(0)
    for i,cat in enumerate(user_categories):
        prefix=">" if i==current_index else " "
        oled.text(f"{prefix}{cat['nome']}",0,i*10)
    oled.show()
def show_entries():
    oled.fill(0)
    for i,e in enumerate(current_category['entries']):
        prefix=">" if i==current_index else " "
        oled.text(f"{prefix}{e['titolo']}",0,i*10)
    oled.show()
def show_entry_details():
    e=current_entry
    oled.fill(0)
    oled.text(f"T:{e['titolo']}",0,0)
    oled.text(f"U:{e['utente']}",0,10)
    oled.text(f"P:{e['password']}",0,20)
    oled.text(f"URL:{e['url']}",0,30)
    oled.text(f"Note:{e['note']}",0,40)
    oled.show()
def update_display():
    if menu_level==0: show_categories()
    elif menu_level==1: show_entries()
    elif menu_level==2: show_entry_details()

# ----------------------------
# ROTARY CALLBACK
# ----------------------------
def menu_count():
    if menu_level==0: return len(user_categories)
    elif menu_level==1: return len(current_category['entries'])
    return 1
def rotate_callback(pin):
    global current_index
    if enc_a.value()!=enc_b.value(): current_index=(current_index+1)%menu_count()
    else: current_index=(current_index-1)%menu_count()
    update_display()
enc_a.irq(trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=rotate_callback)

# ----------------------------
# BUTTON CALLBACK
# ----------------------------
def btn_callback(pin):
    global menu_level, current_index, current_category, current_entry
    if menu_level==0:
        current_category=user_categories[current_index]
        current_index=0
        menu_level=1
    elif menu_level==1:
        current_entry=current_category['entries'][current_index]
        menu_level=2
    elif menu_level==2: menu_level=1
    update_display()
btn.irq(trigger=Pin.IRQ_FALLING,handler=btn_callback)

# ----------------------------
# FINGERPRINT LOGIN
# ----------------------------
def check_fingerprint():
    return "Stefano"  # placeholder

# ----------------------------
# WEB SERVER
# ----------------------------
app=picoweb.WebApp(__name__)
def auth_required(req,resp):
    auth=req.headers.get("Authorization")
    if not auth:
        resp.headers["WWW-Authenticate"]='Basic realm="Login"'
        yield from resp.awrite("401 Unauthorized")
        return False
    user_pass=ubinascii.a2b_base64(auth.split(" ")[1]).decode()
    user,passwd=user_pass.split(":")
    for u in db:
        if u["nome"]==user and u.get("password_api")==passwd: return user
    yield from resp.awrite("403 Forbidden")
    return False

# FRONTEND
@app.route("/")
def index(req,resp):
    yield from resp.awrite("""
<html>
<head><title>AccessControl</title></head>
<body>
<h3>AccessControl</h3>
<div id="cats"></div>
<div id="entries"></div>
<div id="form" style="display:none;">
<input id="titulo"><input id="utente"><input id="password">
<input id="url"><input id="note">
<button onclick="save()">Save</button><button onclick="cancel()">Cancel</button>
</div>
<script>
let currentCat="";
function fetchCats(){fetch("/categories").then(r=>r.json()).then(d=>{let html="";d.forEach(c=>{html+=`<button onclick="fetchEnt('${c.nome}')">${c.nome}</button>`});document.getElementById("cats").innerHTML=html;});}
function fetchEnt(cat){currentCat=cat;fetch(`/entries/${cat}`).then(r=>r.json()).then(d=>{let html="";d.forEach(e=>{html+=`<div>${e.titolo} <button onclick="edit('${e.titolo}')">Edit</button><button onclick="del('${e.titolo}')">Del</button></div>`});html+=`<button onclick="add()">Add</button>`;document.getElementById("entries").innerHTML=html;});}
function add(){document.getElementById("form").style.display="block";}
function edit(t){document.getElementById("form").style.display="block";}
function cancel(){document.getElementById("form").style.display="none";}
function save(){document.getElementById("form").style.display="none";fetch(`/entries/${currentCat}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({titulo:"demo",utente:"demo",password:"demo",url:"",note:""})}).then(()=>fetchEnt(currentCat));}
function del(t){fetch(`/entries/${currentCat}/${t}`,{method:"DELETE"}).then(()=>fetchEnt(currentCat));}
fetchCats();
</script>
</body>
</html>
""")

# API
@app.route("/categories")
def get_categories(req,resp):
    user=yield from auth_required(req,resp)
    if not user: return
    cats=next(u["categorie"] for u in db if u["nome"]==user)
    yield from resp.awrite(json.dumps([{"nome":c["nome"]} for c in cats]))

@app.route("/entries/<cat>")
def get_entries(req,resp,cat):
    user=yield from auth_required(req,resp)
    if not user: return
    c=next(c for c in next(u["categorie"] for u in db if u["nome"]==user) if c["nome"]==cat)
    yield from resp.awrite(json.dumps(c["entries"]))

@app.route("/entries/<cat>",methods=["POST"])
def add_entry(req,resp,cat):
    user=yield from auth_required(req,resp)
    if not user: return
    data=yield from req.read_form_data()
    e=json.loads(data[0][1])
    cats=next(u["categorie"] for u in db if u["nome"]==user)
    c=next(c for c in cats if c["nome"]==cat)
    for i,entry in enumerate(c["entries"]):
        if entry["titolo"]==e["titolo"]: c["entries"][i]=e; break
    else: c["entries"].append(e)
    save_db(db)
    yield from resp.awrite(json.dumps({"status":"ok"}))

@app.route("/entries/<cat>/<titulo>",methods=["DELETE"])
def delete_entry(req,resp,cat,titulo):
    user=yield from auth_required(req,resp)
    if not user: return
    cats=next(u["categorie"] for u in db if u["nome"]==user)
    c=next(c for c in cats if c["nome"]==cat)
    c["entries"]=[e for e in c["entries"] if e["titolo"]!=titulo]
    save_db(db)
    yield from resp.awrite(json.dumps({"status":"ok"}))

# ----------------------------
# MAIN
# ----------------------------
def main():
    global user_categories
    user=check_fingerprint()
    if not user:
        oled.fill(0)
        oled.text("Access Denied",0,0)
        oled.show()
        return
    oled.fill(0)
    oled.text(f"Hello {user}",0,0)
    oled.show()
    time.sleep(2)
    user_categories=next(u["categorie"] for u in db if u["nome"]==user)
    update_display()
    print("Web server on 0.0.0.0:80")
    asyncio.run(app.run(host="0.0.0.0",port=80))

if __name__=="__main__":
    main()
