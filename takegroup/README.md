# Article Scraper

Projekt do scrapowania artykułów z różnych źródeł i udostępniania ich przez REST API.

## Wymagania

- Python 3.10+
- PostgreSQL
- Chrome/Chromium (do headless browsing)

## Instalacja

1. Sklonuj repo i wejdź do folderu projektu

2. Stwórz i aktywuj venv:
```bash
python -m venv venv
source venv/bin/activate  # na Linuxie/Mac

venv\Scripts\activate  # na Windowsie
```

3. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

3. Utwórz bazę danych w PostgreSQL:
```sql
CREATE DATABASE article_scraper;
CREATE USER user WITH PASSWORD 'password123';
GRANT ALL PRIVILEGES ON DATABASE article_scraper TO user;
```

4. Uruchom migracje:
```bash
cd takegroup
python manage.py migrate
```

## Jak używać

### Scrapowanie artykułów

Żeby zescrapować artykuły wystarczy odpalić:
```bash
python manage.py scrape_articles
```

Komenda automatycznie:
- Pobierze artykuły ze wszystkich źródeł
- Sprawdzi czy dany URL już nie istnieje w bazie
- Zapisze nowe artykuły
- Pokaże progress w terminalu

### Uruchomienie serwera

```bash
python manage.py runserver
```

Serwer wystartuje na `http://localhost:8000`

## API Endpoints

### Wszystkie artykuły
```bash
GET http://localhost:8000/articles/
```

Zwraca listę wszystkich zescrapowanych artykułów.

### Pojedynczy artykuł
```bash
GET http://localhost:8000/articles/1/
```

Zwraca szczegóły artykułu o danym ID.

### Filtrowanie po źródle
```bash
GET http://localhost:8000/articles/?source=galicjaexpress
```

Znajdzie wszystkie artykuły z URLi zawierających "galicjaexpress".

### Przykładowa odpowiedź:
```json
[
  {
    "id": 1,
    "title": "Ford C-Max - jaki silnik benzynowy wybrać...",
    "original_content": "<article>...</article>",
    "plain_text": "Ford C-Max to popularny...",
    "source_url": "https://galicjaexpress.pl/ford-c-max...",
    "publication_date": "14.10.2024 00:00:00",
    "scraped_at": "2024-10-15T17:45:23.123456Z"
  }
]
```

## Struktura projektu

```
takegroup/
├── scraper/              # Główna aplikacja
│   ├── models.py         # Model Article
│   ├── views.py          # API endpoints
│   ├── serializers.py    # Serializery DRF
│   └── management/
│       └── commands/
│           └── scrape_articles.py  # Komenda do scrapowania
└── takegroup/            # Ustawienia Django
    ├── settings.py
    └── urls.py
```

## Szczegóły techniczne

### Parsowanie dat
Scraper radzi sobie z różnymi formatami dat:
- ISO format: `2024-10-14T12:30:00`
- Polski format: `14 października 2024`
- Angielski: `October 14, 2024`
- Relatywne: `2 days ago`, `3 godziny temu`

Wszystkie są konwertowane do: `dd.mm.yyyy HH:mm:ss`

### Obsługa Cloudflare
Projekt używa `undetected-chromedriver` żeby ominąć zabezpieczenia Cloudflare. Jeśli strona ma challenge, scraper automatycznie czeka dłużej.

### Walidacja
Przed zapisem każdy URL jest sprawdzany czy już nie istnieje w bazie. Duplikaty są pomijane.
