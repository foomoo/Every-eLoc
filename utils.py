import ipaddress
from typing import Optional
from models import VisitorInfo

def anonymize_ip(ip: str) -> str:
    """Anonymize the provided IP address."""
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.version == 4:
            parts = ip.split('.')
            parts[-1] = '0'
            return '.'.join(parts)
        elif ip_obj.version == 6:
            # Masking to a /64 prefix
            net = ipaddress.ip_network(f"{ip}/64", strict=False)
            return str(net.network_address)
    except ValueError:
        return ip
    return ip

def format_plain_text(info: VisitorInfo) -> str:
    """Format the VisitorInfo into Plain Text as per the requirements."""
    # Mapping JSON dict values to Plain Text representation rules
    def safe_str(val, is_bool_proxy=False):
        if val is None:
            return "N/A"
        if is_bool_proxy:
            return "yes" if val else "no"
        return str(val)

    lines = [
        f"ipv4: {safe_str(info.ipv4)}",
        f"ipv6: {safe_str(info.ipv6)}",
        f"Proxy Check: {safe_str(info.proxy_check, True)}",
        f"Detected Proxy Country: {safe_str(info.detected_proxy_country)}",
        f"Proxy Type: {safe_str(info.proxy_type)}",
        f"OS: {safe_str(info.os)}",
        f"browser: {safe_str(info.browser)}",
        f"City: {safe_str(info.city)}",
        f"State/Region: {safe_str(info.state_region)}",
        f"Postal Code: {safe_str(info.postal_code)}",
        f"Country: {safe_str(info.country)}",
        f"ISP: {safe_str(info.isp)}",
        f"ASN: {safe_str(info.asn)}",
        f"Time Zone: {safe_str(info.time_zone)}"
    ]
    return "\n".join(lines) + "\n"
