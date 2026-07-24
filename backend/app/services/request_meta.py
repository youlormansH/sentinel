from dataclasses import dataclass

from fastapi import Request
from user_agents import parse as parse_user_agent


@dataclass
class RequestMeta:
    ip_address: str
    user_agent: str
    device: str
    browser: str


def extract_request_meta(request: Request) -> RequestMeta:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    elif request.client:
        ip_address = request.client.host
    else:
        ip_address = "unknown"

    ua_string = request.headers.get("user-agent", "")
    ua = parse_user_agent(ua_string)
    device = ua.device.family if ua.device and ua.device.family != "Other" else (
        "Mobile" if ua.is_mobile else "Tablet" if ua.is_tablet else "Desktop"
    )
    browser = f"{ua.browser.family} {ua.browser.version_string}".strip()

    return RequestMeta(ip_address=ip_address, user_agent=ua_string, device=device, browser=browser)
