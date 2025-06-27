#!/usr/bin/env python3
"""
東京シティ競馬サイトの詳細調査スクリプト
見つかったURLを深く調査し、レース結果へのアクセス方法を探る
"""
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import json
from urllib.parse import urljoin, urlparse
import re

class TokyoCityDeepInvestigator:
    def __init__(self):
        self.base_url = "https://www.tokyocitykeiba.com/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 調査対象URL
        self.target_urls = {
            'calendar': 'https://www.tokyocitykeiba.com/race/calendar/',
            'schedule': 'https://www.tokyocitykeiba.com/race/schedule/',
            'race_main': 'https://www.tokyocitykeiba.com/race/',
            'grade_race': 'https://www.tokyocitykeiba.com/race/grade_race/'
        }
    
    def investigate_calendar(self):
        """開催カレンダーページを詳細調査"""
        print("=" * 60)
        print("開催カレンダーの詳細調査")
        print("=" * 60)
        
        try:
            response = self.session.get(self.target_urls['calendar'])
            soup = BeautifulSoup(response.content, 'html.parser')
            
            print(f"ステータス: {response.status_code}")
            
            # カレンダー要素を探す
            calendar_elements = soup.find_all(['div', 'table', 'section'], 
                                            class_=lambda x: x and ('calendar' in str(x).lower() or 'schedule' in str(x).lower()) if x else False)
            
            print(f"\nカレンダー関連要素: {len(calendar_elements)}個")
            
            # 日付リンクを探す
            date_links = []
            for link in soup.find_all('a', href=True):
                text = link.text.strip()
                href = link.get('href', '')
                
                # 日付パターンを探す
                if re.search(r'\d{1,2}[月/]\d{1,2}', text) or re.search(r'開催', text):
                    date_links.append({
                        'text': text,
                        'href': urljoin(self.target_urls['calendar'], href)
                    })
            
            if date_links:
                print(f"\n✅ {len(date_links)}個の日付関連リンクを発見:")
                for i, link in enumerate(date_links[:10]):  # 最初の10個
                    print(f"{i+1}. {link['text']}: {link['href']}")
                    
                # 最初のリンクを詳細調査
                if date_links:
                    print(f"\n### 最初のリンクを調査: {date_links[0]['href']}")
                    self.follow_link(date_links[0]['href'])
            
            # スクリプトタグ内のデータを探す
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and ('calendar' in script.string.lower() or 'schedule' in script.string.lower()):
                    print("\n✅ カレンダー関連のJavaScriptデータを発見")
                    # JSON形式のデータを探す
                    json_matches = re.findall(r'\{[^}]+\}', script.string)
                    if json_matches:
                        print(f"  JSONオブジェクト数: {len(json_matches)}")
                        
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    def investigate_race_main(self):
        """レースメインページを調査"""
        print("\n" + "=" * 60)
        print("レースメインページの詳細調査")
        print("=" * 60)
        
        try:
            response = self.session.get(self.target_urls['race_main'])
            soup = BeautifulSoup(response.content, 'html.parser')
            
            print(f"ステータス: {response.status_code}")
            
            # レース関連のリンクを全て収集
            race_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.text.strip()
                
                # レース関連のキーワード
                if any(keyword in text for keyword in ['レース', '出走表', '結果', '成績', 'オッズ']):
                    full_url = urljoin(self.target_urls['race_main'], href)
                    race_links.append({
                        'text': text,
                        'href': full_url
                    })
            
            if race_links:
                print(f"\n✅ {len(race_links)}個のレース関連リンクを発見:")
                # 重複を除去
                unique_links = []
                seen_urls = set()
                for link in race_links:
                    if link['href'] not in seen_urls:
                        seen_urls.add(link['href'])
                        unique_links.append(link)
                
                for i, link in enumerate(unique_links[:15]):
                    print(f"{i+1}. {link['text']}: {link['href']}")
            
            # フォーム要素を探す（検索機能など）
            forms = soup.find_all('form')
            if forms:
                print(f"\n✅ {len(forms)}個のフォームを発見")
                for i, form in enumerate(forms):
                    action = form.get('action', '')
                    method = form.get('method', 'get')
                    print(f"  フォーム{i+1}: action={action}, method={method}")
                    
                    # input要素を確認
                    inputs = form.find_all('input')
                    if inputs:
                        print(f"    入力フィールド:")
                        for inp in inputs[:5]:
                            print(f"      - {inp.get('name', 'no-name')}: {inp.get('type', 'text')}")
                            
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    def investigate_nankan_keiba(self):
        """南関競馬サイトを調査"""
        print("\n" + "=" * 60)
        print("南関競馬サイトの調査")
        print("=" * 60)
        
        nankan_url = "http://www.nankankeiba.com/program/00000000000000.do"
        
        try:
            response = self.session.get(nankan_url, timeout=10)
            print(f"ステータス: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 大井競馬関連の情報を探す
                if '大井' in soup.text:
                    print("✅ 大井競馬の情報が含まれています")
                    
                    # プログラムやレース結果のリンクを探す
                    links = soup.find_all('a', href=True)
                    oi_links = []
                    
                    for link in links:
                        text = link.text.strip()
                        href = link.get('href', '')
                        
                        if '大井' in text or 'TCK' in text:
                            oi_links.append({
                                'text': text,
                                'href': urljoin(nankan_url, href)
                            })
                    
                    if oi_links:
                        print(f"\n大井競馬関連リンク: {len(oi_links)}個")
                        for i, link in enumerate(oi_links[:10]):
                            print(f"{i+1}. {link['text']}: {link['href']}")
                            
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    def follow_link(self, url):
        """リンクを追跡して詳細を調査"""
        try:
            time.sleep(1)  # 礼儀正しく待機
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # レース結果テーブルを探す
                tables = soup.find_all('table')
                if tables:
                    print(f"  → テーブル数: {len(tables)}")
                    
                    for i, table in enumerate(tables[:2]):
                        # ヘッダーを確認
                        headers = table.find_all('th')
                        if headers:
                            header_texts = [h.text.strip() for h in headers[:8]]
                            print(f"    テーブル{i+1}のヘッダー: {header_texts}")
                            
                            # レース結果っぽいキーワードを探す
                            result_keywords = ['着順', '馬番', '馬名', 'タイム', 'オッズ', '騎手', '調教師']
                            if any(keyword in str(header_texts) for keyword in result_keywords):
                                print(f"    ✅ レース結果テーブルの可能性が高い！")
                
                # レース詳細リンクを探す
                race_detail_links = []
                for link in soup.find_all('a', href=True):
                    text = link.text.strip()
                    if re.match(r'\d+R', text) or 'レース' in text:
                        race_detail_links.append({
                            'text': text,
                            'href': urljoin(url, link.get('href'))
                        })
                
                if race_detail_links:
                    print(f"  → レース詳細リンク: {len(race_detail_links)}個")
                    for link in race_detail_links[:3]:
                        print(f"    - {link['text']}: {link['href']}")
                        
            else:
                print(f"  → アクセス失敗: {response.status_code}")
                
        except Exception as e:
            print(f"  → エラー: {type(e).__name__}")
    
    def check_ajax_endpoints(self):
        """Ajax APIエンドポイントを調査"""
        print("\n" + "=" * 60)
        print("Ajax APIエンドポイントの調査")
        print("=" * 60)
        
        # 可能性のあるAjaxエンドポイント
        ajax_endpoints = [
            '/ajax/race',
            '/ajax/result',
            '/ajax/schedule',
            '/ajax/calendar',
            '/ajax/program',
            '/wp-admin/admin-ajax.php'  # WordPressの標準Ajax
        ]
        
        for endpoint in ajax_endpoints:
            url = urljoin(self.base_url, endpoint)
            print(f"\n試行中: {url}")
            
            try:
                # GETリクエスト
                response = self.session.get(url, timeout=5)
                print(f"  GET: {response.status_code}")
                
                # POSTリクエスト（WordPressのajaxはPOSTが一般的）
                if 'admin-ajax.php' in endpoint:
                    # 一般的なWordPress Ajaxアクション
                    test_actions = ['get_race_data', 'load_race_results', 'fetch_schedule']
                    
                    for action in test_actions:
                        data = {'action': action}
                        response = self.session.post(url, data=data, timeout=5)
                        print(f"  POST (action={action}): {response.status_code}")
                        
                        if response.status_code == 200 and response.text.strip() != '0':
                            print(f"    ✅ 有効なレスポンス: {response.text[:100]}...")
                            
            except Exception as e:
                print(f"  ❌ エラー: {type(e).__name__}")
            
            time.sleep(0.5)
    
    def investigate_schedule_detail(self):
        """スケジュールページの詳細調査"""
        print("\n" + "=" * 60)
        print("スケジュールページの詳細調査")
        print("=" * 60)
        
        try:
            response = self.session.get(self.target_urls['schedule'])
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # テーブル構造を詳しく分析
            tables = soup.find_all('table')
            for i, table in enumerate(tables):
                print(f"\nテーブル{i+1}の分析:")
                
                # キャプションを確認
                caption = table.find('caption')
                if caption:
                    print(f"  キャプション: {caption.text.strip()}")
                
                # 行を分析
                rows = table.find_all('tr')
                print(f"  行数: {len(rows)}")
                
                if rows:
                    # 最初の数行を詳細に分析
                    for j, row in enumerate(rows[:5]):
                        cells = row.find_all(['td', 'th'])
                        cell_texts = [cell.text.strip() for cell in cells]
                        print(f"    行{j+1}: {cell_texts}")
                        
                        # リンクを確認
                        links = row.find_all('a', href=True)
                        if links:
                            for link in links:
                                print(f"      → リンク: {link.text.strip()} => {link.get('href')}")
                                
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    def generate_findings(self):
        """調査結果をまとめる"""
        print("\n" + "=" * 60)
        print("調査結果のまとめ")
        print("=" * 60)
        
        print("""
### 主な発見:
1. 東京シティ競馬サイトはWordPressベース
2. レース情報は以下の構造：
   - /race/calendar/ - 開催カレンダー
   - /race/schedule/ - 詳細スケジュール
   - 個別のレース結果は別システムの可能性
3. 南関競馬サイトとの連携がある

### データ取得戦略:
1. まず開催カレンダーから開催日を取得
2. 各開催日のレース情報へアクセス
3. 南関競馬サイトも併用する可能性
4. WordPress AjaxAPIの活用を検討

### 次のアクション:
1. 実際の開催日でのアクセステスト
2. 南関競馬サイトの詳細調査
3. プロトタイプスクレイパーの作成
        """)

def main():
    print("東京シティ競馬サイトの詳細調査を開始します...")
    print("=" * 60)
    
    investigator = TokyoCityDeepInvestigator()
    
    # 詳細調査実行
    investigator.investigate_calendar()
    investigator.investigate_race_main()
    investigator.investigate_schedule_detail()
    investigator.investigate_nankan_keiba()
    investigator.check_ajax_endpoints()
    investigator.generate_findings()
    
    print("\n詳細調査完了！")

if __name__ == "__main__":
    main()