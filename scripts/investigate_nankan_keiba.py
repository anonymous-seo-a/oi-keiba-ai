#!/usr/bin/env python3
"""
南関競馬サイトのレース結果ページを調査するスクリプト
大井競馬のデータ構造を解析する
"""
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import re
from urllib.parse import urljoin

class NankanKeibaInvestigator:
    def __init__(self):
        self.base_url = "http://www.nankankeiba.com/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 東京シティ競馬から発見したレース結果URL
        self.sample_result_urls = [
            "http://www.nankankeiba.com/result/2025012920160311.do",
            "http://www.nankankeiba.com/result/2025021920170311.do",
            "http://www.nankankeiba.com/result/2025031320180411.do",
            "http://www.nankankeiba.com/result/2025032620190311.do",
            "http://www.nankankeiba.com/result/2025041620010311.do"
        ]
    
    def check_robots_txt(self):
        """robots.txtを確認"""
        print("=" * 60)
        print("robots.txtの確認")
        print("=" * 60)
        
        try:
            url = urljoin(self.base_url, "robots.txt")
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                print("✅ robots.txt が見つかりました:")
                print(response.text[:500])  # 最初の500文字
            else:
                print(f"❌ robots.txt が見つかりません (ステータス: {response.status_code})")
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    def analyze_url_pattern(self):
        """URLパターンを分析"""
        print("\n" + "=" * 60)
        print("URLパターンの分析")
        print("=" * 60)
        
        for url in self.sample_result_urls:
            # URLからパラメータを抽出
            match = re.search(r'/result/(\d{8})(\d+)\.do', url)
            if match:
                date_part = match.group(1)
                code_part = match.group(2)
                
                # 日付を解析
                date_obj = datetime.strptime(date_part, '%Y%m%d')
                
                print(f"\nURL: {url}")
                print(f"  日付: {date_obj.strftime('%Y年%m月%d日')}")
                print(f"  コード部分: {code_part}")
                
                # コード部分を分析
                if len(code_part) >= 8:
                    possible_track = code_part[:2]
                    possible_kaisai = code_part[2:4]
                    possible_day = code_part[4:6]
                    possible_race = code_part[6:8]
                    
                    print(f"  可能な構造:")
                    print(f"    - 競馬場コード: {possible_track}")
                    print(f"    - 開催回次: {possible_kaisai}")
                    print(f"    - 日次: {possible_day}")
                    print(f"    - レース番号: {possible_race}")
    
    def investigate_result_page(self, url):
        """レース結果ページを詳細調査"""
        print(f"\n### {url} の調査")
        
        try:
            response = self.session.get(url, timeout=10)
            print(f"ステータス: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser', from_encoding='shift_jis')
                
                # ページタイトル
                title = soup.find('title')
                if title:
                    print(f"ページタイトル: {title.text.strip()}")
                
                # レース名を探す
                race_name = None
                h1_tags = soup.find_all('h1')
                h2_tags = soup.find_all('h2')
                h3_tags = soup.find_all('h3')
                
                for tag in h1_tags + h2_tags + h3_tags:
                    text = tag.text.strip()
                    if 'レース' in text or 'R' in text:
                        race_name = text
                        print(f"レース名: {race_name}")
                        break
                
                # テーブルを探す
                tables = soup.find_all('table')
                print(f"\nテーブル数: {len(tables)}")
                
                for i, table in enumerate(tables):
                    # テーブルのクラスやIDを確認
                    table_class = table.get('class', [])
                    table_id = table.get('id', '')
                    
                    print(f"\nテーブル{i+1}:")
                    if table_class:
                        print(f"  クラス: {table_class}")
                    if table_id:
                        print(f"  ID: {table_id}")
                    
                    # ヘッダーを確認
                    headers = []
                    th_tags = table.find_all('th')
                    if th_tags:
                        headers = [th.text.strip() for th in th_tags]
                        print(f"  ヘッダー: {headers[:15]}")  # 最初の15個
                        
                        # レース結果テーブルの可能性を判定
                        result_keywords = ['着順', '馬番', '馬名', 'タイム', '騎手', '調教師', 'オッズ', '人気']
                        matches = [kw for kw in result_keywords if any(kw in h for h in headers)]
                        if matches:
                            print(f"  ✅ レース結果テーブルの可能性大！ マッチキーワード: {matches}")
                            
                            # 最初の数行のデータを確認
                            rows = table.find_all('tr')[1:4]  # ヘッダー以外の最初の3行
                            for j, row in enumerate(rows):
                                cells = row.find_all(['td', 'th'])
                                cell_texts = [cell.text.strip() for cell in cells[:10]]
                                print(f"    データ行{j+1}: {cell_texts}")
                    
                    # 行数を確認
                    rows = table.find_all('tr')
                    print(f"  行数: {len(rows)}")
                
                # その他の重要な要素を探す
                # レース条件
                race_info_patterns = [
                    r'ダート\d+m',
                    r'\d+万下',
                    r'[A-Z]\d+',
                    r'サラ系\d+歳',
                    r'牝馬限定',
                    r'天候：[晴曇雨雪]+',
                    r'馬場：[良稍重不]+',
                ]
                
                page_text = soup.text
                print("\n### レース条件の抽出:")
                for pattern in race_info_patterns:
                    matches = re.findall(pattern, page_text)
                    if matches:
                        print(f"  {pattern}: {matches[:3]}")  # 最初の3つ
                
                # リンクを確認（他のレースへのナビゲーション）
                print("\n### ナビゲーションリンク:")
                nav_links = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    text = link.text.strip()
                    
                    if 'result' in href and text and len(text) < 20:
                        nav_links.append({
                            'text': text,
                            'href': urljoin(url, href)
                        })
                
                # 重複を除去して表示
                unique_links = []
                seen = set()
                for link in nav_links:
                    if link['href'] not in seen:
                        seen.add(link['href'])
                        unique_links.append(link)
                
                for link in unique_links[:10]:
                    print(f"  - {link['text']}: {link['href']}")
                    
            else:
                print(f"❌ アクセス失敗")
                
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    def investigate_all_samples(self):
        """すべてのサンプルURLを調査"""
        print("\n" + "=" * 60)
        print("レース結果ページの詳細調査")
        print("=" * 60)
        
        for i, url in enumerate(self.sample_result_urls[:3]):  # 最初の3つを詳しく調査
            if i > 0:
                time.sleep(1)  # サーバーに配慮
            self.investigate_result_page(url)
    
    def find_race_list_page(self):
        """レース一覧ページを探す"""
        print("\n" + "=" * 60)
        print("レース一覧ページの探索")
        print("=" * 60)
        
        # 可能性のあるURL
        test_urls = [
            "http://www.nankankeiba.com/program/00000000000000.do",  # 東京シティから発見
            "http://www.nankankeiba.com/result/",
            "http://www.nankankeiba.com/race_list.do",
            "http://www.nankankeiba.com/schedule/",
            "http://www.nankankeiba.com/calendar/",
        ]
        
        for url in test_urls:
            print(f"\n試行中: {url}")
            try:
                response = self.session.get(url, timeout=10)
                print(f"ステータス: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='shift_jis')
                    
                    # 大井競馬の情報を探す
                    if '大井' in soup.text or 'TCK' in soup.text or '東京シティ' in soup.text:
                        print("✅ 大井競馬関連の情報が含まれています！")
                        
                        # レースリンクを探す
                        race_links = []
                        for link in soup.find_all('a', href=True):
                            href = link.get('href', '')
                            text = link.text.strip()
                            
                            if ('result' in href or 'race' in href) and text:
                                race_links.append({
                                    'text': text[:50],  # 長すぎる場合は切る
                                    'href': urljoin(url, href)
                                })
                        
                        if race_links:
                            print(f"レース関連リンク: {len(race_links)}個")
                            for link in race_links[:5]:
                                print(f"  - {link['text']}: {link['href']}")
                                
            except Exception as e:
                print(f"❌ エラー: {type(e).__name__}")
            
            time.sleep(1)
    
    def generate_report(self):
        """調査レポートを生成"""
        print("\n" + "=" * 60)
        print("調査結果レポート")
        print("=" * 60)
        
        print("""
### URLパターンの解析結果:
- 形式: /result/YYYYMMDD[競馬場][開催][日次][レース].do
- 例: /result/2025012920160311.do
  - 20250129: 2025年1月29日
  - 20: 大井競馬場のコード（推定）
  - 16: 第16回開催
  - 03: 3日目
  - 11: 第11レース

### データ取得戦略:
1. 東京シティ競馬サイトから開催日とレース結果URLを取得
2. 南関競馬サイトから実際のレース結果データを取得
3. テーブル構造を解析してデータを抽出

### 実装のポイント:
- 文字エンコーディング: Shift-JIS
- レース結果テーブルの識別: ヘッダーにキーワードを含む
- URLパターンの理解: 日付とレース識別子の構造
        """)

def main():
    print("南関競馬サイトの調査を開始します...")
    print("=" * 60)
    
    investigator = NankanKeibaInvestigator()
    
    # 調査実行
    investigator.check_robots_txt()
    investigator.analyze_url_pattern()
    investigator.investigate_all_samples()
    investigator.find_race_list_page()
    investigator.generate_report()
    
    print("\n調査完了！")

if __name__ == "__main__":
    main()