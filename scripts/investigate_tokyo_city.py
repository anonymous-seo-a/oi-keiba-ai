#!/usr/bin/env python3
"""
東京シティ競馬公式サイトの構造を調査するスクリプト
"""
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import json
from urllib.parse import urljoin

class TokyoCityInvestigator:
    def __init__(self):
        self.base_url = "https://www.tokyocitykeiba.com/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def check_robots_txt(self):
        """robots.txtを確認"""
        print("=" * 60)
        print("robots.txtの確認")
        print("=" * 60)
        
        try:
            url = urljoin(self.base_url, "robots.txt")
            response = self.session.get(url)
            
            if response.status_code == 200:
                print("✅ robots.txt が見つかりました:")
                print(response.text)
            else:
                print(f"❌ robots.txt が見つかりません (ステータス: {response.status_code})")
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    def investigate_homepage(self):
        """トップページの構造を調査"""
        print("\n" + "=" * 60)
        print("トップページの調査")
        print("=" * 60)
        
        try:
            response = self.session.get(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            print(f"ステータスコード: {response.status_code}")
            print(f"ページタイトル: {soup.title.text if soup.title else 'なし'}")
            
            # ナビゲーションメニューを探す
            print("\n### ナビゲーションリンク:")
            nav_links = soup.find_all('a', href=True)[:20]  # 最初の20個
            for link in nav_links:
                href = link.get('href', '')
                text = link.text.strip()
                if text and ('レース' in text or '結果' in text or '出走' in text or 'データ' in text):
                    print(f"- {text}: {urljoin(self.base_url, href)}")
            
            # 開催情報を探す
            print("\n### 開催情報の要素:")
            for tag in ['div', 'section', 'article']:
                elements = soup.find_all(tag, class_=lambda x: x and ('race' in x.lower() or 'schedule' in x.lower() or 'kaisai' in x.lower()) if x else False)
                for elem in elements[:5]:
                    print(f"- {tag}.{elem.get('class', [''])[0]}: {elem.text.strip()[:50]}...")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    def find_race_pages(self):
        """レース関連ページを探す"""
        print("\n" + "=" * 60)
        print("レース関連ページの探索")
        print("=" * 60)
        
        # 一般的なレース関連URLパターン
        patterns = [
            "race/",
            "result/",
            "results/",
            "data/",
            "past/",
            "schedule/",
            "calendar/",
            "racelist/",
            "racedata/",
            "program/",
            "shutuba/",
            "odds/"
        ]
        
        found_urls = set()
        
        try:
            response = self.session.get(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # すべてのリンクを確認
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                full_url = urljoin(self.base_url, href)
                
                # パターンマッチング
                for pattern in patterns:
                    if pattern in href.lower():
                        found_urls.add((link.text.strip(), full_url))
                        break
            
            # 結果を表示
            if found_urls:
                print("✅ レース関連と思われるページが見つかりました:")
                for text, url in sorted(found_urls):
                    if text:
                        print(f"- {text}: {url}")
            else:
                print("❌ レース関連ページが見つかりませんでした")
                
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    def test_specific_urls(self):
        """特定のURLパターンをテスト"""
        print("\n" + "=" * 60)
        print("特定URLパターンのテスト")
        print("=" * 60)
        
        # テストするURL
        test_urls = [
            "race/result/",
            "race/2025/06/",
            "data/race/",
            "schedule/",
            "program/",
            "past/",
            "results/2025/06/",
            "race/past/",
            "race/schedule/"
        ]
        
        for path in test_urls:
            url = urljoin(self.base_url, path)
            print(f"\n試行中: {url}")
            
            try:
                response = self.session.get(url, timeout=10)
                print(f"ステータス: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # ページ内容を確認
                    if 'レース' in soup.text or 'race' in soup.text.lower():
                        print("✅ レース関連コンテンツが含まれています")
                        
                        # テーブルを探す
                        tables = soup.find_all('table')
                        if tables:
                            print(f"  - テーブル数: {len(tables)}")
                            
                        # レース結果のようなデータを探す
                        race_elements = soup.find_all(['div', 'tr', 'section'], 
                                                    class_=lambda x: x and ('race' in str(x).lower() or 'result' in str(x).lower()) if x else False)
                        if race_elements:
                            print(f"  - レース関連要素: {len(race_elements)}個")
                    else:
                        print("❌ レース関連コンテンツが見つかりません")
                        
            except requests.exceptions.RequestException as e:
                print(f"❌ アクセスエラー: {type(e).__name__}")
            
            time.sleep(1)  # サーバーに負荷をかけない
    
    def investigate_date_based_urls(self):
        """日付ベースのURLを調査"""
        print("\n" + "=" * 60)
        print("日付ベースURLの調査")
        print("=" * 60)
        
        # 最近の日付でテスト
        test_date = datetime(2025, 6, 25)
        
        # 様々な日付フォーマット
        date_formats = [
            test_date.strftime("%Y%m%d"),      # 20250625
            test_date.strftime("%Y/%m/%d"),    # 2025/06/25
            test_date.strftime("%Y-%m-%d"),    # 2025-06-25
            test_date.strftime("%Y/%m%d"),     # 2025/0625
            test_date.strftime("%Y%m/%d"),     # 202506/25
        ]
        
        base_paths = ["race/", "result/", "data/", "schedule/", "program/"]
        
        for base_path in base_paths:
            for date_format in date_formats:
                url = urljoin(self.base_url, f"{base_path}{date_format}")
                print(f"\n試行中: {url}")
                
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        print(f"✅ アクセス成功!")
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # レース情報を探す
                        if 'レース' in soup.text or '大井' in soup.text:
                            print("  - レース情報が含まれています！")
                            
                            # より詳細な調査
                            self.analyze_page_structure(soup, url)
                            return url  # 成功したURLを返す
                    else:
                        print(f"❌ ステータス: {response.status_code}")
                        
                except Exception as e:
                    print(f"❌ エラー: {type(e).__name__}")
                
                time.sleep(1)
    
    def analyze_page_structure(self, soup, url):
        """ページの詳細構造を分析"""
        print("\n### ページ構造の詳細分析:")
        
        # レース一覧を探す
        race_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.text.strip()
            
            if ('R' in text and text[0:2].isdigit()) or ('レース' in text):
                race_links.append({
                    'text': text,
                    'href': urljoin(url, href)
                })
        
        if race_links:
            print(f"✅ {len(race_links)}個のレースリンクを発見:")
            for i, link in enumerate(race_links[:5]):  # 最初の5つを表示
                print(f"  {i+1}. {link['text']}: {link['href']}")
        
        # テーブル構造を確認
        tables = soup.find_all('table')
        if tables:
            print(f"\n✅ {len(tables)}個のテーブルを発見")
            for i, table in enumerate(tables[:2]):  # 最初の2つを分析
                print(f"\n  テーブル{i+1}:")
                
                # ヘッダーを確認
                headers = table.find_all('th')
                if headers:
                    print(f"  ヘッダー: {[h.text.strip() for h in headers[:5]]}")
                
                # 行数を確認
                rows = table.find_all('tr')
                print(f"  行数: {len(rows)}")
    
    def search_api_endpoints(self):
        """APIエンドポイントを探す"""
        print("\n" + "=" * 60)
        print("APIエンドポイントの探索")
        print("=" * 60)
        
        try:
            response = self.session.get(self.base_url)
            content = response.text
            
            # JavaScriptファイルを探す
            import re
            js_files = re.findall(r'<script[^>]+src=["\']([^"\']+\.js)["\']', content)
            
            print(f"JavaScriptファイル数: {len(js_files)}")
            
            # APIパターンを探す
            api_patterns = [
                r'api/',
                r'/ajax/',
                r'\.json',
                r'data/',
                r'fetch\(["\']([^"\']+)["\']',
                r'axios\.[get|post]\(["\']([^"\']+)["\']'
            ]
            
            for pattern in api_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    print(f"\n✅ パターン '{pattern}' にマッチ:")
                    for match in matches[:3]:
                        print(f"  - {match}")
                        
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    def generate_report(self):
        """調査結果のレポートを生成"""
        print("\n" + "=" * 60)
        print("調査結果サマリー")
        print("=" * 60)
        
        print("""
### 推奨される次のステップ:
1. 見つかったレース関連URLを詳細に調査
2. レース結果ページの具体的な構造を分析
3. データ抽出のためのセレクターを特定
4. プロトタイプスクレイパーの作成

### 注意事項:
- robots.txtの内容を確認し、遵守する
- アクセス間隔は1秒以上空ける
- User-Agentを適切に設定する
        """)

def main():
    print("東京シティ競馬サイトの調査を開始します...")
    print("=" * 60)
    
    investigator = TokyoCityInvestigator()
    
    # 調査実行
    investigator.check_robots_txt()
    investigator.investigate_homepage()
    investigator.find_race_pages()
    investigator.test_specific_urls()
    investigator.investigate_date_based_urls()
    investigator.search_api_endpoints()
    investigator.generate_report()
    
    print("\n調査完了！")

if __name__ == "__main__":
    main()