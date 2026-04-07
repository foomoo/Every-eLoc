

\# User Requirements Document: Visitor Network \& IP Information Analysis System (Visitor Info API)



\## 1. Project Overview



\*\*1.1 Purpose\*\*

The purpose of this document is to define the functional requirements, non-functional requirements, and deployment architecture for the "Visitor Network \& IP Information Analysis System." It serves as a clear, definitive development guide for the Python engineering team.



\*\*1.2 Background\*\*

In modern web applications, understanding a client's network environment, geolocation, and device information is critical for security auditing, traffic analytics, content localization, and anti-fraud measures. This project aims to develop a lightweight, highly available service node that automatically parses and returns a comprehensive network fingerprint of the requester.



\---



\## 2. Core Objectives



Develop a Python-based web application capable of receiving and processing requests across multiple network protocols (HTTP, HTTPS, RESTful API). The system must extract the client's IP address and HTTP headers, integrate with an IP geolocation database or third-party API, and generate detailed network and device information. The application must intelligently adapt its output format (Plain Text or JSON) based on strict routing rules and be deployed on Google App Engine (GAE) to ensure high availability.



\---



\## 3. Functional Requirements



\*\*3.1 Protocol \& Request Support\*\*

\* \*\*Multi-Protocol Listening:\*\* Support access via both HTTP and HTTPS protocols.

\* \*\*Multi-Method Support:\*\* Support common HTTP request methods, primarily `GET` and `POST`.



\*\*3.2 Request Analysis \& Information Extraction\*\*

\* \*\*User-Agent Parsing:\*\* Analyze the `User-Agent` string to extract the operating system (type/version) and browser (type/version).

\* \*\*IP Profiling (Core):\*\* Integrate with an IP database (e.g., MaxMind GeoIP2) or an external API (e.g., IPinfo) to translate the retrieved IP address into specific geographical and Internet Service Provider (ISP) information.



\*\*3.3 Smart Content Negotiation \& Routing Hierarchy\*\*

The application must determine the response format using the following strict hierarchy to prevent routing conflicts:

1\. \*\*URL Path (Highest Priority):\*\* Any request to `/api/\*` (e.g., `/api/v1/trace`) MUST return JSON, regardless of headers.

2\. \*\*Accept Header (Secondary):\*\* If the path is neutral (e.g., the root `/`), check the `Accept` header. If it explicitly requests `application/json`, return JSON.

3\. \*\*Default Fallback:\*\* If the path is neutral and the `Accept` header is generic (e.g., `text/html` from a browser) or missing (e.g., a basic `curl` command), return human-readable, line-by-line Plain Text.



\---



\## 4. Data Specifications



\### 4.1 Core Data Fields \& Data Types

The system must return the following fields. 



\*\*Global Rule for Missing Data:\*\* If a specific field cannot be determined (e.g., a custom/missing User-Agent, or unknown ISP), the system MUST return `null` in JSON and the string `N/A` in Plain Text. Do not use empty strings (`""`) or omit the key.



\* \*\*ipv4:\*\* Client's IPv4 address (String, e.g., `"192.0.2.1"`)

\* \*\*ipv6:\*\* Client's IPv6 address (String, or `null`/`N/A` if not applicable)

\* \*\*Proxy Check:\*\* Proxy/VPN detection result (\*\*Boolean\*\* `true`/`false` for JSON; \*\*String\*\* `yes`/`no` for Plain Text)

\* \*\*Detected Proxy Country:\*\* Country code of the proxy server (String, e.g., `"US"`)

\* \*\*Proxy Type:\*\* Type of proxy (String, e.g., `"VPN"`, `"TOR"`, `"Web Proxy"`)

\* \*\*OS:\*\* Operating system and version (String, e.g., `"Windows 10"`)

\* \*\*browser:\*\* Browser and version (String, e.g., `"Firefox 80"`)

\* \*\*City:\*\* City location (String, e.g., `"Los Angeles"`)

\* \*\*State/Region:\*\* State/Province/Region (String, e.g., `"California"`)

\* \*\*Postal Code:\*\* ZIP/Postal code (String, e.g., `"90013"`)

\* \*\*Country:\*\* Full country name (String, e.g., `"United States of America"`)

\* \*\*ISP:\*\* Internet Service Provider (String, e.g., `"Hytron Network Services"`)

\* \*\*ASN:\*\* Autonomous System Number (String, e.g., `"153371"`)

\* \*\*Time Zone:\*\* Local time zone (String, e.g., `"UTC -08:00"`)



\### 4.2 Output Examples



\*\*Scenario A: Browser Access to Root `/` (Plain Text)\*\*

```text

ipv4: 198.51.100.1

ipv6: N/A

Proxy Check: yes

Detected Proxy Country: US

Proxy Type: VPN

OS: windows 10

browser: firefox 80

City: Los Angeles

State/Region: California

Postal Code: 90013

Country: United States of America

ISP: Hytron Network Services (US) LLC

ASN: 153371

Time Zone: UTC -08:00

```



\*\*Scenario B: API Call to `/api/v1/trace` (JSON)\*\*

```json

{

&#x20; "ipv4": "198.51.100.1",

&#x20; "ipv6": null,

&#x20; "proxy\_check": true,

&#x20; "detected\_proxy\_country": "US",

&#x20; "proxy\_type": "VPN",

&#x20; "os": "windows 10",

&#x20; "browser": "firefox 80",

&#x20; "city": "Los Angeles",

&#x20; "state\_region": "California",

&#x20; "postal\_code": "90013",

&#x20; "country": "United States of America",

&#x20; "isp": "Hytron Network Services (US) LLC",

&#x20; "asn": "153371",

&#x20; "time\_zone": "UTC -08:00"

}

```



\---



\## 5. Non-Functional Requirements



\* \*\*Performance SLA:\*\* The P95 (95th percentile) processing latency must be \*\*<50ms\*\*, excluding network transit time. If a third-party API is used for IP lookups, a robust local caching mechanism (e.g., Redis or in-process LRU Cache) must be implemented to achieve this SLA.

\* \*\*Scalability:\*\* The system architecture must be designed as stateless.

\* \*\*Security:\*\* Filter and sanitize all Header data retrieved from the client to prevent XSS or log injection attacks.



\---



\## 6. Deployment \& Architecture



\*\*6.1 Runtime Environment\*\*

\* \*\*Platform:\*\* Google App Engine (GAE) - Standard Environment.

\* \*\*Language:\*\* Python 3.9+

\* \*\*Recommended Framework:\*\* FastAPI (highly recommended for modern APIs with automatic JSON serialization and schema validation).



\*\*6.2 Practical Considerations (Data Sources)\*\*

The team must either mount offline IP/VPN databases (like MaxMind GeoIP2) into GAE or connect to commercial data sources like IPinfo.io. 



\---



\## 7. Error Handling \& Edge Cases



\*\*7.1 Error Response Specifications\*\*

\* \*\*JSON Format:\*\* Return the appropriate HTTP status code (e.g., 400, 500) and this structure:

&#x20;   ```json

&#x20;   {

&#x20;     "status": "error",

&#x20;     "error\_code": "ERROR\_CODE\_STRING",

&#x20;     "message": "Detailed error message."

&#x20;   }

&#x20;   ```

\* \*\*Plain Text Format:\*\* Return text prefixed with `Error:`, e.g., `Error: \[ERROR\_CODE\_STRING] Detailed message.`



\*\*7.2 Core Edge Cases\*\*

1\.  \*\*Invalid or Private IP:\*\* If the request lacks a valid IP, or the extracted IP is a local/reserved address (e.g., `127.0.0.1`, `192.168.x.x`), return HTTP `400 Bad Request`. Geolocation fields must be `null`/`N/A`, with the error code `INVALID\_OR\_PRIVATE\_IP`.

2\.  \*\*Service Degradation:\*\* If the backend IP database fails or times out, the system \*\*must not crash\*\*. It must gracefully degrade by returning available header data (`ipv4`, `OS`, `browser`), setting failed geolocation fields to `null`/`N/A`, and appending an `X-Service-Warning: Partial Data` HTTP header.



\---



\## 8. Security, Compliance \& Defense



\*\*8.1 Anti-Spoofing (Header Defense)\*\*

Because malicious users can spoof headers like `X-Forwarded-For` to fake their real IP, and because deployment is strictly on GAE, the application \*\*MUST ONLY trust the `X-Appengine-User-Ip` header\*\* provided by Google's infrastructure. 

\* \*Development Rule:\* Code parsing standard proxy headers (`X-Forwarded-For`, `X-Real-IP`) MUST NOT be implemented in this phase to maintain a zero-trust posture against spoofing.



\*\*8.2 Data Privacy (PII)\*\*

\* \*\*IP Anonymization:\*\* Provide an optional query parameter (`?anonymize=true`). When enabled, mask the last octet of IPv4 (e.g., `198.51.100.0`) and truncate IPv6.

\* \*\*Stateless Operation:\*\* The application must not persistently store visitor IPs mapped to User-Agents. All processing must be discarded immediately.



\*\*8.3 Rate Limiting \& NAT Considerations\*\*

\* Rate limiting must evaluate the extracted real client IP (`X-Appengine-User-Ip`).

\* To prevent mass-blocking of legitimate traffic from corporate offices or universities sharing a single NAT public IP, implement a token-bucket algorithm or set a generous baseline limit (e.g., \*\*300 requests per minute per IP\*\*).

\* When triggered, return HTTP `429 Too Many Requests` with a `Retry-After` header.



\---



\## 9. API Design \& Observability



\*\*9.1 Health Check\*\*

\* A `/health` endpoint must be provided (returning HTTP 200 and `{"status": "healthy"}`). This must verify that the underlying IP database is responsive.



\*\*9.2 Delivery Testing Requirements\*\*

\* \*\*User-Agent Parsing Tests:\*\* Must include assertions for common browsers, obscure mobile devices, missing headers, and web crawlers (e.g., Googlebot).

\* \*\*Degradation Tests:\*\* Must artificially fail the IP database connection and assert that the API gracefully returns HTTP 200 with partial header data rather than a 500 Server Error.



\---



\## 10. Operational \& Lifecycle Requirements



\*\*10.1 Data Freshness \& Maintenance\*\*

\* \*\*Automated Updates:\*\* If the system relies on an offline/local IP database (e.g., MaxMind GeoIP2), IP allocations and VPN nodes will become stale over time. The system must include a scheduled automated job (e.g., via GCP Cloud Scheduler trigger) to pull, verify, and hot-reload the latest database file at least once a week without requiring application downtime or manual intervention.



\*\*10.2 Interactive API Documentation\*\*

\* \*\*Auto-Generated UI:\*\* To facilitate easy integration for frontend developers and third-party clients, the application must expose an interactive API documentation endpoint (e.g., Swagger UI / OpenAPI at the `/docs` route). 

\* \*Framework Note:\* If using FastAPI, this is generated automatically but must be explicitly configured to accurately reflect the request/response schemas defined in Section 4.



\*\*10.3 Safe Application Logging\*\*

\* While Section 8.2 mandates "Zero Logging" of PII to ensure privacy compliance, developers still need logs to troubleshoot system failures.

\* \*\*Scrubbed Logging:\*\* The application must log startup events, application crashes, stack traces, and 500-level HTTP errors to GCP Cloud Logging. However, the system must aggressively scrub or mask the specific client IP string from these logs before writing them to disk.



\*\*10.4 Cost Controls \& Quota Management\*\*

\* \*\*Auto-Scaling Limits:\*\* Google App Engine scales automatically based on traffic. To prevent runaway infrastructure costs during a massive traffic spike or DDoS attempt, the `app.yaml` configuration must explicitly define a `max\_instances` limit.

\* \*\*Budget Alerts:\*\* The DevOps/infrastructure team must configure GCP Budget Alerts to notify stakeholders immediately if daily spend exceeds a predefined threshold.

