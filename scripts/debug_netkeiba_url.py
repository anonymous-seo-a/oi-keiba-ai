#!/usr/bin/env python3
"""
netkeibaのURL形式とコースコードを調査するスクリプト
"""
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta

def test_netkeiba_urls():
    """様々なURL形式を試して、正しい形式を見つける"""
    
    # User-Agentを設定
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # テストする日付（最近の日付）
    test_date = datetime(2025, 6, 25)
    date_str = test_date.strftime('%Y%m%d')
    
    # 試すべきURL形式のリスト
    url_patterns = [
        # 現在の形式
        f"https://db.netkeiba.com/race/list/30{date_str}/",
        
        # 他の可能性のある形式
        f"https://race.netkeiba.com/race/shutuba_past.html?kaisai_date={date_str}&jyo_cd=30",
        f"https://race.netkeiba.com/top/race_list_sub.html?kaisai_date={date_str}&jyo_cd=30",
        f"https://race.netkeiba.com/top/calendar.html?year={test_date.year}&month={test_date.month}",
        
        # 大井競馬場の他の可能なコード
        f"https://db.netkeiba.com/race/list/03{date_str}/",  # 03
        f"https://db.netkeiba.com/race/list/44{date_str}/",  # 44
        
        # 地方競馬用の形式
        f"https://nar.netkeiba.com/race/list/{date_str}/",
        f"https://nar.netkeiba.com/calendar/top/{test_date.strftime('%Y-%m')}/",
    ]
    
    print(f"テスト日付: {test_date.strftime('%Y-%m-%d')}")
    print("=" * 60)
    
    for url in url_patterns:
        print(f"\n試行中: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # ページタイトルを確認
                title = soup.find('title')
                if title:
                    print(f"ページタイトル: {title.text.strip()}")
                
                # 大井関連のキーワードを探す
                page_text = soup.text.lower()
                if '大井' in page_text or 'oi' in page_text or '東京シティ' in page_text:
                    print("✅ 大井競馬関連のコンテンツが見つかりました！")
                    
                    # レースリンクを探す
                    race_links = soup.find_all('a', href=lambda x: x and '/race/' in x and len(x.split('/')) > 2)
                    print(f"レースリンク数: {len(race_links)}")
                    
                    if race_links:
                        print("サンプルレースリンク:")
                        for link in race_links[:3]:  # 最初の3つを表示
                            print(f"  - {link.get('href')}")
                else:
                    print("❌ 大井競馬関連のコンテンツが見つかりません")
                    
            elif response.status_code == 404:
                print("❌ ページが見つかりません (404)")
            else:
                print(f"❌ エラー: {response.status_code}")
                
        except requests.RequestException as e:
            print(f"❌ リクエストエラー: {e}")
        
        time.sleep(1)  # サーバーに負荷をかけないように
    
    print("\n" + "=" * 60)
    print("地方競馬公式サイトの確認")
    print("=" * 60)
    
    # 地方競馬情報サイトも確認
    nar_urls = [
        "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList",  # 地方競馬公式
        "https://www.tokyocitykeiba.com/",  # 東京シティ競馬（大井）
    ]
    
    for url in nar_urls:
        print(f"\n確認中: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"ステータスコード: {response.status_code}")
            if response.status_code == 200:
                print("✅ アクセス可能")
        except:
            print("❌ アクセスエラー")
        time.sleep(1)

def check_specific_race():
    """特定のレースページを直接確認"""
    print("\n" + "=" * 60)
    print("特定レースページの確認")
    print("=" * 60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 大井競馬の最近のレースIDを推測
    # 通常、レースIDは YYYYMMDDHHTT 形式（HH:開催回次、TT:競走番号）
    test_ids = [
        "202503440101",  # 2025年03月44回01レース
        "202544030101",  # 2025年44回03回01レース
        "c202544030101", # 地方競馬用プレフィックス付き
    ]
    
    for race_id in test_ids:
        url = f"https://db.netkeiba.com/race/{race_id}/"
        print(f"\n試行中: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find('h1')
                if title and ('大井' in title.text or '東京シティ' in title.text):
                    print(f"✅ 大井競馬のレースが見つかりました: {title.text}")
                
        except requests.RequestException as e:
            print(f"❌ エラー: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    print("netkeibaのURL形式調査を開始します...")
    print("=" * 60)
    
    # URL形式のテスト
    test_netkeiba_urls()
    
    # 特定レースの確認
    check_specific_race()
    
    print("\n調査完了！")
    print("\n【推奨事項】")
    print("1. 正しいURL形式が見つかったら、settings.pyを更新してください")
    print("2. 地方競馬（NAR）用の専用URLを使う必要があるかもしれません")
    print("3. 東京シティ競馬公式サイトも代替データソースとして検討してください")