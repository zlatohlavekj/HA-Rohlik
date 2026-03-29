# Rohlik.cz HA Integration – Technical Specification

> **Verze:** 0.1 (draft – API sekce bude upřesněna po spuštění `test_api.py`)
> **Datum:** 2026-03-29
> **Autor:** Jakub Zlatohlavek + Claude Code

---

## 1. Project Overview

Integrace umožňuje přidávat zboží do košíku na Rohlik.cz přímo z Home Assistant –
hlasem přes Jarvis (HA Assist) nebo přes mobilní aplikaci HA.
Integrace si pamatuje oblíbené produkty, zobrazuje stav košíku jako sensory
a posílá notifikace (push + TTS) při každé akci.

**Cílový uživatel:** Domácnost s více členy, primární vstup hlasem (Jarvis), záloha mobilní app.

---

## 2. Architecture Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────┐
│                    Home Assistant                        │
│                                                          │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │  HA Assist   │    │   rohlik integration         │   │
│  │  (Jarvis)    │───▶│                              │   │
│  └──────────────┘    │  ┌────────────────────────┐  │   │
│                      │  │  ProductResolver        │  │   │
│  ┌──────────────┐    │  │  1. hledat v cache      │  │   │
│  │  HA Mobile   │───▶│  │  2. volat Rohlik API    │  │   │
│  │  App         │    │  │  3. vybrat nejlevnější  │  │   │
│  └──────────────┘    │  └──────────┬─────────────┘  │   │
│                      │             │                  │   │
│  ┌──────────────┐    │  ┌──────────▼─────────────┐  │   │
│  │  Sensory     │◀───│  │  RohlikApiClient       │  │   │
│  │  cart_total  │    │  │  (aiohttp sessions)    │  │   │
│  │  cart_items  │    │  └──────────┬─────────────┘  │   │
│  └──────────────┘    │             │                  │   │
│                      │  ┌──────────▼─────────────┐  │   │
│  ┌──────────────┐    │  │  ProductCache           │  │   │
│  │  Notifikace  │◀───│  │  (JSON soubor na disku) │  │   │
│  │  Push + TTS  │    │  └────────────────────────┘  │   │
│  └──────────────┘    └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
                   ┌──────────────────┐
                   │   Rohlik.cz API  │
                   │  (REST / HTTPS)  │
                   └──────────────────┘
```

---

## 3. Technical Environment

| Parametr | Hodnota |
|---|---|
| Hardware | VM, 8 GB RAM |
| HA verze | Core 2026.3.4 |
| HA Supervisor | 2026.03.2 |
| HA OS | 17.1 |
| Instalace | HA OS |
| HACS | Nainstalován |
| Hlasový asistent | HA Assist + Jarvis (Nabu Casa) |
| Mobilní app | HA Companion App 2026.2.1 |
| Jazyk UI | Čeština + Angličtina |

---

## 4. Feature List

### MVP (v1.0)

| # | Feature | Popis |
|---|---|---|
| F01 | Config Flow | Přihlášení email + heslo, uložení auth tokenu |
| F02 | Service: add_to_cart | Přidání produktu do košíku podle názvu |
| F03 | Product Resolution | Cache → API search → nejlevnější varianta |
| F04 | Product Cache | Automatické ukládání mapování hlas→produkt |
| F05 | Sensor: cart_total | Celková cena košíku v Kč |
| F06 | Sensor: cart_items | Počet položek v košíku |
| F07 | Push notifikace | HA mobilní app – potvrzení přidání / chyba |
| F08 | TTS notifikace | Jarvis – hlasové potvrzení (název + cena) |
| F09 | Dashboard karta | Lovelace karta zobrazující obsah košíku |
| F10 | Jarvis setup guide | Průvodce instalací Jarvise (součást dokumentace) |

### Future (v2.0+)

| # | Feature |
|---|---|
| F11 | Alexa skill (přímá integrace bez HA jako prostředníka) |
| F12 | Service: remove_from_cart |
| F13 | Automatická objednávka v čas |
| F14 | Filtrace dle kategorie / značky |
| F15 | Podpora více Rohlík účtů |
| F16 | HACS publikace + vlastní ikona |
| F17 | Dokumentace CZ + EN (README, HACS info) |
| F18 | Sensor: ceny a slevy (alerting) |

---

## 5. File Structure

```
custom_components/rohlik/
├── __init__.py              # Inicializace integrace, setup platforem
├── manifest.json            # HACS/HA metadata (verze, závislosti)
├── config_flow.py           # UI průvodce nastavením (email + heslo)
├── const.py                 # Konstanty (DOMAIN, API URL, atd.)
├── api.py                   # RohlikApiClient – veškerá komunikace s API
├── product_cache.py         # ProductCache – čtení/zápis JSON cache
├── sensor.py                # Sensory: cart_total, cart_items
├── services.yaml            # Definice HA service (add_to_cart)
├── strings.json             # Překlady pro config flow (fallback)
└── translations/
    ├── cs.json              # Česká lokalizace
    └── en.json              # Anglická lokalizace

# Kořen repozitáře
├── CLAUDE.md                # Instrukce pro vývoj
├── SPEC.md                  # Tato specifikace
├── test_api.py              # Standalone skript pro ověření Rohlík API
├── .gitignore
├── LICENSE
└── README.md                # (bude vytvořen před HACS publikací)
```

---

## 6. API Documentation

> ⚠️ **PŘEDBĚŽNÁ SEKCE** – bude upřesněna po spuštění `test_api.py`
>
> Rohlík.cz nemá veřejně dokumentované API. Níže jsou odhadované endpointy
> na základě reverse-engineeringu. Vše musí být ověřeno!

### Base URL
```
https://www.rohlik.cz/api/v1
```

### Autentizace (odhad)
```
POST /login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "heslo"
}

Response:
{
  "token": "Bearer eyJ...",
  "userId": 12345
}
```

### Vyhledávání produktů (odhad)
```
GET /products/search?query=mleko&limit=10
Authorization: Bearer {token}

Response:
{
  "results": [
    {
      "id": 678901,
      "name": "Olma Mléko plnotučné 3,5% 1l",
      "price": 29.90,
      "pricePerUnit": "29,90 Kč/l",
      "inStock": true,
      "imageUrl": "https://..."
    },
    ...
  ]
}
```

### Košík – zobrazení (odhad)
```
GET /cart
Authorization: Bearer {token}

Response:
{
  "items": [
    {
      "productId": 678901,
      "name": "Olma Mléko plnotučné 3,5% 1l",
      "quantity": 2,
      "pricePerPiece": 29.90,
      "totalPrice": 59.80
    }
  ],
  "totalPrice": 59.80,
  "itemCount": 1
}
```

### Košík – přidání položky (odhad)
```
POST /cart/items
Authorization: Bearer {token}
Content-Type: application/json

{
  "productId": 678901,
  "quantity": 1
}

Response:
{
  "success": true,
  "cart": { ... }  // aktualizovaný košík
}
```

> 📋 **TODO po `test_api.py`:** Doplnit skutečné endpointy, hlavičky,
> formát session cookie vs. Bearer token, rate limiting.

---

## 7. Data Models

```python
# const.py + datové třídy používané napříč integrací

from typing import TypedDict

class RohlikProduct(TypedDict):
    """Jeden produkt vrácený z API nebo cache."""
    id: int                  # Interní ID produktu na Rohlik.cz
    name: str                # Celý název produktu
    price: float             # Cena v Kč
    in_stock: bool           # Je skladem?
    image_url: str           # URL obrázku (pro dashboard)

class CartItem(TypedDict):
    """Položka v košíku."""
    product_id: int
    name: str
    quantity: int
    price_per_piece: float
    total_price: float

class CartState(TypedDict):
    """Aktuální stav celého košíku."""
    items: list[CartItem]
    total_price: float       # Celková cena košíku v Kč
    item_count: int          # Počet různých položek

class CacheEntry(TypedDict):
    """Jeden záznam v product cache."""
    query: str               # Co uživatel řekl ("mléko")
    product_id: int          # Na jaký produkt se to mapuje
    product_name: str        # Název pro zobrazení
    last_used: str           # ISO datum posledního použití
    use_count: int           # Kolikrát bylo vybráno
```

---

## 8. Config Flow Design

```
Krok 1: Přihlašovací údaje
┌─────────────────────────────────────┐
│ Rohlik.cz – přihlášení              │
│                                     │
│ E-mail: [________________]          │
│ Heslo:  [________________]          │
│                                     │
│ [Zrušit]              [Přihlásit]   │
└─────────────────────────────────────┘
         │ úspěch                │ chyba
         ▼                       ▼
Krok 2: Nastavení notifikací    Chybová hláška
┌─────────────────────────────────────┐
│ Nastavení                           │
│                                     │
│ TTS entita: [select entity]         │
│ (např. tts.jarvis nebo prázdné)     │
│                                     │
│ [Zpět]               [Dokončit]     │
└─────────────────────────────────────┘
         │
         ▼
   Integrace přidána ✅
```

**Uložená data v `config_entry.data`:**
```python
{
    "email": "user@example.com",
    "auth_token": "eyJ...",     # Nikdy heslo – pouze token!
    "user_id": 12345,
    "tts_entity": "tts.piper",  # Nebo None pokud není nastaveno
}
```

---

## 9. Entity Definitions

### Sensor: `sensor.rohlik_cart_total`
| Parametr | Hodnota |
|---|---|
| Název | Rohlík – celková cena košíku |
| Unit | Kč |
| Icon | `mdi:cart` |
| State | float (cena v Kč, např. `459.50`) |
| Update interval | po každé akci + každých 5 minut |

### Sensor: `sensor.rohlik_cart_items`
| Parametr | Hodnota |
|---|---|
| Název | Rohlík – počet položek v košíku |
| Unit | položek |
| Icon | `mdi:cart-variant` |
| State | int (počet položek) |
| Attributes | `items` – list s názvem, množstvím a cenou každé položky |

### Service: `rohlik.add_to_cart`
```yaml
# services.yaml
add_to_cart:
  name: Přidat do košíku
  description: Přidá produkt do košíku na Rohlik.cz podle názvu.
  fields:
    product_name:
      name: Název produktu
      description: Co chceš přidat (např. "mléko", "chleba Šumava")
      required: true
      example: "mléko"
      selector:
        text:
    quantity:
      name: Množství
      description: Kolik kusů přidat (výchozí je 1)
      required: false
      default: 1
      selector:
        number:
          min: 1
          max: 99
```

---

## 10. Product Resolution Logic

```
Vstup: product_name (string od uživatele)
       quantity (int, default=1)

┌─────────────────────────────────────────────┐
│ 1. Normalizace vstupu                       │
│    lowercase, strip, odstranit diakritiku   │
│    "Mléko" → "mleko"                        │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ 2. Hledat v ProductCache                    │
│    Klíč: normalizovaný název                │
└────────┬────────────────────┬───────────────┘
         │ NALEZENO           │ NENALEZENO
         ▼                    ▼
┌─────────────────┐  ┌────────────────────────┐
│ Použít cached   │  │ 3. Volat Rohlik API    │
│ product_id      │  │    GET /search?q=...   │
└────────┬────────┘  └──────────┬─────────────┘
         │                      │
         │           ┌──────────▼─────────────┐
         │           │ Počet výsledků?        │
         │           └──┬──────────────┬──────┘
         │              │ 0            │ 1+
         │              ▼              ▼
         │    ┌──────────────┐ ┌───────────────────┐
         │    │ Notifikace:  │ │ Seřadit dle ceny  │
         │    │ "Nenalezeno" │ │ Vybrat nejlevnější│
         │    └──────────────┘ └────────┬──────────┘
         │                              │
         └──────────────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ 4. POST /cart/items   │
                  │    productId + qty    │
                  └───────────┬───────────┘
                              │
                  ┌───────────▼───────────┐
                  │ 5. Uložit do cache    │
                  │    query → product    │
                  └───────────┬───────────┘
                              │
                  ┌───────────▼───────────┐
                  │ 6. Notifikace         │
                  │    Push + TTS         │
                  │    "Přidáno X za Y Kč"│
                  └───────────────────────┘
```

---

## 11. Notification Design

### Push notifikace (HA mobilní app)

**Úspěch:**
```
Rohlík ✅
Přidáno: Olma Mléko 1l × 1
Cena: 29,90 Kč | Košík celkem: 489,40 Kč
```

**Nenalezeno:**
```
Rohlík ❌
Produkt nenalezen: "sýr gouda xyz"
Košík nebyl změněn.
```

### TTS hlasová odpověď (Jarvis)

**Úspěch (CZ):**
> *"Přidáno do košíku: Olma Mléko, cena dvacet devět korun devadesát."*

**Nenalezeno (CZ):**
> *"Produkt nenalezen: sýr gouda xyz. Zkus upřesnit název."*

---

## 12. Error Handling Matrix

| Situace | Chování | Notifikace |
|---|---|---|
| Špatné přihlašovací údaje | Config flow zobrazí chybu | Ne (uživatel vidí UI) |
| Token expiroval | Automaticky se obnoví, pokud se nepodaří → re-auth flow | Push: "Rohlík: nutné znovu přihlásit" |
| Produkt nenalezen | Nic nepřidat | Push + TTS: "Nenalezeno: X" |
| API nedostupné (timeout) | Retry 3× s exponenciálním backoff | Push po 3. neúspěchu: "Rohlík API nedostupné" |
| Produkt není skladem | Oznámit, nepřidávat | Push + TTS: "X není skladem" |
| Rate limiting (HTTP 429) | Počkat + retry | Push: "Rohlík: příliš mnoho požadavků" |

---

## 13. HACS / GitHub Repository Structure

> Aktivuje se ve v2.0 – viz Future features. Níže je přípravný plán.

```
zlatohlavekj/HA-Rohlik (GitHub, public)
├── custom_components/rohlik/   # Samotná integrace
├── hacs.json                   # HACS metadata
├── README.md                   # Dokumentace CZ + EN
├── CHANGELOG.md                # Historie verzí
├── LICENSE                     # MIT
└── .github/
    └── workflows/
        └── validate.yml        # HACS validation CI
```

**`hacs.json`** (bude vytvořen při HACS publikaci):
```json
{
  "name": "Rohlik.cz",
  "content_in_root": false,
  "render_readme": true,
  "homeassistant": "2024.1.0"
}
```

---

## 14. Implementation Order

Každý krok = samostatný commit na feature větvi.

```
Krok 1: FÁZE 4 – API verifikace
  → test_api.py – ověřit endpointy, auth, search, cart
  → Aktualizovat sekci 6 tohoto SPECu

Krok 2: Základní struktura
  → custom_components/rohlik/__init__.py (skeleton)
  → custom_components/rohlik/manifest.json
  → custom_components/rohlik/const.py

Krok 3: API klient
  → custom_components/rohlik/api.py
  → Implementovat: login, search, get_cart, add_to_cart

Krok 4: Config Flow
  → custom_components/rohlik/config_flow.py
  → UI pro email + heslo + TTS entita

Krok 5: Product Cache
  → custom_components/rohlik/product_cache.py
  → Čtení/zápis JSON souboru v HA config dir

Krok 6: Sensory
  → custom_components/rohlik/sensor.py
  → sensor.rohlik_cart_total + sensor.rohlik_cart_items

Krok 7: Service add_to_cart
  → Registrace service v __init__.py
  → Product Resolution Logic
  → services.yaml

Krok 8: Notifikace
  → Push (HA notify service)
  → TTS (volání tts entity)

Krok 9: Překlady
  → translations/cs.json
  → translations/en.json

Krok 10: Dashboard karta
  → Lovelace YAML příklad v dokumentaci

Krok 11: Testování na HA
  → Instalace, smoke test, iterace

Krok 12: Jarvis setup
  → Průvodce nastavením HA Assist + Jarvis
  → Příklad hlasových příkazů / intent
```

---

## 15. Testing Strategy

Vzhledem k nulovým zkušenostem s Pythonem a HA vývojem:

1. **Manuální testy na reálném HA** – primární metoda
2. **`test_api.py`** – standalone skript pro ověření API před implementací
3. **HA developer tools** – volání service `rohlik.add_to_cart` přímo z UI
4. **HA logy** – `Settings → System → Logs` filtr "rohlik"
5. **Smoke testy** po každém kroku implementace

Automatizované unit testy přijdou ve v2.0 (před HACS publikací).

---

## 16. Open Questions / TBD

| # | Otázka | Status |
|---|---|---|
| Q1 | Skutečné Rohlík API endpointy a formát auth | ⏳ Řeší `test_api.py` |
| Q2 | Session cookie nebo Bearer token? | ⏳ Řeší `test_api.py` |
| Q3 | Rate limiting Rohlík API | ⏳ Zjistit při testování |
| Q4 | Jarvis: jaký TTS engine (Piper / cloud)? | ⏳ Rozhodnout při instalaci |
| Q5 | Název HA service: `rohlik.add_to_cart` nebo `shopping.add_to_cart`? | 💡 Návrh: `rohlik.add_to_cart` |
| Q6 | Aktualizační interval sensorů (5 min nebo push-based)? | 💡 Návrh: 5 min + po každé akci |
