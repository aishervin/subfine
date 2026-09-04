import requests
import base64
import json
import re
from urllib.parse import urlparse


def get_v2ray_configs(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        # V2Ray subscriptions are often base64 encoded
        decoded_content = base64.b64decode(response.text).decode('utf-8')
        return decoded_content.splitlines()
    except Exception as e:
        print(f"Error fetching or decoding configs from {url}: {e}")
        return []


def is_host_reachable(host, port=443, timeout=5):
    """
    Performs a basic TCP reachability check to the specified host and port.
    This is not an ICMP ping and does not validate V2Ray protocol.
    It's a heuristic to check if a server is generally responsive on a common port.
    """
    if not host:
        return False
    try:
        # Attempt to make a simple HTTP/HTTPS connection
        # This is a common way to check if a server is alive and listening.
        # For V2Ray, the actual port might differ, but 443 is a good general test.
        # We use a small timeout to avoid long waits for dead hosts.
        requests.head(f"https://{host}:{port}", timeout=timeout, verify=False)
        print(f"Host {host}:{port} appears reachable.")
        return True
    except requests.exceptions.ConnectionError:
        print(f"Host {host}:{port} connection error (likely unreachable).")
        return False
    except requests.exceptions.Timeout:
        print(f"Host {host}:{port} timed out (likely unreachable).")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Host {host}:{port} encountered an error: {e}")
        return False


def extract_host_from_v2ray_uri(uri):
    """
    Extracts the hostname or IP address from various V2Ray URI formats.
    """
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
            # Fallback for unknown formats, try to find an IP or domain pattern
            match = re.search(r'\b([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b|\b(?:[a-zA-Z0-9]+\.)+[a-zA-Z]{2,}\b)', uri)
            if match:
                return match.group(0)
            return None
    except Exception as e:
        print(f"Error extracting host from URI '{uri}': {e}")
        return None


def main():
    subscription_url = "https://subshen.pages.dev"
    output_file = "filtered_configs.txt"

    all_configs = get_v2ray_configs(subscription_url)
    if not all_configs:
        print("No configurations fetched or decoded. Exiting.")
        # Create an empty file if no configs are available
        with open(output_file, "w") as f:
            f.write("")
        return

    filtered_configs = []
    for config_uri in all_configs:
        if not config_uri.strip():
            continue

        host = extract_host_from_v2ray_uri(config_uri)
        if host:
            # Attempt to check reachability on port 443 as a general indicator
            if is_host_reachable(host, port=443):
                filtered_configs.append(config_uri)
            else:
                print(f"Skipping unreachable config: {config_uri}")
        else:
            print(f"Could not extract host from config, skipping: {config_uri}")

    # Join the filtered configs and re-encode them to base64
    if filtered_configs:
        final_output_content = "\n".join(filtered_configs)
        encoded_final_output = base64.b64encode(final_output_content.encode('utf-8')).decode('utf-8')
    else:
        encoded_final_output = ""  # No configs left

    with open(output_file, "w") as f:
        f.write(encoded_final_output)

    print(f"Filtered configurations saved to {output_file}")


if __name__ == "__main__":
    main()
