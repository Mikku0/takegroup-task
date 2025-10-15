from django.core.management.base import BaseCommand
from scraper.models import Article
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil import parser
import re
import logging
import time
import atexit

logger = logging.getLogger(__name__)
def _safe_quit(self):
    try:
        if hasattr(self, 'service') and self.service and self.service.process:
            self.service.process.kill()
    except:
        pass
uc.Chrome.__del__ = _safe_quit

class Command(BaseCommand):
    help = 'Scrape articles from specified URLs'

    URLS = [
        'https://galicjaexpress.pl/ford-c-max-jaki-silnik-benzynowy-wybrac-aby-zaoszczedzic-na-paliwie',
        'https://galicjaexpress.pl/bmw-e9-30-cs-szczegolowe-informacje-o-osiagach-i-historii-modelu',
        'https://take-group.github.io/example-blog-without-ssr/jak-kroic-piers-z-kurczaka-aby-uniknac-suchych-kawalkow-miesa',
        'https://take-group.github.io/example-blog-without-ssr/co-mozna-zrobic-ze-schabu-oprocz-kotletow-5-zaskakujacych-przepisow',
        'https://www.pap.pl/aktualnosci/konkurs-chopinowski-vincent-ong-w-grze-nie-jestem-nonszalancki-ale-swiadomy',
        'https://przegladsportowy.onet.pl/pilka-nozna/reprezentacja-polski/najwyzsza-pora-powiedziec-to-glosno-o-jerzym-brzeczku-fakty-musza-zatanczyc/k9jl954',
        'https://www.bbc.com/news/articles/c803rmdzjdjo',
    ]

    def __init__(self):
        super().__init__()
        self.driver = None
        self.cleanup_done = False

    def handle(self, *args, **options):
        total = len(self.URLS)
        
        self.setup_driver()
        
        atexit.register(self.cleanup_driver)
        
        try:
            for idx, url in enumerate(self.URLS, 1):
                self.stdout.write(f"Scraping article {idx}/{total}...")
                
                if Article.objects.filter(source_url=url).exists():
                    self.stdout.write(self.style.WARNING(f'Article already exists: {url}'))
                    continue
                
                try:
                    article_data = self.scrape_article(url)
                    if article_data:
                        Article.objects.create(**article_data)
                        self.stdout.write(self.style.SUCCESS(f'Successfully scraped: {url}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'Failed to scrape: {url}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error scraping {url}: {str(e)}'))
                    logger.error(f'Error scraping {url}: {str(e)}')
                
        finally:
            self.cleanup_driver()
    
    def cleanup_driver(self):
        """Bezpieczne zamknięcie drivera"""
        if self.cleanup_done or not self.driver:
            return
        
        try:
            if hasattr(self.driver, 'service') and self.driver.service:
                if hasattr(self.driver.service, 'process') and self.driver.service.process:
                    try:
                        self.driver.service.process.terminate()
                    except:
                        pass
            
            try:
                self.driver.quit()
            except:
                pass
                
        except Exception as e:
            pass
        finally:
            self.driver = None
            self.cleanup_done = True

    def setup_driver(self):
        """Konfiguracja undetected-chromedriver"""
        try:
            options = uc.ChromeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            self.driver = uc.Chrome(
                options=options, 
                version_main=None,
                use_subprocess=False
            )
            
            self.stdout.write(self.style.SUCCESS('Driver initialized successfully'))
        except Exception as e:
            logger.error(f'Failed to initialize WebDriver: {str(e)}')
            raise

    def scrape_article(self, url):
        try:
            self.driver.get(url)
            
            
            self.driver.execute_script("return document.readyState") == "complete"
            
            page_source = self.driver.page_source
            
            if '403 Forbidden' in page_source or 'Request forbidden' in page_source:
                logger.error(f'Got 403 error page for {url}')
                return None
            
            if 'Checking your browser' in page_source or 'Just a moment' in page_source:
                logger.info(f'Cloudflare challenge detected, waiting longer...')
                time.sleep(10)
                page_source = self.driver.page_source
            
            soup = BeautifulSoup(page_source, 'html.parser')
            
            title = self.extract_title(soup)
            
            if '403' in title or 'Forbidden' in title or 'Just a moment' in title:
                logger.warning(f'Article blocked or Cloudflare challenge failed for {url}')
                return None
            
            original_content, plain_text = self.extract_content(soup)
            publication_date = self.extract_and_normalize_date(soup, url)
            
            return {
                'title': title,
                'original_content': original_content,
                'plain_text': plain_text,
                'source_url': url,
                'publication_date': publication_date,
            }
        except Exception as e:
            logger.error(f'Error parsing article {url}: {str(e)}')
            return None

    def extract_title(self, soup):
        title = (soup.find('h1') or 
                soup.find('title') or 
                soup.find('meta', property='og:title'))
        
        if title:
            return title.get_text(strip=True) if hasattr(title, 'get_text') else title.get('content', '')
        return 'No title found'

    def extract_content(self, soup):
        for script in soup(['script', 'style', 'nav', 'header', 'footer']):
            script.decompose()
        
        content_div = (soup.find('article') or 
                      soup.find('div', class_=re.compile('content|article|post')) or
                      soup.find('main'))
        
        if content_div:
            original_content = str(content_div)
            plain_text = content_div.get_text(separator=' ', strip=True)
        else:
            original_content = str(soup.find('body'))
            plain_text = soup.get_text(separator=' ', strip=True)
        
        plain_text = re.sub(r'\s+', ' ', plain_text).strip()
        
        return original_content, plain_text

    def extract_and_normalize_date(self, soup, url):
        date_str = None
        
        meta_date = soup.find('meta', property='article:published_time')
        if not meta_date:
            meta_date = soup.find('meta', attrs={'name': 'publishDate'})
        if not meta_date:
            meta_date = soup.find('meta', attrs={'name': 'publication_date'})
        if not meta_date:
            meta_date = soup.find('meta', attrs={'property': 'article:published'})
        
        if meta_date:
            date_str = meta_date.get('content') or meta_date.get('datetime')
        
        if not date_str:
            time_tag = soup.find('time')
            if time_tag:
                date_str = time_tag.get('datetime') or time_tag.get_text()
        
        if not date_str:
            date_div = soup.find('div', class_=re.compile('date|time|published'))
            if date_div:
                date_str = date_div.get_text()
            
            if not date_str:
                date_p = soup.find('p', string=re.compile(r'\d{1,2}\s+(stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia)\s+\d{4}', re.IGNORECASE))
                if date_p:
                    date_str = date_p.get_text()
        
        if not date_str:
            text = soup.get_text()
            date_patterns = [
                r'\d{1,2}\s+(stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia)\s+\d{4}',
                r'\d{1,2}\.\d{1,2}\.\d{4}',
                r'\d{4}-\d{2}-\d{2}',
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    date_str = match.group(0)
                    break
        
        return self.normalize_date(date_str)

    def normalize_date(self, date_str):
        if not date_str:
            return datetime.now().strftime('%d.%m.%Y 00:00:00')

        try:
            date_str_lower = date_str.lower().strip()

            date_str_lower = re.split(r'aktualizacja|update|zaktualizowano|updated', date_str_lower)[0].strip()

            polish_months = {
                'stycznia': 'January', 'lutego': 'February', 'marca': 'March',
                'kwietnia': 'April', 'maja': 'May', 'czerwca': 'June',
                'lipca': 'July', 'sierpnia': 'August', 'września': 'September',
                'października': 'October', 'listopada': 'November', 'grudnia': 'December'
            }

            for polish, english in polish_months.items():
                if polish in date_str_lower:
                    date_str_lower = date_str_lower.replace(polish, english)
                    break
                
            if 'ago' in date_str_lower or 'temu' in date_str_lower:
                return self.parse_relative_date(date_str_lower)

            if 'today' in date_str_lower or 'dzisiaj' in date_str_lower:
                return datetime.now().strftime('%d.%m.%Y 00:00:00')

            if 'yesterday' in date_str_lower or 'wczoraj' in date_str_lower:
                return (datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y 00:00:00')

            dt = parser.parse(date_str_lower, dayfirst=True)
            return dt.strftime('%d.%m.%Y %H:%M:%S')

        except Exception as e:
            logger.warning(f'Could not parse date: {date_str}. Error: {str(e)}')
            return datetime.now().strftime('%d.%m.%Y 00:00:00')


    def parse_relative_date(self, date_str):
        now = datetime.now()
        
        numbers = re.findall(r'\d+', date_str)
        if not numbers:
            return now.strftime('%d.%m.%Y 00:00:00')
        
        value = int(numbers[0])
        
        if 'minute' in date_str or 'minut' in date_str:
            dt = now - timedelta(minutes=value)
        elif 'hour' in date_str or 'godzin' in date_str:
            dt = now - timedelta(hours=value)
        elif 'day' in date_str or 'dni' in date_str or 'dzień' in date_str:
            dt = now - timedelta(days=value)
        elif 'week' in date_str or 'tydz' in date_str:
            dt = now - timedelta(weeks=value)
        elif 'month' in date_str or 'miesi' in date_str:
            dt = now - timedelta(days=value * 30)
        else:
            dt = now
        
        return dt.strftime('%d.%m.%Y %H:%M:%S')