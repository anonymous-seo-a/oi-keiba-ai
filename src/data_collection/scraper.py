"""
大井競馬データスクレイピング
"""
import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import urljoin
import re

from config.settings import NETKEIBA_BASE_URL, OI_COURSE_CODE, SCRAPING_DELAY, USER_AGENT
from src.data_collection.database import OiKeibaDatabase
from src.utils.logger import setup_logger

class OiKeibaScraper:
    def __init__(self, db=None):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.db = db or OiKeibaDatabase()
        self.logger = setup_logger(__name__)
        
    def get_race_list(self, start_date, end_date):
        """指定期間の大井競馬レース一覧を取得"""
        race_list = []
        current_date = start_date
        
        while current_date <= end_date:
            self.logger.info(f"取得中: {current_date.strftime('%Y-%m-%d')}")
            
            # 大井競馬場のレース一覧URL
            url = f"{NETKEIBA_BASE_URL}/race/list/{OI_COURSE_CODE}{current_date.strftime('%Y%m%d')}/"
            
            try:
                response = self.session.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # レースリンクを取得
                race_links = soup.find_all('a', href=re.compile(r'/race/\d+/'))
                
                for link in race_links:
                    race_url = urljoin(NETKEIBA_BASE_URL, link['href'])
                    race_id = link['href'].split('/')[-2]
                    race_name = link.text.strip()
                    
                    race_list.append({
                        'race_id': race_id,
                        'race_name': race_name,
                        'race_url': race_url,
                        'race_date': current_date.strftime('%Y-%m-%d')
                    })
                
                time.sleep(SCRAPING_DELAY)
                
            except requests.RequestException as e:
                self.logger.error(f"エラー: {current_date.strftime('%Y-%m-%d')} - {e}")
            
            current_date += timedelta(days=1)
        
        return race_list
    
    def scrape_race_result(self, race_id, race_date):
        """個別レースの結果を取得"""
        url = f"{NETKEIBA_BASE_URL}/race/{race_id}/"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # レース情報を取得
            race_info = self.extract_race_info(soup)
            
            # 着順結果を取得
            results_table = soup.find('table', class_='race_table_01')
            if not results_table:
                return None
            
            results = []
            rows = results_table.find_all('tr')[1:]  # ヘッダーを除く
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 8:
                    result = {
                        'race_id': race_id,
                        'race_date': race_date,
                        'race_name': race_info.get('race_name', ''),
                        'course_length': race_info.get('course_length', 0),
                        'course_type': race_info.get('course_type', ''),
                        'weather': race_info.get('weather', ''),
                        'track_condition': race_info.get('track_condition', ''),
                        'finish_position': self.safe_int(cells[0].text.strip()),
                        'horse_name': cells[3].text.strip(),
                        'jockey_name': cells[6].text.strip(),
                        'trainer_name': cells[7].text.strip() if len(cells) > 7 else '',
                        'horse_weight': self.extract_horse_weight(cells[4].text.strip()),
                        'odds': self.safe_float(cells[5].text.strip()),
                        'popularity': self.safe_int(cells[2].text.strip()),
                        'time_result': cells[8].text.strip() if len(cells) > 8 else '',
                        'margin': cells[9].text.strip() if len(cells) > 9 else ''
                    }
                    results.append(result)
            
            return results
            
        except requests.RequestException as e:
            self.logger.error(f"レース結果取得エラー: {race_id} - {e}")
            return None
    
    def extract_race_info(self, soup):
        """レース情報を抽出"""
        race_info = {}
        
        # レース名
        race_name_elem = soup.find('h1')
        if race_name_elem:
            race_info['race_name'] = race_name_elem.text.strip()
        
        # コース情報
        course_info = soup.find('p', class_='racedata')
        if course_info:
            course_text = course_info.text
            
            # 距離を抽出
            distance_match = re.search(r'(\d+)m', course_text)
            if distance_match:
                race_info['course_length'] = int(distance_match.group(1))
            
            # コース種別
            if 'ダ' in course_text:
                race_info['course_type'] = 'ダート'
            elif '芝' in course_text:
                race_info['course_type'] = '芝'
            
            # 天候・馬場状態
            weather_match = re.search(r'天候:(\w+)', course_text)
            if weather_match:
                race_info['weather'] = weather_match.group(1)
            
            condition_match = re.search(r'馬場:(\w+)', course_text)
            if condition_match:
                race_info['track_condition'] = condition_match.group(1)
        
        return race_info
    
    def safe_int(self, value):
        """安全な整数変換"""
        try:
            return int(re.sub(r'[^\d]', '', value))
        except (ValueError, AttributeError):
            return 0
    
    def safe_float(self, value):
        """安全な浮動小数点変換"""
        try:
            return float(re.sub(r'[^\d.]', '', value))
        except (ValueError, AttributeError):
            return 0.0
    
    def extract_horse_weight(self, weight_text):
        """馬体重を抽出"""
        weight_match = re.search(r'(\d+)', weight_text)
        return int(weight_match.group(1)) if weight_match else 0
    
    def run_scraping(self, months_back=36):
        """スクレイピング実行"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        self.logger.info(f"データ取得開始: {start_date.strftime('%Y-%m-%d')} から {end_date.strftime('%Y-%m-%d')}")
        
        # レース一覧を取得
        race_list = self.get_race_list(start_date, end_date)
        self.logger.info(f"取得対象レース数: {len(race_list)}")
        
        # 各レースの結果を取得
        for i, race in enumerate(race_list):
            self.logger.info(f"進捗: {i+1}/{len(race_list)} - {race['race_name']}")
            
            results = self.scrape_race_result(race['race_id'], race['race_date'])
            if results:
                self.db.save_race_results(results)
                self.logger.info(f"保存完了: {len(results)}件")
            
            time.sleep(SCRAPING_DELAY)
        
        self.logger.info("データ取得完了！")
