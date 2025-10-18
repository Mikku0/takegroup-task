# Article Scraper

Projekt do scrapowania artykułów z różnych źródeł i udostępniania ich przez REST API.

## Wymagania

- Python 3.10+
- PostgreSQL
- Chrome/Chromium (do headless browsing)
- Docker i Docker Compose (jeśli chcesz używać kontenerów)

## Uruchomienie przez Docker (rekomendowane)

1. Sklonuj repozytorium i przejdź do folderu projektu:
```bash
git clone https://github.com/Mikku0/takegroup-task.git
cd takegroup_task/takegroup
```

2. Uruchom Docker Desktop, zbuduj obrazy i uruchom kontenery:
```bash
docker-compose build --no-cache
docker-compose up
```

3. Serwer Django będzie dostępny na:
```
http://localhost:8000
```

4. API endpoints działają przez przeglądarkę (port 8000 z kontenera jest przekierowywany) lub `curl`:

```
http://localhost:8000/articles/
http://localhost:8000/articles/1/
http://localhost:8000/articles/?source=galicjaexpress.pl
```

5. Sprawdzenie bazy danych Postgres (ewentualnie):
```bash
docker exec -it takegroup-db-1 psql -U user -d article_scraper
```

W środku możesz używać standardowych komend SQL, np.:
```sql
SELECT * FROM scraper_article;
```

6. Scrapowanie artykułów (w kontenerze web, ewentualnie):
```bash
docker-compose exec takegroup-web-1 python manage.py scrape_articles
```

## Instalacja lokalna (bez Dockera)

1. Sklonuj repo i wejdź do folderu projektu

2. Stwórz i aktywuj venv:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

4. Utwórz bazę danych w PostgreSQL:
```sql
CREATE DATABASE article_scraper;
CREATE USER user WITH PASSWORD 'password123';
GRANT ALL PRIVILEGES ON DATABASE article_scraper TO user;
```

5. Uruchom migracje:
```bash
cd takegroup
python manage.py migrate
```

## Jak używać

### Scrapowanie artykułów
```bash
python manage.py scrape_articles
```

### Uruchomienie serwera
```bash
python manage.py runserver
```

Serwer wystartuje na `http://localhost:8000`

## API Endpoints

### Wszystkie artykuły
```
GET http://localhost:8000/articles/
```

### Pojedynczy artykuł
```
GET http://localhost:8000/articles/1/
```

### Filtrowanie po źródle
```
GET http://localhost:8000/articles/?source=galicjaexpress.pl
```

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

### Walidacja

Przed zapisem każdy URL jest sprawdzany czy już nie istnieje w bazie. Duplikaty są pomijane.
