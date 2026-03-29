# CLAUDE.md – Rohlik.cz Home Assistant Integration

## Твůj první úkol: Discovery session

Než napíšeš jediný řádek kódu, proveď se mnou strukturovaný discovery interview.
Cílem je pochopit přesně co chci, jak to budu používat, a jaké mám technické prostředí.

Postupuj přesně takto:

---

## FÁZE 1: Discovery interview

Projdi všechny níže uvedené kategorie **jednu po druhé**.
Na každou kategorii se zeptej, **počkej na mou odpověď**, pak teprve pokračuj na další.
Neptej se na víc než 2–3 otázky najednou – nechci být zahlcen.

Začni tímto úvodním textem:
---
"Ahoj! Než začneme kódovat, potřebuji tě lépe poznat jako uživatele tohoto projektu.
Půjdeme kategorii po kategorii – bude to asi 6–8 krátkých bloků otázek.
Na konci z toho připravím kompletní technickou specifikaci.

Začněme:"
---

### Kategorie 1: Technické prostředí
- Na čem běží Home Assistant? (typ HW, RAM, OS)
- Jakou verzi HA používáš? (Settings → About)
- Používáš HACS? Pokud ano, máš ho nainstalovaný?
- Jak přistupuješ k HA? (HA OS, Container, Core, Supervised)

### Kategorie 2: Hlasové rozhraní
- Jaké hlasové asistenty používáš? (Alexa, Google, HA Assist, jiné)
- Máš nastavený HA Assist / Jarvis? Pokud ano, jak? (Whisper lokálně, cloud, jiné)
- Přes co chceš primárně hlasem zadávat položky? (telefon, chytré reproduktory, jiné)
- Chceš podporu češtiny, angličtiny, nebo obojí?

### Kategorie 3: Rohlík účet a nákupní chování
- Máš aktivní účet na Rohlík.cz?
- Jak často nakupuješ? (frekvence, průměrný počet položek)
- Máš oblíbené produkty / opakující se nákupy?
- Nakupuje přes Rohlík víc lidí v domácnosti, nebo jen ty?

### Kategorie 4: Požadované chování integrace
- Chceš položky přidávat přímo do košíku, nebo do samostatného seznamu / oblíbených?
- Co se má stát, když se produkt nenajde? (notifikace, fallback, nic)
- Co se má stát, když se najde víc variant? (přidat první, zeptat se, zobrazit výběr)
- Chceš aby integrace uměla i odebírat položky z košíku?
- Chceš vidět obsah košíku přímo v HA dashboardu?
- Chceš sensor s celkovou cenou košíku?

### Kategorie 5: Product mapping a learning
- Chceš aby si integrace pamatovala tvoje oblíbené produkty? (cache / mapping)
- Chceš mapping spravovat manuálně (YAML soubor), nebo automaticky (integrace si zapamatuje co jsi vybral)?
- Jak důležitá je přesnost produktu vs. rychlost přidání?
  (přidám cokoliv rychle vs. raději upozorni a počkej na potvrzení)

### Kategorie 6: Notifikace a feedback
- Přes co chceš dostávat notifikace? (HA mobilní app, TTS hlasem, obojí, nic)
- Chceš hlasovou odpověď potvrzující přidání? ("Přidáno mléko do košíku")
- Jaký detail chceš v notifikacích? (jen název produktu, i cena, i alternativy)

### Kategorie 7: HACS publikace
- Chceš integraci publikovat na HACS pro ostatní uživatele?
- Pokud ano – chceš ji dokumentovat česky, anglicky, nebo obojí?
- Máš GitHub účet připravený?
- Chceš aby integrace měla vlastní ikonu / logo?

### Kategorie 8: Technické zkušenosti a preference
- Jaké máš zkušenosti s Pythonem? (žádné / základy / pokročilý)
- Máš zkušenosti s vývojem HA integrací nebo custom components?
- Preferuješ kód s detailními komentáři (učím se), nebo čistý kód bez komentářů?
- Chceš průběžné vysvětlování async/await vzorů, nebo jen funkční kód?

---

## FÁZE 2: Shrnutí a potvrzení

Po skončení interview:

1. Shrň všechny odpovědi do přehledné tabulky / struktury
2. Identifikuj případné **konflikty nebo nejasnosti** a zeptej se na upřesnění
3. Navrhni **scope MVP** (co bude ve v1.0) vs. **future features** (co přijde později)
4. Počkej na moje potvrzení nebo korekce

---

## FÁZE 3: Vygeneruj finální specifikaci

Teprve po mém explicitním souhlasu ("Ok, generuj spec" nebo podobně) vytvoř soubor:

### `SPEC.md` – struktura

```
# Rohlik.cz HA Integration – Technical Specification

## 1. Project Overview
## 2. Architecture Diagram (ASCII)
## 3. Technical Environment
## 4. Feature List (MVP vs. Future)
## 5. File Structure
## 6. API Documentation (Rohlik endpoints + request/response examples)
## 7. Data Models (TypedDict / dataclasses)
## 8. Config Flow Design
## 9. Entity Definitions (Todo, Sensor, ...)
## 10. Product Resolution Logic (flowchart + pseudocode)
## 11. Notification Design
## 12. Error Handling Matrix
## 13. HACS / GitHub Repository Structure
## 14. Implementation Order (step-by-step)
## 15. Testing Strategy
## 16. Open Questions / TBD
```

---

## FÁZE 4: Verifikace Rohlík API

Před prvním řádkem produkčního kódu:

1. Napiš standalone Python skript `test_api.py` pro ověření Rohlík endpointů
2. Požádej mě o spuštění a výsledky
3. Podle výsledků uprav API sekci ve SPECu
4. Teprve pak začni s `api.py`

---

## FÁZE 0: Git a GitHub setup (provést jako úplně první věc)

Před interview i před jakýmkoliv kódem:

### 0a – Inicializace repozitáře
1. Ověř zda je v projektu inicializován git repozitář (`git status`)
2. Pokud ne: `git init`
3. Vytvoř `.gitignore` hned na začátku – musí obsahovat minimálně:
   ```
   .env
   secrets.yaml
   *.pyc
   __pycache__/
   .DS_Store
   ```

### 0b – GitHub setup
1. Zeptej se mě:
   - Máš již vytvořený GitHub repozitář, nebo ho mám pomoci připravit?
   - Má být repozitář veřejný (HACS vyžaduje public) nebo zatím privátní?
   - Jaký má být název repozitáře? (doporučení: `rohlik-ha`)
2. Podle odpovědi buď:
   - Napoj existující remote: `git remote add origin https://github.com/<user>/rohlik-ha.git`
   - Nebo připrav přesný postup jak repozitář na GitHubu vytvořit, než budeme pokračovat
3. Nastav výchozí branch: `git branch -M main`

### 0c – Branch strategie
Používáme **feature branch workflow**:
```
main          ← stabilní větev, vždy funkční, instaluje se na HA
dev           ← aktivní vývoj
feature/xxx   ← jednotlivé funkce
```
- Vývoj probíhá na `dev` nebo `feature/` větvích
- Do `main` mergujeme pouze otestovaný kód (po úspěšném testu na HA)
- Každý merge do `main` = nová verze k instalaci na HA

### 0d – Commit pravidla
- Commit message konvence: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`)
- Commituj po každé logicky ucelené změně
- Před každým commitem shrň co commitujeme a počkej na moje „ok"
- Před každým push do `main` počkej na moje explicitní potvrzení

Teprve po dokončení git setupu přejdi na FÁZI 1 (interview).

---

## Vývojový cyklus (opakuje se po celou dobu projektu)

Toto je náš standardní postup pro každou iteraci:

```
1. VÝVOJ (Mac + Claude Code)
   Píšeme / upravujeme kód na feature větvi

2. COMMIT + PUSH
   git add . → commit → push do GitHub
   (vždy s mým souhlasem)

3. INSTALACE NA HA
   Já na HA serveru:
   - přes HACS nebo manuálně stáhnu novou verzi z GitHubu
   - restartuji HA integraci

4. TESTOVÁNÍ
   Já testuji na reálném HA prostředí

5. FEEDBACK
   Hlásím výsledky zpět do Claude Code:
   - co funguje ✅
   - co nefunguje ❌ (chybová hláška, neočekávané chování)
   - co chybí 💡

6. DALŠÍ ITERACE
   Vrátíme se na krok 1
```

### Jak reportovat feedback (instrukce pro mě)
Při hlášení výsledků testů vždy uveď:
- Verzi kterou testuji (commit hash nebo datum)
- Co přesně jsem udělal (kroky k reprodukci)
- Co se stalo (chybová hláška z HA logu, nebo popis chování)
- Co jsem očekával

### Jak číst HA logy
```
Settings → System → Logs → filtruji "rohlik"
```
Nebo přes SSH/terminál:
```bash
ha logs | grep rohlik
```

---

## Důležité instrukce pro celou session

- Komunikuj česky, technické termíny ponechej anglicky
- Nikdy nezačínaj implementaci bez mého explicitního souhlasu
- Pokud narazíš na nejasnost, zastav a zeptej se
- Vždy navrhni více přístupů s trade-off analýzou pro klíčová rozhodnutí
- Upozorni na bezpečnostní rizika (credentials, API rate limiting, apod.)
- Kód komentuj přiměřeně mým zkušenostem (zjistíš v interview)
- Každý větší krok ukonči shrnutím "co jsme udělali" a "co je next step"
- Každá dokončená fáze = git commit (s mým souhlasem před push)
- Nikdy nepushuj bez mého explicitního souhlasu
