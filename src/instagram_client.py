import instaloader
import time
import random
import os
from config import INSTAGRAM_USER, INSTAGRAM_PASSWORD

class InstagramClient:
    def __init__(self):
        self.L = instaloader.Instaloader()
        self.is_logged_in = False
        self.session_file = os.path.join(os.getcwd(), f"session-{INSTAGRAM_USER}")

        if INSTAGRAM_USER:
            self._smart_login()
        else:
            print("No Instagram credentials provided. Mock mode active.")

    def _smart_login(self):
        """Şifre yerine oturum dosyası ile giriş yapmayı dener."""
        try:
            # 1. Önce kayıtlı bir oturum dosyası var mı diye bak
            if os.path.exists(self.session_file):
                self.L.load_session_from_file(INSTAGRAM_USER, filename=self.session_file)
                print(f"Session loaded from file for {INSTAGRAM_USER}")
            else:
                # 2. Dosya yoksa normal giriş yap ve dosyayı oluştur
                print(f"No session file found. Logging in with password...")
                self.L.login(INSTAGRAM_USER, INSTAGRAM_PASSWORD)
                self.L.save_session_to_file(filename=self.session_file)
                print("New session file created.")
            
            self.is_logged_in = True
        except Exception as e:
            print(f"Login failed: {e}")
            self.is_logged_in = False

    def get_following(self, username):
        if not self.is_logged_in:
            print(f"Login required for {username}. Using mock data.")
            return self._get_mock_following(username)

        try:
            # Instagram'ın botu anlamaması için süreyi artıralım
            # 1000 kişi sorgulayacaksanız bu süre çok kritik!
            time.sleep(random.uniform(10, 25)) 
            
            profile = instaloader.Profile.from_username(self.L.context, username)
            followees = profile.get_followees()
            
            # Sadece ilk 100 takip edilen kişiyi al (Hız sınırı için önerilir)
            # Eğer hepsini isterseniz list(followee.username...) yapın ama risk artar.
            return [followee.username for followee in followees]
        except Exception as e:
            print(f"Error fetching data for {username}: {e}")
            if "429" in str(e):
                print("!!! RATE LIMIT: Instagram çok fazla istek attığımızı anladı !!!")
            return None

    def _get_mock_following(self, username):
        return ["dummy_user_1", "dummy_user_2"]
