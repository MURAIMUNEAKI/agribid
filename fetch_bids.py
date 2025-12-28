import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime, timedelta

BASE_URL = "https://www.kkj.go.jp"
SEARCH_URL = "https://www.kkj.go.jp/s/"

def get_latest_bids():
    """Scrapes the latest bids and returns them as a list of dicts."""
    all_items = []
    print("Starting scraper job...")
    
    # Date limit
    limit_date = datetime.now() - timedelta(days=60)
    print(f"Filtering items older than: {limit_date.strftime('%Y-%m-%d')}")

    # Configuration for scraping
    # "queries": list of params to send to server.
    # "title_keywords": list of strings, ONE of which MUST be in the title (OR logic).
    # If "title_keywords" is None, no title filtering is applied (for MAFF category).
    
    CONFIG = [
        # 1. Agriculture: 農業、農地、農協 + Farmstay (農泊、移住、定住、農業体験)
        {
            "id": "agriculture",
            "queries": [
                {"S": "農業"}, {"S": "農地"}, {"S": "農協"},
                {"S": "農泊"}, {"S": "移住"}, {"S": "定住"}, {"S": "農業体験"}
            ],
            "title_keywords": ["農業", "農地", "農協", "農泊", "移住", "定住", "農業体験"],
            "required_agencies": None
        },
        # 2. Food: 食品、食料品、米、小麦、野菜、食育
        {
            "id": "food",
            "queries": [
                {"S": "食品"}, {"S": "食料品"}, {"S": "米"},
                {"S": "小麦"}, {"S": "野菜"}, {"S": "食育"}
            ],
            "title_keywords": ["食品", "食料品", "米", "小麦", "野菜", "食育"],
            "required_agencies": None
        },
        # 4. MAFF (Other): All from Ministry of Agriculture
        # We search for "農林水産省" keyword to find candidates, 
        # then strictly filter by Agency Name.
        {
            "id": "other",
            "queries": [{"S": "農林水産省"}], 
            "title_keywords": None, 
            "required_agencies": ["農林水産省", "林野庁", "水産庁", "農政局"],
            "blacklist_agencies": ["県", "市", "町", "村", "教育委員会", "警察", "病院"] # Exclude local gov
        }
    ]

    for cat in CONFIG:
        print(f"Fetching category: {cat['id']}...")
        
        for q in cat['queries']:
            # Friendly label for progress
            q_str = list(q.values())[0] 
            print(f"  -> Searching for '{q_str}'...")

            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }

                # Allow fetching more items to ensure we find matches after filtering
                resp = requests.get(SEARCH_URL, params=q, headers=headers, timeout=20)
                resp.encoding = resp.apparent_encoding
                
                soup = BeautifulSoup(resp.text, "html.parser")
                results = soup.find_all("div", class_="box_contents")
                
                count = 0
                for item in results:
                    # Limit per keyword scan
                    if count >= 100: # Increased limit to ensure we find enough valid items
                        break
                    
                    # Extract Agency FIRST
                    agency = "不明"
                    dd_agency = item.find("dd", style=re.compile("text-align: left;"))
                    if dd_agency:
                        spans = dd_agency.find_all("span")
                        if spans:
                            agency = spans[0].get_text(strip=True)

                    # --- AGENCY FILTERING ---
                    # 1. Required Agencies (Whitelist)
                    if cat.get("required_agencies"):
                        hit = False
                        for req in cat["required_agencies"]:
                            if req in agency:
                                hit = True
                                break
                        if not hit:
                            # print(f"    Skipping (Agency mismatch): {agency}")
                            continue 
                    
                    # 2. Blacklist Agencies (Blacklist) - mainly for 'other' category
                    if cat.get("blacklist_agencies"):
                        hit_black = False
                        for bl in cat["blacklist_agencies"]:
                            if bl in agency:
                                hit_black = True
                                break
                        if hit_black:
                            # print(f"    Skipping (Agency blacklist): {agency}")
                            continue
                    # ------------------------

                    # Extract Title
                    dt = item.find("dt")
                    if not dt: continue
                    link_tag = dt.find("a")
                    if not link_tag: continue
                    title_text = link_tag.get_text(strip=True)
                    
                    # --- TITLE FILTERING ---
                    if cat["title_keywords"]:
                        hit = False
                        for kw in cat["title_keywords"]:
                            if kw in title_text:
                                hit = True
                                break
                        if not hit:
                            # print(f"    Skipping (Title mismatch): {title_text}")
                            continue 
                    # -----------------------

                    href = link_tag.get("href")
                    if not href or "/d/?D=" not in href:
                        continue
                        
                    full_url = BASE_URL + href
                    if "&L=" not in full_url:
                        full_url += "&L=ja"

                    # Extract Date & Filter (60 days)
                    date_display = ""
                    date_iso = ""
                    p_date = item.find("p", class_="fRight")
                    is_within_range = False 
                    
                    if p_date:
                        txt = p_date.get_text()
                        match = re.search(r"(\d{4}-\d{2}-\d{2})", txt)
                        if match:
                            raw_date = match.group(1)
                            try:
                                dt_obj = datetime.strptime(raw_date, "%Y-%m-%d")
                                date_display = f"{dt_obj.year}年{dt_obj.month}月{dt_obj.day}日"
                                date_iso = raw_date
                                if dt_obj >= limit_date:
                                    is_within_range = True
                            except:
                                date_display = raw_date
                                date_iso = raw_date # Fallback
                    
                    if not is_within_range:
                        continue

                    # Add to list
                    all_items.append({
                        "title": title_text,
                        "category": cat["id"],
                        "agency": agency,
                        "date": date_display,
                        "date_iso": date_iso, # For sorting
                        "url": full_url
                    })
                    count += 1
                
            except Exception as e:
                print(f"     -> Error: {e}")

    # Remove duplicates
    unique_map = {}
    for item in all_items:
        unique_map[item['title']] = item
    
    unique_items = list(unique_map.values())
    
    # Sort in Python just in case
    try:
        unique_items.sort(key=lambda x: x['date_iso'], reverse=True)
    except:
        pass # Ignore sort errors

    print(f"Total unique items found: {len(unique_items)}")

    return unique_items

if __name__ == "__main__":
    # If run as a script, generate the data.js file AND print JSON to stdout
    items = get_latest_bids()
    
    js_content = f"""// This file is auto-generated by fetch_bids.py
// Do not edit manually. Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

window.GENERATED_BID_DATA = {json.dumps(items, ensure_ascii=False, indent=4)};
"""

    with open("data.js", "w", encoding="utf-8") as f:
        f.write(js_content)
        
    # Also save as JSON for server to read easily if needed
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=4)

    print(f"Done. Saved {len(items)} unique items to data.js.")
