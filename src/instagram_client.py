import time
import random
import requests
from typing import List, Optional

from config import RAPIDAPI_KEY, RAPIDAPI_HOST


class InstagramClient:
    """
    RapidAPI üzerinden 'following list' çeker.
    """

    def __init__(self):
        if not RAPIDAPI_KEY or not RAPIDAPI_HOST:
            raise RuntimeError(
                "RAPIDAPI_KEY / RAPIDAPI_HOST eksik. GitHub Secrets'e ekle."
            )

        self.base_url = f"https://{RAPIDAPI_HOST}"
        self.headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": RAPIDAPI_HOST,
        }

    def get_following(self, username_or_id_or_url: str, max_pages: int = 30) -> List[str]:
        """
        username_or_id_or_url: 'ksi' gibi username veya URL.
        max_pages: API pagination varsa kaç sayfa denesin.
        """
        # Bazı API'ler pagination için cursor/next_page kullanır.
        # Dokümana göre değişebiliyor; biz esnek okuyacağız.

        all_usernames: List[str] = []
        seen = set()

        cursor: Optional[str] = None

        for _ in range(max_pages):
            # Bot gibi görünmesin diye küçük jitter (özellikle çok hedefte iyi)
            time.sleep(random.uniform(0.7, 1.6))

            params = {"username_or_id_or_url": username_or_id_or_url}
            if cursor:
                # yaygın isimler: cursor / next_cursor / page_id vs.
                # bazı API'lerde "cursor" çalışıyor.
                params["cursor"] = cursor

            url = f"{self.base_url}/user/following"
            r = requests.get(url, headers=self.headers, params=params, timeout=30)

            if r.status_code == 429:
                # rate limit -> biraz bekle
                wait_s = random.uniform(20, 40)
                print(f"RATE LIMIT (429). {wait_s:.1f}s bekliyorum...")
                time.sleep(wait_s)
                continue

            r.raise_for_status()
            payload = r.json()

            # ---- ITEMS'i olabildiğince toleranslı çekiyoruz ----
            data = payload.get("data", payload)

            # Olası liste alanları
            items = (
                data.get("items")
                or data.get("users")
                or data.get("following")
                or data.get("list")
                or []
            )

            # items bazen [{username:..}, ...] bazen ["a","b"] gelir
            extracted = []
            for it in items:
                if isinstance(it, str):
                    extracted.append(it)
                elif isinstance(it, dict):
                    # farklı API'ler farklı alanlar kullanır
                    u = (
                        it.get("username")
                        or it.get("user", {}).get("username")
                        or it.get("pk")  # fallback (id)
                    )
                    if u:
                        extracted.append(str(u))

            # unique
            new_count = 0
            for u in extracted:
                if u not in seen:
                    seen.add(u)
                    all_usernames.append(u)
                    new_count += 1

            print(f"[{username_or_id_or_url}] +{new_count} (toplam {len(all_usernames)})")

            # ---- Pagination / next cursor ----
            # Olası cursor alanları
            cursor = (
                data.get("next_cursor")
                or data.get("cursor")
                or data.get("next_page")
                or data.get("paging", {}).get("next_cursor")
            )

            # Eğer pagination yoksa veya yeni ekleme yoksa çık
            if not cursor:
                break

        return all_usernames
