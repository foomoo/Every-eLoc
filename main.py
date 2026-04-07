from fastapi import FastAPI, Request, Header, HTTPException, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from user_agents import parse
import httpx
import ipaddress
import logging
from typing import Optional, Tuple
from cachetools import TTLCache
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from models import VisitorInfo, ErrorResponse
from utils import anonymize_ip as utils_anonymize_ip, format_plain_text

# Initialize App
app = FastAPI(title="Visitor Info API", version="1.0.0")

# Setup Logging (scrubbing IP logs later, keeping it simple here)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate Limiter
# Using a custom key func that respects X-Appengine-User-Ip
def get_client_ip(request: Request) -> str:
    gae_ip = request.headers.get("X-Appengine-User-Ip")
    if gae_ip:
        return gae_ip
    return request.client.host if request.client else "127.0.0.1"

limiter = Limiter(key_func=get_client_ip, default_limits=["300/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Caching GeoIP lookups (TTL 1 hour)
geoip_cache = TTLCache(maxsize=10000, ttl=3600)

async def get_geoip_data(ip: str) -> dict:
    if ip in geoip_cache:
        return geoip_cache[ip]
    
    # Query ip-api for geolocation info
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,zip,timeZone,isp,as,proxy"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "success":
                geoip_cache[ip] = data
                return data
    except Exception as e:
        logger.warning(f"Failed to fetch GeoIP data: {e}")
    
    return {}

def is_private_ip(ip: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback
    except ValueError:
        return True

async def extract_visitor_info(request: Request, anonymize: bool = False) -> Tuple[VisitorInfo, bool]:
    ip = get_client_ip(request)
    if not ip or is_private_ip(ip):
        raise HTTPException(status_code=400, detail="INVALID_OR_PRIVATE_IP")
    
    # Extract headers
    user_agent_str = request.headers.get("user-agent", "")
    ua = parse(user_agent_str)
    
    os_info = f"{ua.os.family} {ua.os.version_string}".strip() if ua.os.family else None
    browser_info = f"{ua.browser.family} {ua.browser.version_string}".strip() if ua.browser.family else None
    
    if anonymize:
        ip_display = utils_anonymize_ip(ip)
    else:
        ip_display = ip

    ip_obj = ipaddress.ip_address(ip)

    info = VisitorInfo(
        ipv4=ip_display if ip_obj.version == 4 else None,
        ipv6=ip_display if ip_obj.version == 6 else None,
        os=os_info,
        browser=browser_info
    )

    geo_data = await get_geoip_data(ip)
    partial_data = False
    if geo_data:
        info.city = geo_data.get("city")
        info.state_region = geo_data.get("regionName")
        info.postal_code = geo_data.get("zip")
        info.country = geo_data.get("country")
        info.isp = geo_data.get("isp")
        asn_str = geo_data.get("as")
        info.asn = asn_str.split(" ")[0].replace("AS", "") if asn_str else None
        info.time_zone = geo_data.get("timeZone")
        info.proxy_check = geo_data.get("proxy", False)
    else:
        partial_data = True
    
    return info, partial_data

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    accept = request.headers.get("accept", "")
    is_api = request.url.path.startswith("/api/")
    
    status_code = exc.status_code
    error_code = exc.detail if isinstance(exc.detail, str) else "ERROR"
    message = "An error occurred."
    
    if is_api or "application/json" in accept:
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(error_code=error_code, message=message).model_dump()
        )
    else:
        return PlainTextResponse(f"Error: [{error_code}] {message}", status_code=status_code)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}", exc_info=True)
    accept = request.headers.get("accept", "")
    is_api = request.url.path.startswith("/api/")
    
    if is_api or "application/json" in accept:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error_code="INTERNAL_ERROR", message="Internal Server Error").model_dump()
        )
    else:
        return PlainTextResponse("Error: [INTERNAL_ERROR] Internal Server Error", status_code=500)


@app.get("/health", response_class=JSONResponse)
def health_check():
    return {"status": "healthy"}


@app.api_route("/api/v1/trace", methods=["GET", "POST"], response_model=VisitorInfo)
@limiter.limit("300/minute")
async def api_trace(request: Request, anonymize: bool = False):
    info, partial = await extract_visitor_info(request, anonymize)
    headers = {"X-Service-Warning": "Partial Data"} if partial else {}
    return JSONResponse(content=info.model_dump(), headers=headers)


@app.api_route("/", methods=["GET", "POST"])
@limiter.limit("300/minute")
async def root_trace(request: Request, anonymize: bool = False):
    info, partial = await extract_visitor_info(request, anonymize)
    headers = {"X-Service-Warning": "Partial Data"} if partial else {}
    
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        return JSONResponse(content=info.model_dump(), headers=headers)
    else:
        plain_text = format_plain_text(info)
        return PlainTextResponse(content=plain_text, headers=headers)
