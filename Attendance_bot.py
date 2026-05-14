import requests
from bs4 import BeautifulSoup
import time
import re
import sys

print("="*40)
print("      BMSCE ATTENDANCE SNIPER")
print("="*40)

# --- 1. CLEAN INPUT COLLECTION ---
USERNAME = input("📧 College Email: ").strip()

print("📅 DOB (Format: DD MM YYYY, example: 24 10 2007)")
dob_input = input("   Enter: ").strip().split()
if len(dob_input) != 3:
    print("❌ Invalid DOB. Please run again.")
    sys.exit()

DOB_DD = dob_input[0]
DOB_MM = dob_input[1]
DOB_YYYY = dob_input[2]

# Using standard input instead of getpass to prevent hidden Windows terminal characters
FATHER_DIGITS = input("🔑 Father's Mobile (Last 4 digits): ").strip()

TOKEN = input("\n🤖 Telegram Bot Token (Press Enter to skip): ").strip()
if TOKEN:
    CHAT_ID = input("🆔 Telegram Chat ID: ").strip()
else:
    CHAT_ID = ""

# --- 2. YOUR EXACT WORKING CONFIG ---
COURSES = [
    {"name": "AI & Applications", "id": "1253"},
    {"name": "Python Programming", "id": "1279"},
    {"name": "Mathematics", "id": "1266"},
    {"name": "Applied Chemistry", "id": "1274"},
    {"name": "Constitution of India", "id": "1270"},
    {"name": "English", "id": "1269"}
]

COMMON_IDS = {"secId": "88", "semId": "92"}

session = requests.Session()
login_url = "https://students.bmsce.ac.in/parents/index.php"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://students.bmsce.ac.in/parents/index.php"
}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[-] Telegram Error: {e}")

def get_full_report():
    password = f"{DOB_YYYY}-{DOB_MM}-{DOB_DD}"
    
    # Phase 1: Initial Login
    print("\n[*] Phase 1: Authenticating...")
    res1 = session.get(login_url, headers=headers)
    soup1 = BeautifulSoup(res1.text, 'html.parser')
    payload1 = {tag['name']: tag.get('value', '') for tag in soup1.find_all("input", type="hidden") if tag.get('name')}
    payload1.update({"username": USERNAME, "dd": DOB_DD, "mm": DOB_MM, "yyyy": DOB_YYYY, "passwd": password, "option": "com_user", "task": "loginOtp", "token": ""})
    res2 = session.post(login_url, data=payload1, headers=headers)

    # Phase 2: 2FA Bypass
    print("[*] Phase 2: Bypassing 2FA...")
    soup2 = BeautifulSoup(res2.text, 'html.parser')
    payload2 = {tag['name']: tag.get('value', '') for tag in soup2.find_all("input", type="hidden") if tag.get('name')}
    payload2.update({"idType": "father", "enteredid": FATHER_DIGITS, "option": "com_user", "task": "login", "username": USERNAME, "passwd": password, "token": "", "action": "result_form"})
    res3 = session.post(login_url, data=payload2, headers=headers)

    # Phase 3: Scrape Subject Data
    report = f"📅 *BMSCE Report - {time.strftime('%d/%m/%y')}*\n" + "—" * 15 + "\n"
    
    for subject in COURSES:
        print(f"[*] Fetching: {subject['name']}...")
        
        # EXACT TIMING FROM YOUR WORKING SCRIPT
        time.sleep(1.5)  
        
        params = {
            "option": "com_studentdashboard", 
            "controller": "studentdashboard", 
            "task": "attendencelist", 
            "courseId": subject["id"], 
            **COMMON_IDS
        }
        
        res = session.get(login_url, params=params, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        page_text = soup.get_text()

        # Hunt for percentage using Regex (looks for "Overall : 90 %" or similar)
        match = re.search(r"Overall\s*:\s*(\d+)", page_text)
        
        if match:
            val = float(match.group(1))
            emoji = "🚨" if val < 85 else "✅"
            report += f"{emoji} {subject['name']}: *{val}%*\n"
        elif "%" in page_text:
            # Secondary check for any floating percentage
            backup_match = re.findall(r"(\d+)\s*%", page_text)
            if backup_match:
                val = float(backup_match[0])
                emoji = "🚨" if val < 85 else "✅"
                report += f"{emoji} {subject['name']}: *{val}%*\n"
            else:
                report += f"❓ {subject['name']}: *Data Missing*\n"
        else:
            report += f"❓ {subject['name']}: *Data Missing*\n"
            
    return report

if __name__ == "__main__":
    full_text = get_full_report()
    
    print("\n" + "="*30)
    print(full_text.replace('*', ''))
    print("="*30)
    
    if TOKEN and CHAT_ID:
        send_telegram_message(full_text)
        print("\n[+] Success! Report sent to your Telegram.")
