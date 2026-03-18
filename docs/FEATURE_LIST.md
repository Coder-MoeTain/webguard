# WebGuard RF - Feature List with Descriptions

## SQL Injection Features

| Feature | Type | Description |
|---------|------|-------------|
| has_select | bool | Payload contains SELECT keyword (case-insensitive) |
| has_union | bool | Payload contains UNION keyword |
| has_sleep | bool | Payload contains SLEEP, BENCHMARK, or WAITFOR |
| has_or_1_equals_1 | bool | Pattern "or 1=1", "or 1 = 1", etc. |
| has_drop | bool | Payload contains DROP keyword |
| has_insert | bool | Payload contains INSERT keyword |
| has_delete | bool | Payload contains DELETE keyword |
| has_update | bool | Payload contains UPDATE keyword |
| has_information_schema | bool | Payload references information_schema |
| quote_count | int | Count of single and double quotes |
| comment_marker_count | int | Count of --, #, /*, */ |
| semicolon_count | int | Count of semicolons |
| equals_count | int | Count of = characters |
| parentheses_count | int | Count of ( and ) |
| keyword_density | float | Ratio of SQL keywords to total length |
| sqli_entropy | float | Shannon entropy of payload |

## XSS Features

| Feature | Type | Description |
|---------|------|-------------|
| has_script_tag | bool | Payload contains <script> |
| has_javascript_protocol | bool | Payload contains javascript: |
| has_onerror | bool | Payload contains onerror= |
| has_onload | bool | Payload contains onload= |
| has_alert | bool | Payload contains alert( |
| has_document_write | bool | Payload contains document.write |
| has_eval | bool | Payload contains eval( |
| html_tag_count | int | Count of HTML tags |
| angle_bracket_count | int | Count of < and > |
| encoded_js_pattern | bool | Base64/hex encoded JS patterns |
| suspicious_dom_keywords | int | Count of DOM manipulation keywords |
| svg_script_count | int | SVG with script elements |

## CSRF Features

| Feature | Type | Description |
|---------|------|-------------|
| missing_csrf_token | bool | No csrf/token/X-CSRF in request |
| invalid_csrf_token | bool | Token present but invalid format |
| cross_origin_flag | bool | Origin differs from target |
| missing_referer | bool | No Referer header |
| state_change_request | bool | POST/PUT/DELETE without validation |
| suspicious_cookie_usage | bool | Cookie without SameSite |
| same_site_violation | bool | Cross-site request indicators |

## Common/Contextual Features

| Feature | Type | Description |
|---------|------|-------------|
| request_method_get | bool | One-hot: GET |
| request_method_post | bool | One-hot: POST |
| payload_length | int | Character count of payload |
| url_length | int | URL length |
| number_count | int | Count of digits |
| special_char_ratio | float | Non-alphanumeric ratio |
| encoded_char_ratio | float | % and hex encoded ratio |
| whitespace_ratio | float | Whitespace to total ratio |
| status_code | int | HTTP response status (hybrid) |
| response_length | int | Response body length (hybrid) |
| response_time | float | Response time ms (hybrid) |
| has_cookies | bool | Cookies present |
| has_referer | bool | Referer header present |

## Feature Groups

- **payload_only**: All payload-based features (SQLi, XSS, CSRF payload, common payload)
- **response_only**: status_code, response_length, response_time, error_flags
- **hybrid**: payload_only + response_only
