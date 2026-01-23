"""
Script de test pour verifier le scraping des actualites LinkedIn
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
import re
import sys


async def test_scrape_linkedin_news(url: str):
    """Test de scraping d'une URL LinkedIn News"""
    print(f"[TEST] Scraping pour: {url}\n")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            print("[INFO] Telechargement de la page...")
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            print(f"[OK] Status code: {response.status_code}")
            print(f"[OK] Content-Type: {response.headers.get('content-type')}")
            print(f"[OK] Taille de la reponse: {len(response.text)} caracteres\n")

            # Parser le HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Sauvegarder le HTML brut pour inspection
            with open("linkedin_news_raw.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("[SAVE] HTML brut sauvegarde dans: linkedin_news_raw.html\n")

            # Supprimer les scripts et styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Afficher le titre de la page
            title_tag = soup.find("title")
            if title_tag:
                print(f"[TITLE] Titre de la page: {title_tag.get_text(strip=True)}\n")

            # Tentative 1: Recherche des balises article
            print("[TRY 1] Recherche de <article>")
            article = soup.find("article")
            if article:
                content = article.get_text(separator=" ", strip=True)
                print(f"[OK] Trouve dans <article>: {len(content)} caracteres")
                print(f"[PREVIEW] Apercu: {content[:300]}...\n")
            else:
                print("[FAIL] Pas de balise <article>\n")

            # Tentative 2: Recherche de divs avec classes communes LinkedIn
            print("[TRY 2] Recherche de divs avec classes content/article/main")
            main_content = soup.find("div", class_=re.compile(r"(article|content|main|post)", re.IGNORECASE))
            if main_content:
                content = main_content.get_text(separator=" ", strip=True)
                print(f"[OK] Trouve dans <div>: {len(content)} caracteres")
                print(f"[PREVIEW] Apercu: {content[:300]}...\n")
            else:
                print("[FAIL] Pas de div avec classes communes\n")

            # Tentative 3: Recherche de toutes les divs avec du contenu
            print("[TRY 3] Liste de toutes les classes CSS trouvees")
            all_divs = soup.find_all("div", class_=True, limit=20)
            classes_found = set()
            for div in all_divs:
                classes = div.get("class", [])
                for cls in classes:
                    classes_found.add(cls)

            print(f"[CLASSES] Classes trouvees (echantillon): {sorted(list(classes_found))[:30]}\n")

            # Tentative 4: Extraction de tout le body
            print("[TRY 4] Extraction du <body> complet")
            body = soup.find("body")
            if body:
                content = body.get_text(separator=" ", strip=True)
                # Nettoyer les espaces multiples
                content = re.sub(r'\s+', ' ', content)
                print(f"[OK] Body extrait: {len(content)} caracteres")
                print(f"[PREVIEW] Apercu: {content[:500]}...\n")

                # Sauvegarder le contenu nettoye
                with open("linkedin_news_content.txt", "w", encoding="utf-8") as f:
                    f.write(content)
                print("[SAVE] Contenu nettoye sauvegarde dans: linkedin_news_content.txt\n")

                return content[:3000]  # Limiter a 3000 caracteres
            else:
                print("[FAIL] Pas de balise <body>\n")
                return None

    except httpx.HTTPError as e:
        print(f"[ERROR] Erreur HTTP: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    # URL de test fournie par l'utilisateur
    test_url = "https://www.linkedin.com/news/story/totalenergies-condamn%C3%A9-pour-greenwashing-7108041/"

    content = await test_scrape_linkedin_news(test_url)

    if content:
        print("\n" + "="*80)
        print("[SUCCESS] SCRAPING REUSSI")
        print("="*80)
        print(f"\nContenu extrait ({len(content)} caracteres):")
        print("-"*80)
        print(content)
        print("-"*80)
    else:
        print("\n" + "="*80)
        print("[FAIL] SCRAPING ECHOUE")
        print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
