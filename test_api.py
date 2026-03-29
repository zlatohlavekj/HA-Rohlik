#!/usr/bin/env python3
"""
test_api.py – Rohlik.cz API verifikační skript v1.2
=====================================================
Tento skript ověří, zda Rohlik.cz API funguje tak, jak očekáváme.
Spusť ho PŘED implementací integrace a výsledky pošli zpět.

Použití:
    python3 test_api.py

Vyžaduje:
    pip install requests

Co skript testuje:
    1. Přihlášení (zjistí formát autentizace)
    2. Vyhledávání produktu
    3. Zobrazení košíku
    4. Přidání položky do košíku (volitelné – viz PŘIDAT_DO_KOŠÍKU níže)
"""

import json
import sys
import time
import requests  # pip install requests

# ============================================================
# NASTAVENÍ – vyplň před spuštěním
# ============================================================

EMAIL = "tvůj@email.cz"       # <- Doplň svůj Rohlik email
HESLO = "tvojeHeslo"          # <- Doplň své heslo
HLEDANY_PRODUKT = "mléko"     # <- Co chceš vyhledat

# Chceš otestovat i přidání do košíku?
# POZOR: Toto skutečně přidá položku do tvého košíku!
# Nastav na True jen pokud to chceš otestovat.
PŘIDAT_DO_KOŠÍKU = False

# ============================================================
# Pomocné funkce pro výpis výsledků
# ============================================================

def ok(zprava):
    print(f"  ✅ {zprava}")

def chyba(zprava):
    print(f"  ❌ {zprava}")

def info(zprava):
    print(f"  ℹ️  {zprava}")

def sekce(nazev):
    print(f"\n{'='*50}")
    print(f"  TEST: {nazev}")
    print(f"{'='*50}")

def ukazat_response(response, zkratit=False):
    """Ukáže HTTP response – hlavičky i plné tělo."""
    info(f"Status: {response.status_code}")
    info(f"URL: {response.url}")

    # Všechny zajímavé hlavičky
    zajimave_hlavicky = [
        "content-type", "set-cookie", "x-auth-token",
        "authorization", "x-session-id", "x-token",
        "www-authenticate", "x-error", "x-request-id"
    ]
    for h in zajimave_hlavicky:
        if h.lower() in {k.lower() for k in response.headers}:
            # case-insensitive hledání
            for k, v in response.headers.items():
                if k.lower() == h.lower():
                    info(f"Header {k}: {v[:200]}")

    # Tělo odpovědi – vždy plné, bez zkrácení
    try:
        data = response.json()
        text = json.dumps(data, ensure_ascii=False, indent=2)
        if zkratit and len(text) > 3000:
            text = text[:3000] + "\n  ... (zkráceno na 3000 znaků)"
        info(f"Response body:\n{text}")
    except Exception:
        info(f"Response text: {response.text}")

def ukazat_cookies(session):
    """Zobrazí všechny cookies v session."""
    cookies = dict(session.cookies)
    if cookies:
        info(f"Session cookies: {json.dumps(cookies, indent=2)}")
    else:
        info("Session cookies: žádné!")

# ============================================================
# Hlavní testovací funkce
# ============================================================

def test_prihlaseni(session):
    """
    TEST 1: Přihlášení
    Cíl: Zjistit jak funguje autentizace (Bearer token vs. cookie vs. jiné)
    """
    sekce("Přihlášení")

    # Zkusíme endpointy od nejvíce pravděpodobných
    kandidati = [
        "https://www.rohlik.cz/services/frontend-service/login",
        "https://www.rohlik.cz/api/v1/login",
        "https://www.rohlik.cz/api/v1/auth/login",
        "https://www.rohlik.cz/api/v2/login",
    ]

    payload = {"email": EMAIL, "password": HESLO}

    for url in kandidati:
        info(f"Zkouším POST {url}")
        try:
            response = session.post(url, json=payload, timeout=10)
            info(f"  Status: {response.status_code}")

            if response.status_code == 200:
                ok(f"Přihlášení úspěšné! Endpoint: {url}")
                # Zobrazíme PLNOU odpověď (bez zkrácení) – hledáme token
                ukazat_response(response, zkratit=False)
                ukazat_cookies(session)

                # Pokusíme se najít token v odpovědi
                try:
                    data = response.json()
                    d = data.get("data") or data
                    token = (
                        d.get("token") or d.get("accessToken") or
                        d.get("access_token") or d.get("authToken") or
                        data.get("token") or data.get("accessToken")
                    )
                    if token:
                        ok(f"Token nalezen v odpovědi: {str(token)[:50]}...")
                        return token
                    else:
                        info("Token v JSON odpovědi nenalezen – autentizace zřejmě přes cookie")
                        return "cookie_based"
                except Exception as e:
                    info(f"Chyba při parsování odpovědi: {e}")
                    return "cookie_based"

        except requests.exceptions.Timeout:
            chyba(f"Timeout na {url}")
        except requests.exceptions.ConnectionError as e:
            chyba(f"Chyba připojení na {url}: {e}")

    chyba("Přihlášení selhalo na všech endpointech")
    return None


def test_vyhledavani(session, token=None):
    """
    TEST 2: Vyhledávání produktů
    Cíl: Ověřit search endpoint a formát odpovědi
    """
    sekce(f"Vyhledávání: '{HLEDANY_PRODUKT}'")

    # Pokud máme Bearer token, přidáme ho
    if token and token != "cookie_based":
        session.headers.update({"Authorization": f"Bearer {token}"})
        info(f"Používám Bearer token: {str(token)[:30]}...")
    else:
        info("Používám cookie autentizaci (žádný Bearer token)")

    info(f"Aktuální cookies: {dict(session.cookies)}")

    # Endpointy – services/frontend-service má prioritu (tam funguje login)
    endpointy = [
        f"https://www.rohlik.cz/services/frontend-service/v2/products?productName={HLEDANY_PRODUKT}&limit=10",
        f"https://www.rohlik.cz/services/frontend-service/v2/products?query={HLEDANY_PRODUKT}&limit=10",
        f"https://www.rohlik.cz/services/frontend-service/v1/products?name={HLEDANY_PRODUKT}",
        f"https://www.rohlik.cz/services/frontend-service/v2/products/search?q={HLEDANY_PRODUKT}",
        f"https://www.rohlik.cz/api/v1/products/search?query={HLEDANY_PRODUKT}",
        f"https://www.rohlik.cz/api/v1/search?q={HLEDANY_PRODUKT}",
        f"https://www.rohlik.cz/api/v2/products?search={HLEDANY_PRODUKT}",
    ]

    for url in endpointy:
        info(f"Zkouším: GET {url}")
        try:
            response = session.get(url, timeout=10)
            info(f"  Status: {response.status_code}")

            # I u 401 chceme vidět odpověď – může říct co chybí
            if response.status_code in (401, 403):
                info("  Odpověď 401/403:")
                ukazat_response(response, zkratit=True)

            if response.status_code == 200:
                ok(f"Vyhledávání funguje! Endpoint: {url}")
                ukazat_response(response, zkratit=True)

                try:
                    data = response.json()
                    d = data.get("data") or data
                    produkty = (
                        d.get("results") or d.get("products") or
                        d.get("items") or data.get("results") or []
                    )
                    if isinstance(produkty, list) and produkty:
                        ok(f"Nalezeno {len(produkty)} produktů")
                        info(f"Struktura prvního produktu: {json.dumps(produkty[0], ensure_ascii=False)[:300]}")
                        return url, produkty
                except Exception as e:
                    info(f"Chyba při parsování výsledků: {e}")
                return url, []

        except Exception as e:
            info(f"  Chyba: {e}")

    chyba("Vyhledávání nefunguje na žádném z testovaných endpointů")
    return None, []


def test_kosik(session, token=None):
    """
    TEST 3: Zobrazení košíku
    Cíl: Ověřit cart endpoint a formát dat
    """
    sekce("Zobrazení košíku")

    endpointy = [
        # services/frontend-service má prioritu
        "https://www.rohlik.cz/services/frontend-service/v1/orders",
        "https://www.rohlik.cz/services/frontend-service/v2/orders",
        "https://www.rohlik.cz/services/frontend-service/v1/cart",
        "https://www.rohlik.cz/services/frontend-service/v2/cart",
        # api/ endpointy
        "https://www.rohlik.cz/api/v1/cart",
        "https://www.rohlik.cz/api/v2/cart",
    ]

    for url in endpointy:
        info(f"Zkouším: GET {url}")
        try:
            response = session.get(url, timeout=10)
            info(f"  Status: {response.status_code}")

            if response.status_code in (401, 403):
                info("  Odpověď 401/403:")
                ukazat_response(response, zkratit=True)

            if response.status_code == 200:
                ok(f"Košík endpoint funguje! URL: {url}")
                ukazat_response(response, zkratit=True)
                return url

        except Exception as e:
            info(f"  Chyba: {e}")

    chyba("Žádný cart endpoint nefunguje")
    return None


def test_pridat_do_kosiku(session, produkt_id, cart_url, token=None):
    """
    TEST 4: Přidání do košíku (volitelné)
    POZOR: Skutečně přidá položku do košíku!
    """
    sekce(f"Přidání do košíku (produkt ID: {produkt_id})")
    info("POZOR: Toto skutečně přidá položku do tvého košíku!")
    time.sleep(2)

    base = "https://www.rohlik.cz/services/frontend-service"
    endpointy = [
        f"{base}/v1/orders",
        f"{base}/v2/orders",
        f"{base}/v1/cart/items",
        "https://www.rohlik.cz/api/v1/cart/items",
    ]

    payload = {"productId": produkt_id, "quantity": 1}

    for url in endpointy:
        info(f"Zkouším: POST {url} payload={payload}")
        try:
            response = session.post(url, json=payload, timeout=10)
            info(f"  Status: {response.status_code}")
            ukazat_response(response, zkratit=True)

            if response.status_code in (200, 201):
                ok("Přidání do košíku úspěšné!")
                return True
        except Exception as e:
            info(f"  Chyba: {e}")

    chyba("Přidání do košíku selhalo")
    return False


# ============================================================
# Hlavní program
# ============================================================

def main():
    print("\n" + "="*50)
    print("  Rohlik.cz API Test Script v1.2")
    print("  Projekt: HA-Rohlik")
    print("="*50)

    if EMAIL == "tvůj@email.cz" or HESLO == "tvojeHeslo":
        print("\n❌ CHYBA: Vyplň EMAIL a HESLO na začátku souboru!")
        sys.exit(1)

    # HTTP session – sdílí cookies automaticky mezi requesty
    session = requests.Session()
    session.headers.update({
        # Napodobíme prohlížeč – Rohlik může blokovat non-browser requesty
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.8",
        "Content-Type": "application/json",
        "Origin": "https://www.rohlik.cz",
        "Referer": "https://www.rohlik.cz/",
        "X-Requested-With": "XMLHttpRequest",
    })

    výsledky = {}

    # TEST 1: Přihlášení
    token = test_prihlaseni(session)
    výsledky["přihlášení"] = "OK" if token else "FAILED"

    if not token:
        print("\n❌ Přihlášení selhalo – nelze pokračovat.")
        vypsat_souhrn(výsledky)
        sys.exit(1)

    # TEST 2: Vyhledávání
    search_url, produkty = test_vyhledavani(session, token)
    výsledky["vyhledávání"] = "OK" if search_url else "FAILED"

    # TEST 3: Košík
    cart_url = test_kosik(session, token)
    výsledky["košík"] = "OK" if cart_url else "FAILED"

    # TEST 4: Přidání do košíku (jen pokud povoleno)
    if PŘIDAT_DO_KOŠÍKU and produkty:
        prvni_id = produkty[0].get("id") or produkty[0].get("productId")
        if prvni_id:
            uspech = test_pridat_do_kosiku(session, prvni_id, cart_url, token)
            výsledky["přidání do košíku"] = "OK" if uspech else "FAILED"
        else:
            výsledky["přidání do košíku"] = "SKIPPED (no product ID)"
    elif not PŘIDAT_DO_KOŠÍKU:
        výsledky["přidání do košíku"] = "SKIPPED (disabled)"

    vypsat_souhrn(výsledky)


def vypsat_souhrn(výsledky):
    print("\n" + "="*50)
    print("  SOUHRN VÝSLEDKŮ")
    print("="*50)
    for test, výsledek in výsledky.items():
        emoji = "✅" if "OK" in výsledek else ("⏭️" if "SKIP" in výsledek else "❌")
        print(f"  {emoji}  {test:30s} {výsledek}")
    print("="*50)
    print("\n📋 Zkopíruj tento výstup a pošli ho zpět do Claude Code.")


if __name__ == "__main__":
    main()

Tento skript ověří, zda Rohlik.cz API funguje tak, jak očekáváme.
Spusť ho PŘED implementací integrace a výsledky pošli zpět.

Použití:
    python3 test_api.py

Vyžaduje:
    pip install requests

Co skript testuje:
    1. Přihlášení (zjistí formát autentizace)
    2. Vyhledávání produktu
    3. Zobrazení košíku
    4. Přidání položky do košíku (volitelné – viz PŘIDAT_DO_KOŠÍKU níže)
"""

import json
import sys
import time
import requests  # pip install requests

# ============================================================
# NASTAVENÍ – vyplň před spuštěním
# ============================================================

EMAIL = "tvůj@email.cz"       # <- Doplň svůj Rohlik email
HESLO = "tvojeHeslo"          # <- Doplň své heslo
HLEDANY_PRODUKT = "mléko"     # <- Co chceš vyhledat

# Chceš otestovat i přidání do košíku?
# POZOR: Toto skutečně přidá položku do tvého košíku!
# Nastav na True jen pokud to chceš otestovat.
PŘIDAT_DO_KOŠÍKU = False

# ============================================================
# Pomocné funkce pro výpis výsledků
# ============================================================

def ok(zprava):
    """Vytiskne zelenou zprávu o úspěchu."""
    print(f"  ✅ {zprava}")

def chyba(zprava):
    """Vytiskne červenou chybovou zprávu."""
    print(f"  ❌ {zprava}")

def info(zprava):
    """Vytiskne informační zprávu."""
    print(f"  ℹ️  {zprava}")

def sekce(nazev):
    """Vytiskne nadpis sekce."""
    print(f"\n{'='*50}")
    print(f"  TEST: {nazev}")
    print(f"{'='*50}")

def ukazat_response(response, max_delka=500):
    """Ukáže HTTP response včetně hlaviček a těla."""
    info(f"Status: {response.status_code}")
    info(f"URL: {response.url}")

    # Zajímavé hlavičky
    zajimave_hlavicky = ["content-type", "set-cookie", "x-auth-token",
                          "authorization", "x-session-id"]
    for h in zajimave_hlavicky:
        if h in response.headers:
            info(f"Header {h}: {response.headers[h][:100]}")

    # Tělo odpovědi
    try:
        data = response.json()
        text = json.dumps(data, ensure_ascii=False, indent=2)
        if len(text) > max_delka:
            text = text[:max_delka] + "\n  ... (zkráceno)"
        info(f"Response body:\n{text}")
    except Exception:
        info(f"Response text: {response.text[:max_delka]}")

# ============================================================
# Hlavní testovací funkce
# ============================================================

def test_prihlaseni(session):
    """
    TEST 1: Přihlášení
    Cíl: Zjistit jak funguje autentizace (Bearer token vs. cookie)
    """
    sekce("Přihlášení")

    # Zkusíme nejprve JSON login endpoint
    url = "https://www.rohlik.cz/api/v1/login"
    payload = {
        "email": EMAIL,
        "password": HESLO
    }

    info(f"Zkouším POST {url}")
    info(f"Payload: {{email: '{EMAIL}', password: '***'}}")

    try:
        response = session.post(url, json=payload, timeout=10)
        ukazat_response(response)

        if response.status_code == 200:
            ok("Přihlášení úspěšné!")
            data = response.json()

            # Hledáme token v různých místech
            token = (
                data.get("token") or
                data.get("accessToken") or
                data.get("access_token") or
                data.get("data", {}).get("token") if isinstance(data.get("data"), dict) else None
            )

            if token:
                ok(f"Token nalezen: {token[:30]}...")
                return token
            else:
                info("Token nebyl v JSON odpovědi – možná používá session cookie")
                info(f"Cookies po přihlášení: {dict(session.cookies)}")
                return "cookie_based"

        elif response.status_code == 404:
            chyba(f"Endpoint {url} neexistuje – zkusím alternativy")
            return test_prihlaseni_alternativy(session)

        else:
            chyba(f"Přihlášení selhalo: HTTP {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        chyba("Timeout – server neodpovídá")
        return None
    except requests.exceptions.ConnectionError as e:
        chyba(f"Chyba připojení: {e}")
        return None


def test_prihlaseni_alternativy(session):
    """Zkouší alternativní přihlašovací endpointy."""
    alternativy = [
        ("POST", "https://www.rohlik.cz/api/v1/auth/login"),
        ("POST", "https://www.rohlik.cz/api/v2/login"),
        ("POST", "https://www.rohlik.cz/services/frontend-service/login"),
    ]

    for metoda, url in alternativy:
        info(f"Zkouším alternativu: {metoda} {url}")
        try:
            response = session.post(url, json={
                "email": EMAIL,
                "password": HESLO
            }, timeout=10)
            info(f"  Status: {response.status_code}")
            if response.status_code == 200:
                ok(f"Funguje! Endpoint: {url}")
                ukazat_response(response, max_delka=2000)
                # Zobrazit cookies pro debug
                info(f"Cookies po přihlášení: {dict(session.cookies)}")
                # Vrátíme "cookie_based" – autentizace probíhá přes PHPSESSION cookie,
                # nikoliv přes Bearer token. Session objekt si cookies pamatuje automaticky.
                return "cookie_based"
        except Exception as e:
            info(f"  Chyba: {e}")

    chyba("Žádná alternativa nefunguje")
    return None


def test_vyhledavani(session, token=None):
    """
    TEST 2: Vyhledávání produktů
    Cíl: Ověřit search endpoint a formát odpovědi
    """
    sekce(f"Vyhledávání: '{HLEDANY_PRODUKT}'")

    # Nastavit auth hlavičku pokud máme token
    if token and token != "cookie_based":
        session.headers.update({"Authorization": f"Bearer {token}"})

    # Zkusit různé search endpointy
    # Priorita: services/frontend-service (tam funguje login) → api/v1 → api/v2
    endpointy = [
        f"https://www.rohlik.cz/services/frontend-service/v2/products?productName={HLEDANY_PRODUKT}&limit=10",
        f"https://www.rohlik.cz/services/frontend-service/v2/products?query={HLEDANY_PRODUKT}&limit=10",
        f"https://www.rohlik.cz/services/frontend-service/v2/products/search?q={HLEDANY_PRODUKT}",
        f"https://www.rohlik.cz/services/frontend-service/v1/products?name={HLEDANY_PRODUKT}",
        f"https://www.rohlik.cz/api/v1/products/search?query={HLEDANY_PRODUKT}",
        f"https://www.rohlik.cz/api/v1/search?q={HLEDANY_PRODUKT}",
        f"https://www.rohlik.cz/api/v2/products?search={HLEDANY_PRODUKT}",
    ]

    for url in endpointy:
        info(f"Zkouším: GET {url}")
        try:
            response = session.get(url, timeout=10)
            info(f"  Status: {response.status_code}")

            if response.status_code == 200:
                ok(f"Vyhledávání funguje! Endpoint: {url}")
                ukazat_response(response, max_delka=1000)

                # Pokusíme se přečíst výsledky
                try:
                    data = response.json()
                    # Hledat pole s produkty v různých strukturách
                    produkty = (
                        data.get("results") or
                        data.get("products") or
                        data.get("items") or
                        data.get("data", {}).get("products") if isinstance(data.get("data"), dict) else None or
                        []
                    )
                    if produkty:
                        ok(f"Nalezeno {len(produkty)} produktů")
                        info(f"První produkt: {json.dumps(produkty[0], ensure_ascii=False)[:200]}")
                        return url, produkty
                except Exception:
                    pass

        except Exception as e:
            info(f"  Chyba: {e}")

    chyba("Vyhledávání nefunguje na žádném z testovaných endpointů")
    return None, []


def test_kosik(session, token=None):
    """
    TEST 3: Zobrazení košíku
    Cíl: Ověřit cart endpoint a formát dat
    """
    sekce("Zobrazení košíku")

    endpointy = [
        # services/frontend-service (priorita – tam funguje login)
        "https://www.rohlik.cz/services/frontend-service/v1/orders",
        "https://www.rohlik.cz/services/frontend-service/v2/orders",
        "https://www.rohlik.cz/services/frontend-service/v1/cart",
        "https://www.rohlik.cz/services/frontend-service/v2/cart",
        # api/ endpointy
        "https://www.rohlik.cz/api/v1/cart",
        "https://www.rohlik.cz/api/v2/cart",
    ]

    for url in endpointy:
        info(f"Zkouším: GET {url}")
        try:
            response = session.get(url, timeout=10)
            info(f"  Status: {response.status_code}")

            if response.status_code == 200:
                ok(f"Košík endpoint funguje! URL: {url}")
                ukazat_response(response, max_delka=800)
                return url
        except Exception as e:
            info(f"  Chyba: {e}")

    chyba("Žádný cart endpoint nefunguje")
    return None


def test_pridat_do_kosiku(session, produkt_id, cart_url, token=None):
    """
    TEST 4: Přidání do košíku (volitelné)
    POZOR: Skutečně přidá položku do košíku!
    """
    sekce(f"Přidání do košíku (produkt ID: {produkt_id})")
    info("POZOR: Toto skutečně přidá položku do tvého košíku!")
    time.sleep(2)  # Krátká pauza – dáváme čas přečíst upozornění

    # Odhadnutý POST endpoint
    base = cart_url.replace("/cart", "") if cart_url else "https://www.rohlik.cz/api/v1"
    endpointy = [
        f"{base}/cart/items",
        f"{base}/cart",
        "https://www.rohlik.cz/api/v1/cart/items",
    ]

    payload = {
        "productId": produkt_id,
        "quantity": 1
    }

    for url in endpointy:
        info(f"Zkouším: POST {url}")
        info(f"Payload: {payload}")
        try:
            response = session.post(url, json=payload, timeout=10)
            info(f"  Status: {response.status_code}")
            ukazat_response(response, max_delka=500)

            if response.status_code in (200, 201):
                ok("Přidání do košíku úspěšné!")
                return True
        except Exception as e:
            info(f"  Chyba: {e}")

    chyba("Přidání do košíku selhalo")
    return False


# ============================================================
# Hlavní program
# ============================================================

def main():
    print("\n" + "="*50)
    print("  Rohlik.cz API Test Script")
    print("  Verze: 1.0 | Projekt: HA-Rohlik")
    print("="*50)

    # Ověříme, že uživatel vyplnil credentials
    if EMAIL == "tvůj@email.cz" or HESLO == "tvojeHeslo":
        print("\n❌ CHYBA: Vyplň EMAIL a HESLO na začátku souboru!")
        print("   Otevři test_api.py a uprav proměnné EMAIL a HESLO.")
        sys.exit(1)

    # Vytvoříme HTTP session (sdílí cookies mezi requesty)
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; HA-Rohlik-test/1.0)",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })

    výsledky = {}

    # TEST 1: Přihlášení
    token = test_prihlaseni(session)
    výsledky["přihlášení"] = "OK" if token else "FAILED"

    if not token:
        print("\n❌ Přihlášení selhalo – nelze pokračovat dalšími testy.")
        vypsat_souhrn(výsledky)
        sys.exit(1)

    # TEST 2: Vyhledávání
    search_url, produkty = test_vyhledavani(session, token)
    výsledky["vyhledávání"] = "OK" if search_url else "FAILED"

    # TEST 3: Košík
    cart_url = test_kosik(session, token)
    výsledky["košík"] = "OK" if cart_url else "FAILED"

    # TEST 4: Přidání do košíku (jen pokud povoleno)
    if PŘIDAT_DO_KOŠÍKU and produkty:
        prvni_produkt_id = produkty[0].get("id") or produkty[0].get("productId")
        if prvni_produkt_id:
            uspech = test_pridat_do_kosiku(session, prvni_produkt_id, cart_url, token)
            výsledky["přidání do košíku"] = "OK" if uspech else "FAILED"
        else:
            info("Nelze získat ID prvního produktu pro test přidání")
            výsledky["přidání do košíku"] = "SKIPPED (no product ID)"
    elif not PŘIDAT_DO_KOŠÍKU:
        výsledky["přidání do košíku"] = "SKIPPED (disabled)"

    # Souhrn
    vypsat_souhrn(výsledky)


def vypsat_souhrn(výsledky):
    """Vytiskne přehledný souhrn všech testů."""
    print("\n" + "="*50)
    print("  SOUHRN VÝSLEDKŮ")
    print("="*50)
    for test, výsledek in výsledky.items():
        emoji = "✅" if "OK" in výsledek else ("⏭️" if "SKIP" in výsledek else "❌")
        print(f"  {emoji}  {test:30s} {výsledek}")
    print("="*50)
    print("\n📋 Zkopíruj tento výstup a pošli ho zpět do Claude Code.")
    print("   Na základě výsledků aktualizujeme SPEC.md sekci 6 (API Documentation).")


if __name__ == "__main__":
    main()
