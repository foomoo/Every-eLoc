from pydantic import BaseModel
from typing import Optional

class VisitorInfo(BaseModel):
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    proxy_check: bool = False
    detected_proxy_country: Optional[str] = None
    proxy_type: Optional[str] = None
    os: Optional[str] = None
    browser: Optional[str] = None
    city: Optional[str] = None
    state_region: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    isp: Optional[str] = None
    asn: Optional[str] = None
    time_zone: Optional[str] = None

class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str
