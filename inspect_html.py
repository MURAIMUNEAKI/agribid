import requests

url = "https://www.kkj.go.jp/s/?S=農業"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    response.encoding = response.apparent_encoding # Ensure correct encoding (likely Shift_JIS or UTF-8)
    
    with open("temp_source.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("Successfully saved HTML.")
except Exception as e:
    print(f"Error: {e}")
