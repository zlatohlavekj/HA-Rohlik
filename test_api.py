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
    info("Pouzivam cookie autentizaci (PHPSESSION)")

    # Spravny endpoint zjisteny z existujici HA integrace dvejsada/HA-RohlikCZ
    url = "https://www.rohlik.cz/services/frontend-service/search-metadata"
    params = {
        "search": HLEDANY_PRODUKT,
        "offset": 0,
        "limit": 15,
        "companyId": 1,
        "canCorrect": "true",
    }

    info(f"Zkousim: GET {url}")
    info(f"  Params: {params}")
    try:
        response = session.get(url, params=params, timeout=10)
        info(f"  Status: {response.status_code}")

        if response.status_code in (400, 401, 403, 404):
            info(f"  Odpoved {response.status_code}:")
            ukazat_response(response, zkratit=True)
            return None, []

        if response.status_code == 200:
            ok(f"Vyhledavani funguje!")
            ukazat_response(response, zkratit=True)
            try:
                data = response.json()
                d = data.get("data") or data
                # Spravna cesta k produktum: data.productList
                produkty = d.get("productList") or d.get("products") or []
                if isinstance(produkty, list) and produkty:
                    ok(f"Nalezeno {len(produkty)} produktu")
                    info(f"Prvni produkt: {json.dumps(produkty[0], ensure_ascii=False)[:400]}")
                    return url, produkty
                else:
                    info(f"Odpoved 200 ale produkty nenalezeny. Klice v data: {list(d.keys()) if isinstance(d, dict) else type(d)}")
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

    # Spravny endpoint a payload zjisteny z dvejsada/HA-RohlikCZ
    url = "https://www.rohlik.cz/services/frontend-service/v2/cart"
    payload = {
        "actionId": None,
        "productId": produkt_id,
        "quantity": 1,
        "recipeId": None,
        "source": "true:Shopping Lists",
    }

    info(f"POST {url}")
    info(f"  Payload: {payload}")
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
# TEST 5: Header autentizace (rhl-email + rhl-pass)
# ============================================================

def test_header_auth():
    """
    TEST 5: Autentizace pres rhl-email / rhl-pass hlavicky
    -------------------------------------------------------
    Rohlik.cz ma oficialni MCP server (mcp.rohlik.cz) ktery pouziva
    tyto HTTP hlavicky misto session cookie. Pokud funguje i na beznych
    REST endpointech, muze HA volat Rohlik primo pres rest_command
    bez jakehokoli session managementu.
    """
    sekce("Header auth (rhl-email + rhl-pass)")
    info("Testujeme autentizaci pres HTTP hlavicky (bez cookies)")
    info("Zdroj: oficialny Rohlik MCP server na mcp.rohlik.cz")

    # Nova session BEZ predchoziho loginu – pouze hlavicky
    h_session = requests.Session()
    h_session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://www.rohlik.cz",
        "Referer": "https://www.rohlik.cz/",
        # Oficialny auth mechanismus z rohlik.cz/en-CZ/stranka/rohlik-mcp-server
        "rhl-email": EMAIL,
        "rhl-pass": HESLO,
    })

    vysledky_header = {}

    # --- Test A: Search bez loginu, pouze s hlavickami ---
    info("\n  [A] Search s rhl-email/rhl-pass hlavickami:")
    url_search = "https://www.rohlik.cz/services/frontend-service/search-metadata"
    params = {"search": HLEDANY_PRODUKT, "offset": 0, "limit": 5, "companyId": 1, "canCorrect": "true"}
    try:
        r = h_session.get(url_search, params=params, timeout=10)
        info(f"  Status: {r.status_code}")
        if r.status_code == 200:
            ok("Search funguje s header auth!")
            data = r.json().get("data", {})
            produkty = data.get("productList", [])
            info(f"  Nalezeno: {len(produkty)} produktu")
            if produkty:
                info(f"  Prvni: {produkty[0].get('productName')} – {produkty[0].get('price', {}).get('full')} Kc")
            vysledky_header["search"] = "OK"
        else:
            chyba(f"Search selhal: {r.status_code}")
            ukazat_response(r, zkratit=True)
            vysledky_header["search"] = f"FAILED ({r.status_code})"
    except Exception as e:
        chyba(f"Chyba: {e}")
        vysledky_header["search"] = "ERROR"

    # --- Test B: Kosik bez loginu, pouze s hlavickami ---
    info("\n  [B] Kosik s rhl-email/rhl-pass hlavickami:")
    url_cart = "https://www.rohlik.cz/services/frontend-service/v2/cart"
    try:
        r = h_session.get(url_cart, timeout=10)
        info(f"  Status: {r.status_code}")
        if r.status_code == 200:
            ok("Kosik funguje s header auth!")
            data = r.json().get("data", {})
            info(f"  Cart total: {data.get('totalPrice')} Kc")
            info(f"  Polozek: {len(data.get('items', {}))}")
            vysledky_header["kosik"] = "OK"
        else:
            chyba(f"Kosik selhal: {r.status_code}")
            ukazat_response(r, zkratit=True)
            vysledky_header["kosik"] = f"FAILED ({r.status_code})"
    except Exception as e:
        chyba(f"Chyba: {e}")
        vysledky_header["kosik"] = "ERROR"

    # --- Test C: MCP endpoint primo ---
    info("\n  [C] Oficialny MCP endpoint (mcp.rohlik.cz):")
    url_mcp = "https://mcp.rohlik.cz/mcp"
    # MCP pouziva JSON-RPC – zkusime jednoduchý initialize request
    mcp_payload = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "ha-rohlik-test", "version": "1.0"}
        },
        "id": 1
    }
    try:
        r = h_session.post(url_mcp, json=mcp_payload, timeout=10)
        info(f"  Status: {r.status_code}")
        if r.status_code == 200:
            ok("MCP endpoint dostupny!")
            ukazat_response(r, zkratit=True)
            vysledky_header["mcp_endpoint"] = "OK"
        else:
            info(f"  MCP endpoint status: {r.status_code}")
            ukazat_response(r, zkratit=True)
            vysledky_header["mcp_endpoint"] = f"STATUS {r.status_code}"
    except Exception as e:
        chyba(f"Chyba: {e}")
        vysledky_header["mcp_endpoint"] = "ERROR"

    # Souhrn header auth testu
    print("\n  --- Souhrn Header Auth ---")
    for test, vysledek in vysledky_header.items():
        emoji = "\u2705" if "OK" in vysledek else "\u274c"
        print(f"  {emoji}  header_{test:25s} {vysledek}")

    return vysledky_header


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

    # TEST 5: Header autentizace
    header_vysledky = test_header_auth()
    vysledky["header_auth_search"] = header_vysledky.get("search", "SKIPPED")
    vysledky["header_auth_kosik"] = header_vysledky.get("kosik", "SKIPPED")
    vysledky["mcp_endpoint"] = header_vysledky.get("mcp_endpoint", "SKIPPED")

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
