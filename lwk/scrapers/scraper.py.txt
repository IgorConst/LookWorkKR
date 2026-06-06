import asyncio
import os
import re
from datetime import datetime
from urllib.parse import urljoin

from playwright.async_api import async_playwright
from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import select
from dotenv import load_dotenv

load_dotenv()

# ---------- База данных ----------
Base = declarative_base()

class Vacancy(Base):
    __tablename__ = 'vacancies'
    
    id = Column(String, primary_key=True)          # korect_12345
    source = Column(String, default='korect')
    url = Column(String, unique=True, nullable=False)
    title = Column(String)
    content = Column(Text)
    location = Column(String)
    published_at = Column(DateTime, nullable=True)
    raw_json = Column(Text)                         # запас на будущее
    created_at = Column(DateTime, default=datetime.utcnow)
    is_relevant = Column(Boolean, default=None)

# Асинхронный движок
engine = create_async_engine('sqlite+aiosqlite:///./lwk.db')
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ---------- Парсинг ----------
async def save_vacancy(vacancy_data):
    async with async_session() as session:
        # Проверяем, есть ли уже такой URL
        stmt = select(Vacancy).where(Vacancy.url == vacancy_data['url'])
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            print(f"Пропускаем дубликат: {vacancy_data['url']}")
            return
        vac = Vacancy(**vacancy_data)
        session.add(vac)
        await session.commit()
        print(f"Сохранено: {vacancy_data['title']}")

async def scrape_korect():
    email = os.getenv('KORECT_EMAIL')
    password = os.getenv('KORECT_PASSWORD')
    if not email or not password:
        print("Ошибка: задайте KORECT_EMAIL и KORECT_PASSWORD в .env")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Логин
        print("Логинимся...")
        await page.goto('https://korect.kr/login')
        await page.fill('input[name="email"]', email)
        await page.fill('input[name="password"]', password)
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        
        # 2. Переходим на страницу вакансий
        await page.goto('https://korect.kr/jobs')
        
        # 3. Скроллим до конца, пока грузятся новые
        print("Собираем все объявления (скролл)...")
        previous_count = 0
        while True:
            # Прокрутка вниз
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)  # ждём подгрузки
            
            # Считаем текущие карточки (подберите селектор, если надо)
            cards = await page.query_selector_all('.job-card, .post-card, [class*="job"]')
            current_count = len(cards)
            print(f"  Загружено объявлений: {current_count}")
            if current_count == previous_count:
                break
            previous_count = current_count
        
        # 4. Парсим каждую карточку
        cards = await page.query_selector_all('.job-card, .post-card, [class*="job"]')
        print(f"Найдено {len(cards)} объявлений")
        
        for card in cards:
            try:
                # Извлекаем ссылку (первая ссылка в карточке)
                link = await card.query_selector('a')
                if not link:
                    continue
                href = await link.get_attribute('href')
                if not href:
                    continue
                full_url = urljoin('https://korect.kr', href)
                
                # ID из URL (например /jobs/12345)
                match = re.search(r'/jobs/(\d+)', full_url)
                if not match:
                    continue
                job_id = match.group(1)
                
                # Заголовок
                title_elem = await card.query_selector('.title, h3, .job-title')
                title = await title_elem.inner_text() if title_elem else ''
                
                # Локация
                loc_elem = await card.query_selector('.location, .region, .place')
                location = await loc_elem.inner_text() if loc_elem else ''
                
                # Текст (короткое описание)
                desc_elem = await card.query_selector('.description, .content, .summary')
                content = await desc_elem.inner_text() if desc_elem else ''
                
                vacancy_data = {
                    'id': f'korect_{job_id}',
                    'url': full_url,
                    'title': title.strip(),
                    'location': location.strip(),
                    'content': content.strip(),
                    'published_at': None,  # на сайте может не быть явной даты
                    'raw_json': '',        # не используем пока
                }
                await save_vacancy(vacancy_data)
            except Exception as e:
                print(f"Ошибка при парсинге карточки: {e}")
        
        await browser.close()

async def main():
    await init_db()
    while True:
        print(f"\n--- Запуск сбора: {datetime.now()} ---")
        await scrape_korect()
        print(f"--- Ожидание {os.getenv('SCRAPE_INTERVAL_MINUTES', 30)} минут ---")
        await asyncio.sleep(int(os.getenv('SCRAPE_INTERVAL_MINUTES', 30)) * 60)

if __name__ == '__main__':
    asyncio.run(main())