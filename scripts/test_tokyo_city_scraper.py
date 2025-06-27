#!/usr/bin/env python3
"""
東京シティ競馬（大井競馬）スクレイパーのプロトタイプ
東京シティ競馬サイトと南関競馬サイトを組み合わせてデータを取得
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin
import pandas as pd
from typing import List, Dict, Optional

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class TokyoCityScraper:
    def __init__(self):
        self.tokyo_city_base = "https://www.tokyocitykeiba.com/"
        self.nankan_base = "http://www.nankankeiba.com/"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 大井競馬場のコード
        self.OI_TRACK_CODE = "20"
    
    def get_race_schedule(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        東京シティ競馬サイトから開催スケジュールを取得
        """
        logger.info(f"開催スケジュールを取得: {start_date.strftime('%Y-%m-%d')} 〜 {end_date.strftime('%Y-%m-%d')}")
        
        schedules = []
        
        try:
            # レースメインページから情報を取得
            url = urljoin(self.tokyo_city_base, "race/")
            response = self.session.get(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # レース結果リンクを探す（南関競馬サイトへのリンク）
                result_links = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if 'nankankeiba.com/result/' in href:
                        result_links.append(href)
                
                logger.info(f"見つかったレース結果リンク: {len(result_links)}個")
                
                # 各リンクから日付とレース情報を抽出
                for link in result_links:
                    match = re.search(r'/result/(\d{8})(\d+)\.do', link)
                    if match:
                        date_str = match.group(1)
                        code_str = match.group(2)
                        
                        # 日付を解析
                        race_date = datetime.strptime(date_str, '%Y%m%d')
                        
                        # 期間内のレースのみ
                        if start_date <= race_date <= end_date:
                            # コード部分を解析
                            if len(code_str) >= 8 and code_str[:2] == self.OI_TRACK_CODE:
                                kaisai = code_str[2:4]
                                day = code_str[4:6]
                                race_num = code_str[6:8]
                                
                                schedule = {
                                    'date': race_date,
                                    'kaisai': int(kaisai),
                                    'day': int(day),
                                    'race_num': int(race_num),
                                    'url': link
                                }
                                schedules.append(schedule)
                
                # カレンダーページも確認
                calendar_url = urljoin(self.tokyo_city_base, "race/calendar/")
                response = self.session.get(calendar_url)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    # 追加の開催情報があれば取得
                    # （実装は実際のHTML構造に応じて調整）
                    
            else:
                logger.error(f"スケジュール取得失敗: {response.status_code}")
                
        except Exception as e:
            logger.error(f"スケジュール取得エラー: {e}")
        
        # 日付順にソート
        schedules.sort(key=lambda x: (x['date'], x['race_num']))
        
        return schedules
    
    def scrape_race_result(self, result_url: str) -> Optional[List[Dict]]:
        """
        南関競馬サイトからレース結果を取得
        """
        logger.info(f"レース結果を取得: {result_url}")
        
        try:
            response = self.session.get(result_url)
            
            if response.status_code == 200:
                # Shift-JISでデコード
                soup = BeautifulSoup(response.content, 'html.parser', from_encoding='shift_jis')
                
                # レース情報を取得
                race_info = self._extract_race_info(soup, result_url)
                
                # 結果テーブルを探す
                result_table = None
                tables = soup.find_all('table', class_='nk23_c-table01__table')
                
                for table in tables:
                    headers = [th.text.strip() for th in table.find_all('th')]
                    # メインの結果テーブルを識別
                    if '着' in headers and '馬名' in headers and 'タイム' in headers:
                        result_table = table
                        break
                
                if result_table:
                    results = self._parse_result_table(result_table, race_info)
                    logger.info(f"取得した結果: {len(results)}件")
                    return results
                else:
                    logger.warning("結果テーブルが見つかりません")
                    
            else:
                logger.error(f"アクセス失敗: {response.status_code}")
                
        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            
        return None
    
    def _extract_race_info(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        レース基本情報を抽出
        """
        # URLから日付とレース番号を抽出
        match = re.search(r'/result/(\d{8})(\d{2})(\d{2})(\d{2})(\d{2})\.do', url)
        
        race_info = {
            'race_date': '',
            'kaisai': '',
            'day': '',
            'race_num': '',
            'race_name': '',
            'course_length': '',
            'course_type': 'ダート',  # 大井は基本ダート
            'weather': '',
            'track_condition': ''
        }
        
        if match:
            date_str = match.group(1)
            race_info['race_date'] = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
            race_info['kaisai'] = f"第{int(match.group(2))}回"
            race_info['day'] = f"{int(match.group(3))}日目"
            race_info['race_num'] = f"{int(match.group(4))}R"
        
        # ページからレース名を取得
        # （実際のHTML構造に応じて調整が必要）
        h1_tags = soup.find_all('h1')
        h2_tags = soup.find_all('h2')
        
        for tag in h1_tags + h2_tags:
            text = tag.text.strip()
            if 'レース' in text or 'R' in text:
                race_info['race_name'] = text
                break
        
        # コース情報を取得
        for link in soup.find_all('a', href=True):
            text = link.text.strip()
            match = re.match(r'ダ(\d+)m', text)
            if match:
                race_info['course_length'] = match.group(1)
                break
        
        return race_info
    
    def _parse_result_table(self, table, race_info: Dict) -> List[Dict]:
        """
        結果テーブルをパース
        """
        results = []
        
        # ヘッダーを取得
        headers = []
        header_row = table.find('tr')
        if header_row:
            headers = [th.text.strip() for th in header_row.find_all('th')]
        
        # データ行を処理
        rows = table.find_all('tr')[1:]  # ヘッダーをスキップ
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 10:  # 最低限必要なカラム数
                
                # インデックスマッピング（実際のテーブル構造に応じて調整）
                try:
                    result = {
                        'race_id': f"{race_info['race_date'].replace('-', '')}{race_info['race_num'].replace('R', '')}",
                        'race_date': race_info['race_date'],
                        'race_name': race_info['race_name'],
                        'race_num': race_info['race_num'],
                        'kaisai': race_info['kaisai'],
                        'day': race_info['day'],
                        'course_length': race_info['course_length'],
                        'course_type': race_info['course_type'],
                        'weather': race_info['weather'],
                        'track_condition': race_info['track_condition'],
                        
                        # レース結果データ
                        'finish_position': cells[0].text.strip(),
                        'frame_number': cells[1].text.strip(),
                        'horse_number': cells[2].text.strip(),
                        'horse_name': cells[3].text.strip().replace('[J]', ''),  # JRA転入馬マーク除去
                        'sex_age': cells[4].text.strip(),
                        'weight_carried': cells[5].text.strip().replace('kg', ''),
                        'horse_weight': cells[6].text.strip().replace('kg', ''),
                        'weight_change': cells[7].text.strip(),
                        'jockey_name': cells[8].text.strip().replace('[J]', ''),
                        'trainer_name': cells[9].text.strip(),
                        'time': cells[10].text.strip() if len(cells) > 10 else '',
                        'margin': cells[11].text.strip() if len(cells) > 11 else '',
                        'last_3f': cells[12].text.strip() if len(cells) > 12 else '',
                        'corner_position': cells[13].text.strip() if len(cells) > 13 else '',
                        'popularity': cells[14].text.strip() if len(cells) > 14 else '',
                        
                        # オッズは別テーブルから取得する必要があるかも
                        'odds': '',
                        'prize_money': ''
                    }
                    
                    # 数値データの整形
                    if result['finish_position'].isdigit():
                        results.append(result)
                        
                except Exception as e:
                    logger.warning(f"行のパースエラー: {e}")
                    continue
        
        return results
    
    def test_single_race(self):
        """
        単一レースでテスト
        """
        test_url = "http://www.nankankeiba.com/result/2025012920160311.do"
        logger.info(f"テストURL: {test_url}")
        
        results = self.scrape_race_result(test_url)
        
        if results:
            logger.info(f"成功！ {len(results)}件の結果を取得")
            
            # 最初の3件を表示
            for i, result in enumerate(results[:3]):
                logger.info(f"\n{i+1}着:")
                logger.info(f"  馬名: {result['horse_name']}")
                logger.info(f"  騎手: {result['jockey_name']}")
                logger.info(f"  タイム: {result['time']}")
                logger.info(f"  人気: {result['popularity']}")
            
            # DataFrameとして表示
            df = pd.DataFrame(results)
            print("\n結果のDataFrame:")
            print(df[['finish_position', 'horse_name', 'jockey_name', 'time', 'popularity']].head())
            
            return True
        else:
            logger.error("テスト失敗")
            return False
    
    def run_date_range(self, start_date: datetime, end_date: datetime):
        """
        指定期間のレースデータを取得
        """
        # スケジュールを取得
        schedules = self.get_race_schedule(start_date, end_date)
        logger.info(f"取得対象レース: {len(schedules)}件")
        
        all_results = []
        
        for schedule in schedules[:5]:  # テストとして最初の5レースのみ
            logger.info(f"\n処理中: {schedule['date'].strftime('%Y-%m-%d')} {schedule['race_num']}R")
            
            results = self.scrape_race_result(schedule['url'])
            if results:
                all_results.extend(results)
            
            # サーバーに配慮
            time.sleep(1)
        
        logger.info(f"\n合計取得結果: {len(all_results)}件")
        return all_results

def main():
    """メイン処理"""
    logger.info("東京シティ競馬スクレイパーのテスト開始")
    
    scraper = TokyoCityScraper()
    
    # 単一レースのテスト
    logger.info("\n=== 単一レーステスト ===")
    if scraper.test_single_race():
        logger.info("✅ 単一レーステスト成功！")
        
        # 期間指定のテスト
        logger.info("\n=== 期間指定テスト ===")
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)
        
        results = scraper.run_date_range(start_date, end_date)
        
        if results:
            logger.info("✅ 期間指定テスト成功！")
            
            # CSVに保存
            df = pd.DataFrame(results)
            df.to_csv('test_results.csv', index=False, encoding='utf-8-sig')
            logger.info("結果をtest_results.csvに保存しました")

if __name__ == "__main__":
    main()
