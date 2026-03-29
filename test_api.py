#!/usr/bin/env python3
"""
test_api.py v1.2 - Rohlik.cz API verifika\u010dn\u00ed skript
=======================================================
Spus\u0165: python3 test_api.py
Vy\u017eaduje: pip install requests
"""

import json
import sys
import time
import requests

# ============================================================
# NASTAVEN\u00cd - vyplni\u0020p\u0159ed spust\u011bn\u00edm
# ============================================================

EMAIL = "tv\u016fj@email.cz"
HESLO = "tvojeHeslo"
HLEDANY_PRODUKT = "ml\u00e9ko"

# POZOR: nastav na True jen pokud chce\u0161 skute\u010dn\u011b p\u0159idat do ko\u0161\u00edku!
PRIDAT_DO_KOSIKU = False

# ============================================================
# Pomocn\u00e9 funkce
# ============================================================

def ok(zprava):
    print(f"  \u2705 {zprava}")

def chyba(zprava):
    print(f"  \u274c {zprava}")

def info(zprava):
    print(f"  \u2139\ufe0f  {zprava}")

def sekce(nazev):
    print(f"\n{'='*50}")
    print(f"  TEST: {nazev}")
    print(f"{'='*50}")

def ukazat_response(response, zkratit=False):
    info(f"Status: {response.status_code}")
    info(f"URL: {response.url}")
    zajimave = ["content-type", "set-cookie", "x-auth-token",
                "www-authenticate", "x-error", "x-token"]
    for k, v in response.headers.items():
        if k.lower() in zajimave:
            info(f"Header {k}: {v[:200]}")
    try:
        data = response.json()
        text = json.dumps(data, ensure_ascii=False, indent=2)
        if zkratit and len(text) > 3000:
            text = text[:3000] + "\n  ... (zkraceno)"
        info(f"Response body:\n{text}")
    except Exception:
        info(f"Response text: {response.text[:2000]}")

def ukazat_cookies(session):
    cookies = dict(session.cookies)
    info(f"Session cookies: {json.dumps(cookies, ensure_ascii=False, indent=2)}")

# ============================================================
# Testy
# ============================================================

def test_prihlaseni(session):
    sekce("Prihlaseni")

    kandidati = [
        "https://www.rohlik.cz/services/frontend-service/login",
        "https://www.rohlik.cz/api/v1/login",
        "https://www.rohlik.cz/api/v1/auth/login",
        "https://www.rohlik.cz/api/v2/login",
    ]
    payload = {"email": EMAIL, "password": HESLO}

    for url in kandidati:
        info(f"Zkousim POST {url}")
        try:
            response = session.post(url, json=payload, timeout=10)
            info(f"  Status: {response.status_code}")
            if response.status_code == 200:
                ok(f"Prihlaseni uspesne! Endpoint: {url}")
                ukazat_response(response, zkratit=False)
                ukazat_cookies(session)
                try:
                    data = response.json()
                    d = data.get("data") or data
                    token = (d.get("token") or d.get("accessToken") or
                             d.get("access_token") or d.get("authToken") or
                             data.get("token"))
                    if token:
                        ok(f"Token nalezen: {str(token)[:50]}")
                        return token
                    else:
                        info("Token v odpovedi nenalezen - autentizace pres cookie")
                        return "cookie_based"
                except Exception as e:
                    info(f"Chyba parsovani: {e}")
                    return "cookie_based"
        except requests.exceptions.Timeout:
            chyba(f"Timeout: {url}")
        except requests.exceptions.ConnectionError as e:
            chyba(f"Chyba pripojeni: {e}")

    chyba("Prihlaseni selhalo na vsech endpointech")
    return None


def test_vyhledavani(session, token=None):
    sekce(f"Vyhledavani: '{HLEDANY_PRODUKT}'")

    if token and token != "cookie_based":
        session.headers.update({"Authorization": f"Bearer {token}"})
    else:
        info("Pouzivam cookie autentizaci")

    # storeId ziskame z login response (8799 je hodnota z tveho uctu)
    STORE_ID = 8799

    # Pouzivame params= misto string interpolace – requests automaticky URL-enkoduje
    # napr. "mléko" → "ml%C3%A9ko" (spravne zpracuje diakritiku)
    endpointy = [
        # api/v1/products/search vratil 400 (endpoint existuje!) – zkusime s ruznyma parametrama
        ("https://www.rohlik.cz/api/v1/products/search",
            {"query": HLEDANY_PRODUKT, "storeId": STORE_ID, "limit": 10}),
        ("https://www.rohlik.cz/api/v1/products/search",
            {"query": HLEDANY_PRODUKT, "limit": 10}),
        ("https://www.rohlik.cz/api/v1/products/search",
            {"name": HLEDANY_PRODUKT, "storeId": STORE_ID}),
        # frontend-service varianty
        ("https://www.rohlik.cz/services/frontend-service/v2/search",
            {"query": HLEDANY_PRODUKT, "storeId": STORE_ID}),
        ("https://www.rohlik.cz/services/frontend-service/v1/search",
            {"query": HLEDANY_PRODUKT}),
        ("https://www.rohlik.cz/services/frontend-service/v2/products",
            {"productName": HLEDANY_PRODUKT, "storeId": STORE_ID, "limit": 10}),
        ("https://www.rohlik.cz/services/frontend-service/v2/products",
            {"name": HLEDANY_PRODUKT, "storeId": STORE_ID, "limit": 10}),
    ]

    for url, params in endpointy:
        info(f"Zkousim: GET {url} params={params}")
        try:
            response = session.get(url, params=params, timeout=10)
            info(f"  Status: {response.status_code}")
            # Zobrazit telo i u 400/401/403 – server nam rekne co chybi
            if response.status_code in (400, 401, 403):
                info(f"  Odpoved {response.status_code} (co rika server):")
                ukazat_response(response, zkratit=True)
            if response.status_code == 200:
                ok(f"Vyhledavani funguje! Endpoint: {url} params={params}")
                ukazat_response(response, zkratit=True)
                try:
                    data = response.json()
                    d = data.get("data") or data
                    produkty = (d.get("results") or d.get("products") or
                                d.get("items") or data.get("results") or [])
                    if isinstance(produkty, list) and produkty:
                        ok(f"Nalezeno {len(produkty)} produktu")
                        info(f"Prvni produkt: {json.dumps(produkty[0], ensure_ascii=False)[:300]}")
                        return url, produkty
                except Exception as e:
                    info(f"Chyba parsovani: {e}")
                return url, []
        except Exception as e:
            info(f"  Chyba: {e}")

    chyba("Vyhledavani nefunguje")
    return None, []


def test_kosik(session, token=None):
    sekce("Zobrazeni kosiku")

    endpointy = [
        "https://www.rohlik.cz/services/frontend-service/v1/orders",
        "https://www.rohlik.cz/services/frontend-service/v2/orders",
        "https://www.rohlik.cz/services/frontend-service/v1/cart",
        "https://www.rohlik.cz/services/frontend-service/v2/cart",
        "https://www.rohlik.cz/api/v1/cart",
        "https://www.rohlik.cz/api/v2/cart",
    ]

    for url in endpointy:
        info(f"Zkousim: GET {url}")
        try:
            response = session.get(url, timeout=10)
            info(f"  Status: {response.status_code}")
            if response.status_code in (401, 403):
                info("  Odpoved 401/403:")
                ukazat_response(response, zkratit=True)
            if response.status_code == 200:
                ok(f"Kosik funguje! URL: {url}")
                ukazat_response(response, zkratit=True)
                return url
        except Exception as e:
            info(f"  Chyba: {e}")

    chyba("Zadny cart endpoint nefunguje")
    return None


def test_pridat_do_kosiku(session, produkt_id, cart_url):
    sekce(f"Pridani do kosiku (ID: {produkt_id})")
    info("POZOR: Toto skutecne prida polozku do tveho kosiku!")
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
        info(f"Zkousim: POST {url}")
        try:
            response = session.post(url, json=payload, timeout=10)
            info(f"  Status: {response.status_code}")
            ukazat_response(response, zkratit=True)
            if response.status_code in (200, 201):
                ok("Pridani uspesne!")
                return True
        except Exception as e:
            info(f"  Chyba: {e}")

    chyba("Pridani do kosiku selhalo")
    return False


# ============================================================
# Hlavni program
# ============================================================

def main():
    print("\n" + "="*50)
    print("  Rohlik.cz API Test Script v1.2")
    print("  Projekt: HA-Rohlik")
    print("="*50)

    if EMAIL == "tv\u016fj@email.cz" or HESLO == "tvojeHeslo":
        print("\n\u274c CHYBA: Vyplni EMAIL a HESLO na zacatku souboru!")
        sys.exit(1)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.8",
        "Content-Type": "application/json",
        "Origin": "https://www.rohlik.cz",
        "Referer": "https://www.rohlik.cz/",
        "X-Requested-With": "XMLHttpRequest",
    })

    vysledky = {}

    token = test_prihlaseni(session)
    vysledky["prihlaseni"] = "OK" if token else "FAILED"
    if not token:
        vypsat_souhrn(vysledky)
        sys.exit(1)

    search_url, produkty = test_vyhledavani(session, token)
    vysledky["vyhledavani"] = "OK" if search_url else "FAILED"

    cart_url = test_kosik(session, token)
    vysledky["kosik"] = "OK" if cart_url else "FAILED"

    if PRIDAT_DO_KOSIKU and produkty:
        prvni_id = produkty[0].get("id") or produkty[0].get("productId")
        if prvni_id:
            uspech = test_pridat_do_kosiku(session, prvni_id, cart_url)
            vysledky["pridani do kosiku"] = "OK" if uspech else "FAILED"
        else:
            vysledky["pridani do kosiku"] = "SKIPPED (no product ID)"
    else:
        vysledky["pridani do kosiku"] = "SKIPPED (disabled)"

    vypsat_souhrn(vysledky)


def vypsat_souhrn(vysledky):
    print("\n" + "="*50)
    print("  SOUHRN VYSLEDKU")
    print("="*50)
    for test, vysledek in vysledky.items():
        emoji = "\u2705" if "OK" in vysledek else ("\u23ed\ufe0f" if "SKIP" in vysledek else "\u274c")
        print(f"  {emoji}  {test:30s} {vysledek}")
    print("="*50)
    print("\n Zkopiruj tento vystup a posli ho zpet do Claude Code.")


if __name__ == "__main__":
    main()
