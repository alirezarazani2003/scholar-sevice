from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.orm import selectinload
from bs4 import BeautifulSoup
from typing import Optional
import urllib.parse
import httpx
import asyncio
from datetime import datetime, timedelta
from database import get_db, engine, Base
from models import ScholarProfile, Article
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(">>> Lifespan started")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)


# ========== Utility Models ==========

class ScholarRequest(BaseModel):
    user_url: str

class ArticleOut(BaseModel):
    title: str
    link: str
    year: str
    citations: int

class ScholarResponse(BaseModel):
    name: str
    affiliation: Optional[str]
    email: Optional[str]
    h_index_all: int
    h_index_recent: int
    i10_index_all: int
    i10_index_recent: int
    citations_all: int
    citations_recent: int
    articles: list[ArticleOut]

# ========== Helpers ==========

def safe_int(value):
    try:
        return int(value)
    except:
        return 0

async def fetch_page(client: httpx.AsyncClient, url: str):
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        return None

async def parse_articles(user_id: str, client: httpx.AsyncClient, max_articles=100):
    articles = []
    cstart = 0
    pagesize = 100
    while len(articles) < max_articles:
        url = f"https://scholar.google.com/citations?user={user_id}&hl=en&cstart={cstart}&pagesize={pagesize}"
        page_text = await fetch_page(client, url)
        if page_text is None:
            break
        soup = BeautifulSoup(page_text, "html.parser")
        rows = soup.find_all("tr", class_="gsc_a_tr")
        if not rows:
            break
        for row in rows:
            title_tag = row.find("a", class_="gsc_a_at")
            title = title_tag.text.strip() if title_tag else ""
            link = "https://scholar.google.com" + title_tag["href"] if title_tag else ""
            year_tag = row.find("span", class_="gsc_a_h")
            year = year_tag.text.strip() if year_tag else ""
            citation_tag = row.find("a", class_="gsc_a_ac")
            citations = citation_tag.text.strip() if citation_tag else "0"
            citations = int(citations) if citations.isdigit() else 0

            articles.append({
                "title": title,
                "link": link,
                "year": year,
                "citations": citations
            })
            if len(articles) >= max_articles:
                break
        if len(rows) < pagesize:
            break
        cstart += pagesize
        await asyncio.sleep(1)
    return articles

# ========== API ==========



@app.post("/scholar/profile/", response_model=ScholarResponse)
async def get_scholar_profile(request: ScholarRequest, db: AsyncSession = Depends(get_db)):
    user = request.user_url.strip()
    if user.startswith("http"):
        parsed = urllib.parse.urlparse(user)
        query_params = urllib.parse.parse_qs(parsed.query)
        if "user" in query_params:
            user_id = query_params["user"][0]
        else:
            raise HTTPException(status_code=400, detail="Invalid Google Scholar URL: missing user parameter")
    else:
        user_id = user

    # بررسی کش (۲۴ ساعت) با eager loading روی مقالات
    stmt = select(ScholarProfile).options(selectinload(ScholarProfile.articles)).where(ScholarProfile.user_id == user_id)
    result = await db.execute(stmt)
    profile: ScholarProfile = result.scalar_one_or_none()

    if profile and profile.updated_at > datetime.utcnow() - timedelta(hours=24):
        return ScholarResponse(
            name=profile.name,
            affiliation=profile.affiliation,
            email=profile.email,
            h_index_all=profile.h_index_all,
            h_index_recent=profile.h_index_recent,
            i10_index_all=profile.i10_index_all,
            i10_index_recent=profile.i10_index_recent,
            citations_all=profile.citations_all,
            citations_recent=profile.citations_recent,
            articles=[ArticleOut(
                title=article.title,
                link=article.link,
                year=article.year,
                citations=article.citations
            ) for article in profile.articles]
        )

    base_url = f"https://scholar.google.com/citations?user={user_id}&hl=en"
    headers = {"User-Agent": "Mozilla/5.0"}

    async with httpx.AsyncClient(headers=headers) as client:
        page_text = await fetch_page(client, base_url)
        if not page_text:
            raise HTTPException(status_code=500, detail="Failed to retrieve Google Scholar page")

        soup = BeautifulSoup(page_text, "html.parser")
        name_tag = soup.find("div", id="gsc_prf_in")
        if not name_tag:
            raise HTTPException(status_code=404, detail="Profile not found or page structure changed")

        name = name_tag.text.strip()
        affiliation_tag = soup.find("div", class_="gsc_prf_il")
        affiliation = affiliation_tag.text.strip() if affiliation_tag else ""
        email = None
        for div in soup.find_all("div", class_="gsc_prf_il"):
            if "Verified email" in div.text:
                email = div.text.strip()
                break

        indices = soup.find_all("td", class_="gsc_rsb_std")
        (citations_all, citations_recent, h_index_all, h_index_recent,
         i10_index_all, i10_index_recent) = [safe_int(i.text) if i else 0 for i in indices[:6]]

        articles_data = await parse_articles(user_id, client)

    # حذف داده‌ی قدیمی
    if profile:
        await db.execute(delete(Article).where(Article.profile_id == profile.id))
        await db.delete(profile)
        await db.commit()

    # ذخیره‌سازی جدید
    profile = ScholarProfile(
        user_id=user_id,
        name=name,
        affiliation=affiliation,
        email=email,
        h_index_all=h_index_all,
        h_index_recent=h_index_recent,
        i10_index_all=i10_index_all,
        i10_index_recent=i10_index_recent,
        citations_all=citations_all,
        citations_recent=citations_recent,
        updated_at=datetime.utcnow()
    )
    db.add(profile)
    await db.flush()  # برای گرفتن ID

    for a in articles_data:
        article = Article(
            profile_id=profile.id,
            title=a["title"],
            link=a["link"],
            year=a["year"],
            citations=a["citations"]
        )
        db.add(article)

    await db.commit()
    await db.refresh(profile)

    return ScholarResponse(
        name=profile.name,
        affiliation=profile.affiliation,
        email=profile.email,
        h_index_all=profile.h_index_all,
        h_index_recent=profile.h_index_recent,
        i10_index_all=profile.i10_index_all,
        i10_index_recent=profile.i10_index_recent,
        citations_all=profile.citations_all,
        citations_recent=profile.citations_recent,
        articles=[ArticleOut(
            title=a["title"],
            link=a["link"],
            year=a["year"],
            citations=a["citations"]
        ) for a in articles_data]
    )
