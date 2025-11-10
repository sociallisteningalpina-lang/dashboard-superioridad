import pandas as pd
from apify_client import ApifyClient
import time
import re
import logging
import html
import unicodedata
import os

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
    "https://www.instagram.com/p/DQrnhboAK1O/",
    #NUEVOS
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
    #NUEVOS
    "https://www.facebook.com/reel/1177590664294662/",
    "https://www.facebook.com/reel/1370746317719068/",
    "https://www.facebook.com/reel/809881044994848/",
    "https://www.facebook.com/100064867445065/posts/1267673125404924/",

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
    "https://www.tiktok.com/@alpinacol/video/7554519618174389512?_r=1&_t=ZS-90Y3FEZWIfX",
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
    #NUEVOS
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
        # <-- CORRECCIÓN: Usando tu lista de campos de fecha más completa
        possible_date_fields = ['createdTime', 'timestamp', 'publishedTime', 'date', 'createdAt', 'publishedAt']
        for comment in items:
            # <-- CORRECCIÓN: Usando tu bucle for original para máxima compatibilidad
            created_time = None
            for field in possible_date_fields:
                if field in comment and comment[field]:
                    created_time = comment[field]
                    break
            comment_data = {**campaign_info, 'post_url': url, 'post_number': post_number, 'platform': 'Facebook', 'author_name': self.fix_encoding(comment.get('authorName')), 'author_url': comment.get('authorUrl'), 'comment_text': self.fix_encoding(comment.get('text')), 'created_time': created_time, 'likes_count': comment.get('likesCount', 0), 'replies_count': comment.get('repliesCount', 0), 'is_reply': False, 'parent_comment_id': None, 'created_time_raw': str(comment)}
            processed.append(comment_data)
        logger.info(f"Processed {len(processed)} Facebook comments.")
        return processed

    def _process_instagram_results(self, items, url, post_number, campaign_info):
        processed = []
        # <-- CORRECCIÓN: Usando tu lista de campos de fecha más completa
        possible_date_fields = ['timestamp', 'createdTime', 'publishedAt', 'date', 'createdAt', 'taken_at']
        for item in items:
            comments_list = item.get('comments', [item]) if item.get('comments') is not None else [item]
            for comment in comments_list:
                # <-- CORRECCIÓN: Usando tu bucle for original
                created_time = None
                for field in possible_date_fields:
                    if field in comment and comment[field]:
                        created_time = comment[field]
                        break
                author = comment.get('ownerUsername', '')
                comment_data = {**campaign_info, 'post_url': url, 'post_number': post_number, 'platform': 'Instagram', 'author_name': self.fix_encoding(author), 'author_url': f"https://instagram.com/{author}", 'comment_text': self.fix_encoding(comment.get('text')), 'created_time': created_time, 'likes_count': comment.get('likesCount', 0), 'replies_count': 0, 'is_reply': False, 'parent_comment_id': None, 'created_time_raw': str(comment)}
                processed.append(comment_data)
        logger.info(f"Processed {len(processed)} Instagram comments.")
        return processed

    def _process_tiktok_results(self, items, url, post_number, campaign_info):
        processed = []
        for comment in items:
            author_id = comment.get('user', {}).get('uniqueId', '')
            comment_data = {**campaign_info, 'post_url': url, 'post_number': post_number, 'platform': 'TikTok', 'author_name': self.fix_encoding(comment.get('user', {}).get('nickname')), 'author_url': f"https://www.tiktok.com/@{author_id}", 'comment_text': self.fix_encoding(comment.get('text')), 'created_time': comment.get('createTime'), 'likes_count': comment.get('diggCount', 0), 'replies_count': comment.get('replyCommentTotal', 0), 'is_reply': 'replyToId' in comment, 'parent_comment_id': comment.get('replyToId'), 'created_time_raw': str(comment)}
            processed.append(comment_data)
        logger.info(f"Processed {len(processed)} TikTok comments.")
        return processed

def save_to_excel(df, filename):
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Comentarios', index=False)
            if 'post_number' in df.columns:
                summary = df.groupby(['post_number', 'platform', 'post_url']).agg(Total_Comentarios=('comment_text', 'count'), Total_Likes=('likes_count', 'sum')).reset_index()
                summary.to_excel(writer, sheet_name='Resumen_Posts', index=False)
        logger.info(f"Excel file saved successfully: {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving Excel file: {e}")
        return False

def process_datetime_columns(df):
    if 'created_time' not in df.columns: return df
    logger.info("Processing datetime columns...")
    # Intenta convertir todo tipo de formatos (timestamps, ISO, etc.) a un datetime unificado
    df['created_time_processed'] = pd.to_datetime(df['created_time'], errors='coerce', utc=True, unit='s')
    mask = df['created_time_processed'].isna()
    df.loc[mask, 'created_time_processed'] = pd.to_datetime(df.loc[mask, 'created_time'], errors='coerce', utc=True)
    if df['created_time_processed'].notna().any():
        df['created_time_processed'] = df['created_time_processed'].dt.tz_localize(None)
        df['fecha_comentario'] = df['created_time_processed'].dt.date
        df['hora_comentario'] = df['created_time_processed'].dt.time
    return df

def run_extraction():
    logger.info("--- STARTING COMMENT EXTRACTION PROCESS ---")
    if not APIFY_TOKEN:
        logger.error("APIFY_TOKEN not found in environment variables. Aborting.")
        return

    valid_urls = [url.strip() for url in URLS_A_PROCESAR if url.strip()]
    if not valid_urls:
        logger.warning("No valid URLs to process. Exiting.")
        return

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
        else:
            logger.warning(f"Unknown platform for URL: {url}")
        
        all_comments.extend(comments)
        if not SOLO_PRIMER_POST and post_counter < len(valid_urls):
            logger.info("Pausing for 30 seconds between posts...")
            time.sleep(30)

    if not all_comments:
        logger.warning("No comments were extracted. Process finished.")
        return

    logger.info("--- PROCESSING FINAL RESULTS ---")
    df_comments = pd.DataFrame(all_comments)
    df_comments = process_datetime_columns(df_comments)
    
    final_columns = ['post_number', 'platform', 'campaign_name', 'post_url', 'author_name', 'comment_text', 'created_time_processed', 'fecha_comentario', 'hora_comentario', 'likes_count', 'replies_count', 'is_reply', 'author_url', 'created_time_raw']
    existing_cols = [col for col in final_columns if col in df_comments.columns]
    df_comments = df_comments[existing_cols]

    filename = "Comentarios Campaña.xlsx"
    save_to_excel(df_comments, filename)
    logger.info("--- EXTRACTION PROCESS FINISHED ---")

if __name__ == "__main__":
    run_extraction()
















