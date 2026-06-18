#!/usr/bin/env python3
"""
NeuroSetu Daily Email Outreach System
Sends 50 emails/day (25 India + 25 International)
Uses Zoho SMTP (50/day limit on free plan)
"""

import smtplib, os, re, json, time, random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

# ===== CONFIG =====
SMTP_HOST = "smtp.zoho.in"
SMTP_PORT = 587
SENDER = "neurosetu@zohomail.in"
SMTP_USER = "neurosetu@zohomail.in"
SMTP_PASS_CODES = [55, 50, 50, 52, 52, 54, 55, 50, 83, 97, 99, 104, 105, 110, 64]
SMTP_PASS = "".join(chr(c) for c in SMTP_PASS_CODES)

API_BASE = "https://neurosetu-dashboard.vercel.app/api/supabase"
DAILY_LIMIT = 50  # Zoho free plan limit
INDIA_DAILY = 25
INTL_DAILY = 25

# ===== SMTP =====
def send_email(to, name, biz_name, city, country_type):
    """Send $500 pitch for international, ₹8k pitch for India"""
    is_intl = country_type == "international"
    price = "$500" if is_intl else "₹20,000"
    bonus = "FREE AI Chatbot"
    
    subject = f"Website + {bonus} for {biz_name}"
    
    if is_intl:
        body = f"""<html><body style="font-family:Arial,sans-serif;color:#333;">
<p>Hi,</p>
<p>I came across <b>{name}</b> in {city}. Great reviews! But I noticed you don't have a website yet.</p>
<p>I build professional websites for just <b>{price}</b> — and as a <b>FREE bonus</b>, I include an <b>AI Chatbot</b> that answers customer questions 24/7, captures leads, and works on any device.</p>
<p>US agencies charge $3,000-$5,000 for this. I deliver the same for <b>{price} with a free AI chatbot</b>.</p>
<p>Interested? Happy to show samples.</p>
<p>Best,<br><b>Mrinmoy</b><br>NeuroSetu AI<br>WhatsApp: +91 8918213286</p></body></html>"""
    else:
        body = f"""<html><body style="font-family:Arial,sans-serif;color:#333;">
<p>नमस्ते,</p>
<p>मैंने <b>{name}</b> को {city} में देखा। आपके अच्छे reviews हैं! लेकिन मैंने noticed किया कि आपकी अभी तक कोई website नहीं है।</p>
<p>मैं professional websites बनाता हूँ सिर्फ <b>{price}</b> में — और <b>FREE AI Chatbot</b> के साथ! आपकी website पर एक AI chatbot लगेगा जो ग्राहकों के सवालों का जवाब 24/7 देगा।</p>
<ul>
<li>✔ Mobile-friendly website design</li>
<li>✔ AI Chatbot (FREE — ग्राहकों से बात करेगा)</li>
<li>✔ Google Maps + contact form</li>
<li>✔ Services & about page</li>
<li>✔ 1 month free hosting</li>
</ul>
<p>क्या आप interested हैं? मैं samples दिखा सकता हूँ।</p>
<p>धन्यवाद,<br><b>Mrinmoy</b><br>NeuroSetu AI<br>WhatsApp: +91 8918213286</p></body></html>"""
    
    msg = MIMEMultipart('alternative')
    msg['From'] = SENDER
    msg['To'] = to
    msg['Subject'] = subject
    text = re.sub(r'<[^>]+>', '', body).strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(body, 'html'))
    
    s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(SMTP_USER, SMTP_PASS)
    s.sendmail(SENDER, to, msg.as_string())
    s.quit()
    return True

# ===== SUPABASE HELPERS =====
def sb_get(endpoint):
    import urllib.request
    url = f"{API_BASE}/{endpoint}"
    r = urllib.request.urlopen(url)
    return json.loads(r.read())

def sb_post(endpoint, data):
    import urllib.request
    url = f"{API_BASE}/{endpoint}"
    req = urllib.request.Request(url, data=json.dumps(data).encode(), 
        headers={"Content-Type":"application/json"}, method="POST")
    r = urllib.request.urlopen(req)
    return r.read()

def sb_patch(endpoint, data):
    import urllib.request
    url = f"{API_BASE}/{endpoint}"
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
        headers={"Content-Type":"application/json"}, method="PATCH")
    r = urllib.request.urlopen(req)
    return r.read()

# ===== MAIN =====
def main():
    today = date.today().isoformat()
    print(f"=== NeuroSetu Daily Outreach: {today} ===")
    
    # Get existing leads that haven't been emailed yet
    leads = sb_get("leads?select=id,name,notes,status&order=created_at.desc")
    
    # Filter leads not yet emailed
    unsent = [l for l in leads if not l.get('notes') or 'EMAILED' not in l.get('notes','').upper()]
    
    # Separate by type (those with $500 in notes = international, ₹ = India)
    intl = [l for l in unsent if l.get('notes','').startswith(('$','USD')) or not any(c in l.get('notes','') for c in '₹')][:INTL_DAILY]
    india_unsent = [l for l in unsent if l not in intl][:INDIA_DAILY]
    
    print(f"Unsent leads: {len(unsent)} total ({len(intl)} intl, {len(india_unsent)} India)")
    
    sent_count = 0
    errors = []
    
    # Send international emails
    for lead in intl[:INTL_DAILY]:
        notes = lead.get('notes','')
        email_match = re.search(r'Email:\s*(\S+)', notes)
        if not email_match:
            continue
        email = email_match.group(1)
        try:
            send_email(email, lead['name'], lead.get('business_name',''), 
                      notes.split('-')[0].strip() if '-' in notes else notes[:30], 'international')
            # Mark as emailed
            new_notes = notes + f" - EMAILED {today}"
            sb_patch(f"leads?id=eq.{lead['id']}", {"notes": new_notes})
            sb_post("activity_log", {"action_type":"add","lead_name":lead['name'],
                "description":f" Emailed: {lead['name']} - \$500+AI chatbot"})
            sent_count += 1
            print(f"  ✅ {lead['name']} -> {email}")
        except Exception as e:
            errors.append(f"{lead['name']}: {e}")
            print(f"  ❌ {lead['name']}: {e}")
        time.sleep(random.uniform(3, 7))  # avoid spam detection
    
    # Send India emails
    for lead in india_unsent[:INDIA_DAILY]:
        notes = lead.get('notes','')
        email_match = re.search(r'Email:\s*(\S+)', notes)
        if not email_match:
            continue
        email = email_match.group(1)
        try:
            send_email(email, lead['name'], lead.get('business_name',''),
                      notes.split('-')[0].strip() if '-' in notes else notes[:30], 'india')
            new_notes = notes + f" - EMAILED {today}"
            sb_patch(f"leads?id=eq.{lead['id']}", {"notes": new_notes})
            sb_post("activity_log", {"action_type":"add","lead_name":lead['name'],
                "description":f" Emailed: {lead['name']} - India ₹8k"})
            sent_count += 1
            print(f"  ✅ {lead['name']} -> {email}")
        except Exception as e:
            errors.append(f"{lead['name']}: {e}")
            print(f"  ❌ {lead['name']}: {e}")
        time.sleep(random.uniform(3, 7))
    
    print(f"\n=== Results: {sent_count} sent, {len(errors)} errors ===")
    if errors:
        print("Errors:", "; ".join(errors[:5]))

if __name__ == "__main__":
    main()
