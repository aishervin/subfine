import concurrent.futures
import requests
import base64
import json
import re
from urllib.parse import urlparse


def get_v2ray_configs(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        decoded_content = base64.b64decode(response.text).decode('utf-8')
        return decoded_content.splitlines()
    except Exception as e:
        print(f"Error fetching or decoding configs from {url}: {e}")
        return []


def is_host_reachable(host, port=443, timeout=3):
    if not host:
        return False
    try:
        requests.head(f"https://{host}:{port}", timeout=timeout, verify=False)
        return True
    except Exception:
        return False


def extract_host_from_v2ray_uri(uri):
    try:
        if uri.startswith("vmess://"):
            encoded_config = uri[len("vmess://"):]
            decoded_config = base64.b64decode(encoded_config).decode('utf-8')
            config_json = json.loads(decoded_config)
            return config_json.get('add')
        elif uri.startswith(("vless://", "trojan://", "ss://", "ssr://")):
            parsed_url = urlparse(uri)
            return parsed_url.hostname
        else:
            match = re.search(r'\b([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b|\b(?:[a-zA-Z0-9]+\.)+[a-zA-Z]{2,}\b)', uri)
            if match:
                return match.group(0)
            return None
    except Exception as e:
        print(f"Error extracting host from URI '{uri}': {e}")
        return None


def check_single_config(config_uri):
    if not config_uri.strip():
        return None
    host = extract_host_from_v2ray_uri(config_uri)
    if host:
        if is_host_reachable(host, port=443, timeout=3):
            return config_uri
    return None


def main():
    subscription_url = "https://subshen.pages.dev"  # ← آدرس Worker شما
    output_file = "filtered_configs.txt"

    print("📥 دریافت سابسکریپشن از Worker...")
    all_configs = get_v2ray_configs(subscription_url)
    if not all_configs:
        print("❌ هیچ کانفیگی دریافت نشد.")
        with open(output_file, "w") as f:
            f.write("")
        return

    print(f"✅ تعداد کل کانفیگ‌های دریافت‌شده: {len(all_configs)}")

    # ✅ محدود کردن به ۴۰۰۰ عدد اول (حتی اگر Worker بیشتر بده)
    if len(all_configs) > 4000:
        print(f"⚠️ محدود کردن به ۴۰۰۰ کانفیگ اول (از {len(all_configs)} کانفیگ)")
        all_configs = all_configs[:4000]

    print(f"🚀 شروع پردازش هم‌زمان {len(all_configs)} کانفیگ با ۵۰ ترد...")

    filtered_configs = []
    max_workers = 50

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(check_single_config, all_configs)
        for result in results:
            if result:
                filtered_configs.append(result)

    print(f"✅ تعداد کانفیگ‌های معتبر: {len(filtered_configs)}")

    if filtered_configs:
        final_output_content = "\n".join(filtered_configs)
        encoded_final_output = base64.b64encode(final_output_content.encode('utf-8')).decode('utf-8')
    else:
        encoded_final_output = ""

    with open(output_file, "w") as f:
        f.write(encoded_final_output)

    print(f"💾 فایل {output_file} ذخیره شد.")


if __name__ == "__main__":
    main()
