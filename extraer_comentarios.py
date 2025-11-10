import pandas as pd
from apify_client import ApifyClient
import time
import re
import logging
import html
import unicodedata
import os
import random
from pathlib import Path

# Configurar logging más limpio
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# --- PARÁMETROS DE CONFIGURACIÓN ---
APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
SOLO_PRIMER_POST = False

# LISTA DE URLs A PROCESAR
URLS_A_PROCESAR = [
    # Instagram
    "https://www.instagram.com/p/DOd_xzvAM_W/",
    "https://www.instagram.com/p/DOeAYHHABLU/",
    "https://www.instagram.com/p/DOnCgSHgM-y/",
    "https://www.instagram.com/p/DOnCcIqgMCH/",
    "https://www.instagram.com/p/DOnCguMALGb/",
    "https://www.instagram.com/p/DOnCceWAKKV/",
    "https://www.instagram.com/p/DOnCdcwgPcG/",
    "https://www.instagram.com/p/DOnCg1YgFk5/",
    "https://www.instagram.com/p/DOnChNSgAYc/",
    "https://www.instagram.com/p/DOnCgxOAHEq/",
    "https://www.instagram.com/p/DOnCgcmgGK0/",
    "https://www.instagram.com/p/DOnCgXEAOf3/",
    "https://www.instagram.com/p/DOnCeYUAJRW/",
    "https://www.instagram.com/p/DOnCg3nANGQ/",
    "https://www.instagram.com/p/DOnA0a_gNUN/",
    "https://www.instagram.com/p/DOnA0ZyAAFp/",
    "https://www.instagram.com/p/DOnA0TaAFej/",
    "https://www.instagram.com/p/DOnA0ZGAOX_/",
    "https://www.instagram.com/p/DOnAdDbAAiy/",
    "https://www.instagram.com/p/DOnAWX2gAt0/",
    "https://www.instagram.com/p/DPFJuzsgOwv/",
    "https://www.instagram.com/p/DPR99idgI9r/",
    "https://www.instagram.com/p/DPR8fkYgHTX/",
    "https://www.instagram.com/p/DPR8fIPgHFb/",
    "https://www.instagram.com/p/DPR8eD8gF6h/",
    "https://www.instagram.com/p/DPR8fZLgJpl/",
    "https://www.instagram.com/p/DPy8k4_AOBD/#advertiser",
    "https://www.instagram.com/p/DPjQxzsgP9k/",
    "https://www.instagram.com/p/DPT9nOrgFWC/",
    "https://www.instagram.com/p/DPT9op8ACyI/",
    "https://www.instagram.com/p/DPT9DVHAOcj/",
    "https://www.instagram.com/p/DPjQxUVgLTi/",
    "https://www.instagram.com/p/DPjQvlpgP7f/",
    "https://www.instagram.com/p/DPjQ0EzAJnK/",
    "https://www.instagram.com/p/DPjQwjegD_D/",
    "https://www.instagram.com/p/DPjQx63AC1N/",
    "https://www.instagram.com/p/DPjQxFPADDe/",
    "https://www.instagram.com/p/DPjQxtuAAgA/",
    "https://www.instagram.com/p/DPjQ0HqALjk/",
    "https://www.instagram.com/p/DPjQx2gAK2t/",
    "https://www.instagram.com/p/DPy9BftAHKl/",
    "https://www.instagram.com/p/DPojcrxAM4H/",  # NUEVO
    # NUEVOS
    "https://www.instagram.com/p/DQHoasBAIfd/",
    "https://www.instagram.com/p/DQHoMgYALbI/",
    "https://www.instagram.com/p/DQHoPChAIOT/",  # NUEVO

    # Facebook
    "https://www.facebook.com/100064867445065/posts/1217384173767153/",
    "https://www.facebook.com/100064867445065/posts/1217383833767187/",
    "https://www.facebook.com/100064867445065/posts/pfbid0SavmgcaTFNzwfFbxDjerqF3UqUGfaAqmmPcwmZByX9WDG4EfBkZRCeEqgf5efwFrl",
    "https://www.facebook.com/100064867445065/posts/pfbid02ppUkwFwzAXGKLcN7drP62ycAUAYiFqNH2krNQ3ge1Dd8ZT3xMz9kYVQC9658tfnbl",
    "https://www.facebook.com/100064867445065/posts/pfbid02t4sFi6WKSVmp6JGpgdfE3FLTcv5dkeoBD9QHhEPbaMVzYu9s6UnqJrw1tdSUKaR7l",
    "https://www.facebook.com/100064867445065/posts/pfbid0wTzVhu4ajvcZ1aA2pbhwPLrt55dveoPzZmqeVTZjwpN7d3LAXKxhbtFXEJXeH9mfl",
    "https://www.facebook.com/100064867445065/posts/pfbid02vdPitVJiBYmgUj2cs2HLuPtnjPWZi5kCTr7R3TJdLztGVesardr8vhZtZkmHp9q2l",
    "https://www.facebook.com/100064867445065/posts/pfbid01EjxNJLRY9MPCKpT7FyYRd1AvfotVwhszWg6Pzs5tWFraBUi6bnXejiwx5Ay29q2l",
    "https://www.facebook.com/?feed_demo_ad=120236325287690640&h=AQChRhkkhNKW_tQFdAY",
    "https://www.facebook.com/?feed_demo_ad=120236324670140640&h=AQB44Ut65grP7KBN0So",
    "https://www.facebook.com/?feed_demo_ad=120236325130830640&h=AQBAGgJAQSY4ch_Hb7U",
    "https://www.facebook.com/?feed_demo_ad=120236325185800640&h=AQAtF24HPHNHakqWzd0",
    "https://www.facebook.com/?feed_demo_ad=120236325162820640&h=AQAYz3GDquTbbeIjmwI",
    "https://www.facebook.com/100064867445065/posts/1247791610726409/?dco_ad_token=Aapj_AgRyAFyvo58bReyXQGjyl3pjEyOg8MQNF6BORDzFYIihmO-xoWfuEuSa0rAHUoXymfIucjCZAaA&dco_ad_id=120237209483310640",
    "https://www.facebook.com/100064867445065/posts/1243854187786818/",  # NUEVO
    # NUEVOS
    "https://www.facebook.com/reel/1177590664294662/",
    "https://www.facebook.com/reel/1370746317719068/",
    "https://www.facebook.com/reel/809881044994848/",

    # Facebook Ads Preview - NUEVOS
    "https://fb.me/adspreview/facebook/xyJOJX8PHYTM8oJ",
    "https://fb.me/adspreview/managedaccount/2aRfHsDy89jxW93",
    "https://fb.me/adspreview/facebook/1XSspjnNpZ7Xclk",
    "https://fb.me/adspreview/managedaccount/1NLhcIvXPBnkxua",
    "https://fb.me/adspreview/managedaccount/1WBSjxvvcydmg71",
    "https://fb.me/adspreview/managedaccount/1PTTEWDqSBHrTp6",
    "https://fb.me/adspreview/managedaccount/26jLT5hEl4ArwW4",
    "https://fb.me/adspreview/managedaccount/282xllZSByJtLFi",
    "https://fb.me/adspreview/managedaccount/1Xmb2M9HrnehjNO",

    # TikTok
    "https://www.tiktok.com/@MS4wLjABAAAAz0g6ilGOuqLdsyj6yj4S_laG21HJXjmypCSGqYY52fGrNTFvF0rbzfybfnxjrpxd/video/7549227541463043329",
    "https://www.tiktok.com/@user369347738/video/7548206070330559762",
    "https://www.tiktok.com/@MS4wLjABAAAAz0g6ilGOuqLdsyj6yj4S_laG21HJXjmypCSGqYY52fGrNTFvF0rbzfybfnxjrpxd/video/7548890366028664072",
    "https://www.tiktok.com/@user369347738/video/7548206069886061831",
    "https://www.tiktok.com/@MS4wLjABAAAAz0g6ilGOuqLdsyj6yj4S_laG21HJXjmypCSGqYY52fGrNTFvF0rbzfybfnxjrpxd/video/7548918352757001490",
    "https://www.tiktok.com/@MS4wLjABAAAAz0g6ilGOuqLdsyj6yj4S_laG21HJXjmypCSGqYY52fGrNTFvF0rbzfybfnxjrpxd/video/7548890366343171346",
    "https://www.tiktok.com/@MS4wLjABAAAAz0g6ilGOuqLdsyj6yj4S_laG21HJXjmypCSGqYY52fGrNTFvF0rbzfybfnxjrpxd/video/7548890371032419591",
    "https://www.tiktok.com/@MS4wLjABAAAAz0g6ilGOuqLdsyj6yj4S_laG21HJXjmypCSGqYY52fGrNTFvF0rbzfybfnxjrpxd/video/7548872989274672401",
    "https://www.tiktok.com/@alpinacol/video/7556666050583153928?_r=1&_t=ZS-90MGnBfy2pL",
    "https://www.tiktok.com/@alpinacol/video/7556663564489035029?_r=1&_t=ZS-90MGkBmNinS",
    "https://www.tiktok.com/@alpinacol/video/7556666045008842000?_r=1&_t=ZS-90MGhMRg7y4",
    "https://www.tiktok.com/@alpinacol/video/7556663878726307079?_r=1&_t=ZS-90MGVU9MQ7E",
    "https://www.tiktok.com/@alpinacol/video/7556663564489051413?_r=1&_t=ZS-90MGTFdxSyY",
    "https://www.tiktok.com/@alpinacol/video/7556666043746340112?_r=1&_t=ZS-90MGQkEa5xf",
    "https://www.tiktok.com/@alpinacol/video/7554519618174389512?_r=1&_t=ZS-90MGNDfj7qM",
    "https://www.tiktok.com/@alpinacol/video/7556666047076502785?_r=1&_t=ZS-90MGLX55n8M",
    "https://www.tiktok.com/@alpinacol/video/7558824662910782738?_r=1&_t=ZS-90Y3Ojc0EAZ",
    "https://www.tiktok.com/@alpinacol/video/7558824665163074834?_r=1&_t=ZS-90Y3RPVylPE",
    "https://www.tiktok.com/@alpinacol/video/7558824655524547841?_r=1&_t=ZS-90Y3ZvDjcrH",
    "https://www.tiktok.com/@alpinacol/video/7558824662910749970?_r=1&_t=ZS-90Y3ds3sXZ9",
    "https://www.tiktok.com/@alpinacol/video/7558824666261916936?_r=1&_t=ZS-90Y3gsjNZD8",
    "https://www.tiktok.com/@alpinacol/video/7558824653947538705?_r=1&_t=ZS-90Y3izNiVRH",
    "https://www.tiktok.com/@alpinacol/video/7558824665162976530?_r=1&_t=ZS-90Y3mahC8u7",
    "https://www.tiktok.com/@alpinacol/video/7558824657030302993?_r=1&_t=ZS-90Y3nvXXWOQ",
    "https://www.tiktok.com/@alpinacol/video/7558824664991010066?_r=1&_t=ZS-90Y3qQAvrGy",
    "https://www.tiktok.com/@alpinacol/video/7558824650868837648?_r=1&_t=ZS-90jgxZNxMiO",
    # NUEVOS
    "https://vt.tiktok.com/ZSyJy8Kv2/",
    "https://vt.tiktok.com/ZSyJUsbVn/",

    
]

# INFORMACIÓN DE CAMPAÑA
CAMPAIGN_INFO = {
    'campaign_name': 'CAMPAÑA_MANUAL_MULTIPLE',
    'campaign_id': 'MANUAL_002',
    'campaign_mes': 'Septiembre 2025',
    'campaign_marca': 'TU_MARCA',
    'campaign_referencia': 'REF_MANUAL',
    'campaign_objetivo': 'Análisis de Comentarios'
}

class SocialMediaScraper:
    def __init__(self, apify_token):
        self.client = ApifyClient(apify_token)

    def detect_platform(self, url):
        if pd.isna(url) or not url: return None
        url = str(url).lower()
        if any(d in url for d in ['facebook.com', 'fb.com']): return 'facebook'
        if 'instagram.com' in url: return 'instagram'
        if 'tiktok.com' in url: return 'tiktok'
        return None

    def clean_url(self, url):
        return str(url).split('?')[0] if '?' in str(url) else str(url)

    def fix_encoding(self, text):
        if pd.isna(text) or text == '': return ''
        try:
            text = str(text)
            text = html.unescape(text)
            text = unicodedata.normalize('NFKD', text)
            return text.strip()
        except Exception as e:
            logger.warning(f"Could not fix encoding: {e}")
            return str(text)

    def _wait_for_run_finish(self, run):
        logger.info("Scraper initiated, waiting for results...")
        max_wait_time = 300
        start_time = time.time()
        while True:
            run_status = self.client.run(run["id"]).get()
            if run_status["status"] in ["SUCCEEDED", "FAILED", "TIMED-OUT"]:
                return run_status
            if time.time() - start_time > max_wait_time:
                logger.error("Timeout reached while waiting for scraper.")
                return None
            time.sleep(10)

    def scrape_facebook_comments(self, url, max_comments=500, campaign_info=None, post_number=1):
        try:
            logger.info(f"Processing Facebook Post {post_number}: {url}")
            run_input = {"startUrls": [{"url": self.clean_url(url)}], "maxComments": max_comments}
            run = self.client.actor("apify/facebook-comments-scraper").call(run_input=run_input)
            run_status = self._wait_for_run_finish(run)
            if not run_status or run_status["status"] != "SUCCEEDED":
                logger.error(f"Facebook extraction failed. Status: {run_status.get('status', 'UNKNOWN')}")
                return []
            items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            logger.info(f"Extraction complete: {len(items)} items found.")
            return self._process_facebook_results(items, url, post_number, campaign_info)
        except Exception as e:
            logger.error(f"Fatal error in scrape_facebook_comments: {e}")
            return []

    def scrape_instagram_comments(self, url, max_comments=500, campaign_info=None, post_number=1):
        try:
            logger.info(f"Processing Instagram Post {post_number}: {url}")
            run_input = {"directUrls": [url], "resultsType": "comments", "resultsLimit": max_comments}
            run = self.client.actor("apify/instagram-scraper").call(run_input=run_input)
            run_status = self._wait_for_run_finish(run)
            if not run_status or run_status["status"] != "SUCCEEDED":
                logger.error(f"Instagram extraction failed. Status: {run_status.get('status', 'UNKNOWN')}")
                return []
            items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            logger.info(f"Extraction complete: {len(items)} items found.")
            return self._process_instagram_results(items, url, post_number, campaign_info)
        except Exception as e:
            logger.error(f"Fatal error in scrape_instagram_comments: {e}")
            return []

    def scrape_tiktok_comments(self, url, max_comments=500, campaign_info=None, post_number=1):
        try:
            logger.info(f"Processing TikTok Post {post_number}: {url}")
            run_input = {"postURLs": [self.clean_url(url)], "maxCommentsPerPost": max_comments}
            run = self.client.actor("clockworks/tiktok-comments-scraper").call(run_input=run_input)
            run_status = self._wait_for_run_finish(run)
            if not run_status or run_status["status"] != "SUCCEEDED":
                logger.error(f"TikTok extraction failed. Status: {run_status.get('status', 'UNKNOWN')}")
                return []
            items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            logger.info(f"Extraction complete: {len(items)} comments found.")
            return self._process_tiktok_results(items, url, post_number, campaign_info)
        except Exception as e:
            logger.error(f"Fatal error in scrape_tiktok_comments: {e}")
            return []

    def _process_facebook_results(self, items, url, post_number, campaign_info):
        processed = []
        possible_date_fields = ['createdTime', 'timestamp', 'publishedTime', 'date', 'createdAt', 'publishedAt']
        for comment in items:
            created_time = None
            for field in possible_date_fields:
                if field in comment and comment[field]:
                    created_time = comment[field]
                    break
            comment_data = {
                **campaign_info,
                'post_url': normalize_url(url),
                'post_url_original': url,
                'post_number': post_number,
                'platform': 'Facebook',
                'author_name': self.fix_encoding(comment.get('authorName')),
                'author_url': comment.get('authorUrl'),
                'comment_text': self.fix_encoding(comment.get('text')),
                'created_time': created_time,
                'likes_count': comment.get('likesCount', 0),
                'replies_count': comment.get('repliesCount', 0),
                'is_reply': False,
                'parent_comment_id': None,
                'created_time_raw': str(comment)
            }
            processed.append(comment_data)
        logger.info(f"Processed {len(processed)} Facebook comments.")
        return processed

    def _process_instagram_results(self, items, url, post_number, campaign_info):
        processed = []
        possible_date_fields = ['timestamp', 'createdTime', 'publishedAt', 'date', 'createdAt', 'taken_at']
        for item in items:
            comments_list = item.get('comments', [item]) if item.get('comments') is not None else [item]
            for comment in comments_list:
                created_time = None
                for field in possible_date_fields:
                    if field in comment and comment[field]:
                        created_time = comment[field]
                        break
                author = comment.get('ownerUsername', '')
                comment_data = {
                    **campaign_info,
                    'post_url': normalize_url(url),
                    'post_url_original': url,
                    'post_number': post_number,
                    'platform': 'Instagram',
                    'author_name': self.fix_encoding(author),
                    'author_url': f"https://instagram.com/{author}",
                    'comment_text': self.fix_encoding(comment.get('text')),
                    'created_time': created_time,
                    'likes_count': comment.get('likesCount', 0),
                    'replies_count': 0,
                    'is_reply': False,
                    'parent_comment_id': None,
                    'created_time_raw': str(comment)
                }
                processed.append(comment_data)
        logger.info(f"Processed {len(processed)} Instagram comments.")
        return processed

    def _process_tiktok_results(self, items, url, post_number, campaign_info):
        processed = []
        for comment in items:
            author_id = comment.get('user', {}).get('uniqueId', '')
            comment_data = {
                **campaign_info,
                'post_url': normalize_url(url),
                'post_url_original': url,
                'post_number': post_number,
                'platform': 'TikTok',
                'author_name': self.fix_encoding(comment.get('user', {}).get('nickname')),
                'author_url': f"https://www.tiktok.com/@{author_id}",
                'comment_text': self.fix_encoding(comment.get('text')),
                'created_time': comment.get('createTime'),
                'likes_count': comment.get('diggCount', 0),
                'replies_count': comment.get('replyCommentTotal', 0),
                'is_reply': 'replyToId' in comment,
                'parent_comment_id': comment.get('replyToId'),
                'created_time_raw': str(comment)
            }
            processed.append(comment_data)
        logger.info(f"Processed {len(processed)} TikTok comments.")
        return processed


def normalize_url(url):
    """
    Normaliza una URL para comparación consistente.
    EXCEPCIÓN: Preserva feed_demo_ad para Facebook Ad Preview
    """
    if pd.isna(url) or url == '':
        return ''
    
    original_url = str(url).strip()
    url_lower = original_url.lower()
    
    # CASO ESPECIAL: Facebook Ad Preview con feed_demo_ad
    # Estos son anuncios diferentes y deben tratarse como URLs únicas
    if 'facebook.com' in url_lower and 'feed_demo_ad=' in url_lower:
        # Extraer solo el feed_demo_ad (es el identificador único)
        import re
        match = re.search(r'feed_demo_ad=(\d+)', url_lower)
        if match:
            ad_id = match.group(1)
            return f"https://www.facebook.com/ad_preview/{ad_id}"
    
    # Normalización estándar
    url = url_lower
    
    # Eliminar parámetros de query (excepto para casos especiales arriba)
    if '?' in url:
        url = url.split('?')[0]
    
    # Eliminar barra final
    if url.endswith('/'):
        url = url[:-1]
    
    # Eliminar fragmentos (#)
    if '#' in url:
        url = url.split('#')[0]
    
    return url


def create_post_registry_entry(url, platform, campaign_info):
    """Crea una entrada de registro para una pauta procesada sin comentarios"""
    return {
        **campaign_info,
        'post_url': normalize_url(url),
        'post_url_original': url,
        'post_number': None,
        'platform': platform,
        'author_name': None,
        'author_url': None,
        'comment_text': None,
        'created_time': None,
        'likes_count': 0,
        'replies_count': 0,
        'is_reply': False,
        'parent_comment_id': None,
        'created_time_raw': None
    }


def assign_consistent_post_numbers(df):
    """Asigna números de pauta consistentes basados en el orden de primera aparición"""
    if df.empty:
        return df
    
    df_with_numbers = df[df['post_number'].notna()].copy()
    existing_mapping = {}
    
    if not df_with_numbers.empty:
        for url in df_with_numbers['post_url'].unique():
            if pd.notna(url):
                url_numbers = df_with_numbers[df_with_numbers['post_url'] == url]['post_number']
                most_common = url_numbers.mode()
                if len(most_common) > 0:
                    existing_mapping[url] = int(most_common.iloc[0])
    
    all_urls = df['post_url'].dropna().unique()
    new_urls = [url for url in all_urls if url not in existing_mapping]
    
    if existing_mapping:
        next_number = max(existing_mapping.values()) + 1
    else:
        next_number = 1
    
    for url in new_urls:
        existing_mapping[url] = next_number
        next_number += 1
    
    df['post_number'] = df['post_url'].map(existing_mapping)
    return df


def load_existing_comments(filename):
    """Carga los comentarios existentes del archivo Excel"""
    if not Path(filename).exists():
        logger.info(f"No existing file found: {filename}. Will create new file.")
        return pd.DataFrame()
    
    try:
        df_existing = pd.read_excel(filename, sheet_name='Comentarios')
        logger.info(f"Loaded {len(df_existing)} existing rows from {filename}")
        
        # Normalizar cadenas vacías a NaN
        if 'comment_text' in df_existing.columns:
            df_existing['comment_text'] = df_existing['comment_text'].replace('', pd.NA)
            df_existing['comment_text'] = df_existing['comment_text'].apply(
                lambda x: pd.NA if isinstance(x, str) and x.strip() == '' else x
            )
        
        # Crear post_url_original si no existe
        if 'post_url_original' not in df_existing.columns:
            logger.info("Creating post_url_original from post_url")
            df_existing['post_url_original'] = df_existing['post_url'].copy()
        
        # Normalizar URLs
        if 'post_url' in df_existing.columns:
            df_existing['post_url'] = df_existing['post_url'].apply(normalize_url)
        
        return df_existing
    except Exception as e:
        logger.error(f"Error loading existing file: {e}")
        return pd.DataFrame()


def is_registry_entry(row):
    """Determina si una fila es una entrada de registro (pauta sin comentarios)"""
    if 'comment_text' not in row.index:
        return True
    comment = row['comment_text']
    if pd.isna(comment):
        return True
    if isinstance(comment, str) and comment.strip() == '':
        return True
    return False


def create_comment_id(row):
    """Crea un identificador único para cada comentario"""
    if is_registry_entry(row):
        post_url = row.get('post_url', '') if 'post_url' in row.index else ''
        normalized_url = normalize_url(post_url)
        if not normalized_url:
            platform = str(row.get('platform', 'unknown')) if 'platform' in row.index else 'unknown'
            return f"REGISTRY|NO_URL|{platform}"
        return f"REGISTRY|{normalized_url}"
    
    # Platform
    platform = str(row['platform']) if 'platform' in row.index and pd.notna(row['platform']) else ''
    platform = platform.strip().lower()
    
    # Author - CORREGIDO: manejar NaN apropiadamente
    author = ''
    if 'author_name' in row.index and pd.notna(row['author_name']):
        author = str(row['author_name']).strip().lower()
        # Si después de convertir es 'nan', tratarlo como vacío
        if author == 'nan':
            author = ''
    
    # Post URL - NUEVO: agregar URL al ID para mayor especificidad
    post_url = ''
    if 'post_url' in row.index and pd.notna(row['post_url']):
        post_url = str(row['post_url']).strip().lower()
    
    # Text
    text = ''
    if 'comment_text' in row.index and pd.notna(row['comment_text']):
        text = str(row['comment_text']).strip().lower()
        text = unicodedata.normalize('NFC', text)
    
    # Date - usar la fecha para diferenciar comentarios idénticos
    date_str = ''
    if 'created_time_processed' in row.index and pd.notna(row['created_time_processed']):
        date_str = str(row['created_time_processed'])
    elif 'created_time' in row.index and pd.notna(row['created_time']):
        date_str = str(row['created_time'])
    
    # MEJORADO: Incluir más información para evitar falsos duplicados
    # Especialmente importante para comentarios cortos o emojis
    unique_id = f"{platform}|{post_url}|{author}|{text}|{date_str}"
    return unique_id


def merge_comments(df_existing, df_new):
    """Combina comentarios existentes con nuevos, evitando duplicados"""
    if df_existing.empty:
        return df_new
    if df_new.empty:
        return df_existing
    
    logger.info(f"Merging: {len(df_existing)} existing + {len(df_new)} new rows")
    
    df_existing['_comment_id'] = df_existing.apply(create_comment_id, axis=1)
    df_new['_comment_id'] = df_new.apply(create_comment_id, axis=1)
    
    existing_ids = set(df_existing['_comment_id'])
    new_ids = set(df_new['_comment_id'])
    unique_new_ids = new_ids - existing_ids
    
    df_truly_new = df_new[df_new['_comment_id'].isin(unique_new_ids)].copy()
    logger.info(f"Adding {len(df_truly_new)} new unique entries")
    
    df_combined = pd.concat([df_existing, df_truly_new], ignore_index=True)
    df_combined = df_combined.drop(columns=['_comment_id'])
    
    return df_combined


def save_to_excel(df, filename):
    """Guarda el DataFrame en Excel"""
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Comentarios', index=False)
            if not df.empty and 'post_number' in df.columns:
                summary = df.groupby(['post_number', 'platform', 'post_url']).agg(
                    Total_Comentarios=('comment_text', 'count'),
                    Total_Likes=('likes_count', 'sum')
                ).reset_index()
                summary.to_excel(writer, sheet_name='Resumen_Posts', index=False)
        logger.info(f"Excel file saved successfully: {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving Excel file: {e}")
        return False


def process_datetime_columns(df):
    """Procesa las columnas de fecha/hora"""
    if 'created_time' not in df.columns:
        return df
    
    df['created_time_processed'] = pd.to_datetime(df['created_time'], errors='coerce', utc=True, unit='s')
    mask = df['created_time_processed'].isna()
    df.loc[mask, 'created_time_processed'] = pd.to_datetime(df.loc[mask, 'created_time'], errors='coerce', utc=True)
    
    if df['created_time_processed'].notna().any():
        df['created_time_processed'] = df['created_time_processed'].dt.tz_localize(None)
        df['fecha_comentario'] = df['created_time_processed'].dt.date
        df['hora_comentario'] = df['created_time_processed'].dt.time
    
    return df


def run_extraction():
    """Función principal que ejecuta todo el proceso de extracción"""
    logger.info("=" * 60)
    logger.info("--- STARTING COMMENT EXTRACTION PROCESS ---")
    logger.info("=" * 60)
    
    if not APIFY_TOKEN:
        logger.error("APIFY_TOKEN not found in environment variables. Aborting.")
        return

    valid_urls = [url.strip() for url in URLS_A_PROCESAR if url.strip()]
    logger.info(f"URLs to process: {len(valid_urls)}")
    
    if not valid_urls:
        logger.warning("No valid URLs to process. Exiting.")
        return

    filename = "Comentarios Campaña.xlsx"
    df_existing = load_existing_comments(filename)
    
    scraper = SocialMediaScraper(APIFY_TOKEN)
    all_comments = []
    post_counter = 0

    for url in valid_urls:
        post_counter += 1
        platform = scraper.detect_platform(url)
        comments = []
        
        if platform == 'facebook':
            comments = scraper.scrape_facebook_comments(url, campaign_info=CAMPAIGN_INFO, post_number=post_counter)
        elif platform == 'instagram':
            comments = scraper.scrape_instagram_comments(url, campaign_info=CAMPAIGN_INFO, post_number=post_counter)
        elif platform == 'tiktok':
            comments = scraper.scrape_tiktok_comments(url, campaign_info=CAMPAIGN_INFO, post_number=post_counter)
        
        if not comments:
            registry_entry = create_post_registry_entry(url, platform, CAMPAIGN_INFO)
            registry_entry['post_number'] = post_counter
            all_comments.append(registry_entry)
        else:
            all_comments.extend(comments)
        
        if not SOLO_PRIMER_POST and post_counter < len(valid_urls):
            pausa = random.uniform(60, 120)
            logger.info(f"Pausing for {pausa:.2f} seconds...")
            time.sleep(pausa)

    if not all_comments:
        if not df_existing.empty:
            save_to_excel(df_existing, filename)
        return

    df_new_comments = pd.DataFrame(all_comments)
    df_new_comments = process_datetime_columns(df_new_comments)
    
    # Normalizar datos
    if 'comment_text' in df_new_comments.columns:
        df_new_comments['comment_text'] = df_new_comments['comment_text'].replace('', pd.NA)
    if 'post_url' in df_new_comments.columns:
        df_new_comments['post_url'] = df_new_comments['post_url'].apply(normalize_url)
    
    df_combined = merge_comments(df_existing, df_new_comments)
    
    # Limpiar registry entries obsoletas
    is_registry_mask = df_combined.apply(is_registry_entry, axis=1)
    urls_with_comments = set(df_combined[~is_registry_mask]['post_url'].dropna().unique())
    
    if urls_with_comments:
        df_combined = df_combined[~(is_registry_mask & df_combined['post_url'].isin(urls_with_comments))].copy()
    
    df_combined = assign_consistent_post_numbers(df_combined)
    
    # Ordenar
    df_with_comments = df_combined[df_combined['comment_text'].notna()].copy()
    df_without_comments = df_combined[df_combined['comment_text'].isna()].copy()
    
    if not df_with_comments.empty and 'created_time_processed' in df_with_comments.columns:
        df_with_comments = df_with_comments.sort_values('created_time_processed', ascending=False)
    
    df_combined = pd.concat([df_with_comments, df_without_comments], ignore_index=True)
    
    # Organizar columnas
    final_columns = [
        'post_number', 'platform', 'campaign_name', 'post_url', 'post_url_original',
        'author_name', 'comment_text', 'created_time_processed', 
        'fecha_comentario', 'hora_comentario', 'likes_count', 
        'replies_count', 'is_reply', 'author_url', 'created_time_raw'
    ]
    existing_cols = [col for col in final_columns if col in df_combined.columns]
    df_combined = df_combined[existing_cols]

    save_to_excel(df_combined, filename)
    
    total_comments = df_combined['comment_text'].notna().sum()
    total_posts = df_combined['post_url'].nunique()
    
    logger.info("=" * 60)
    logger.info("--- EXTRACTION PROCESS FINISHED ---")
    logger.info(f"Total unique posts tracked: {total_posts}")
    logger.info(f"Total comments in file: {total_comments}")
    logger.info(f"File saved: {filename}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_extraction()
