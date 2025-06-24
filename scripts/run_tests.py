#!/usr/bin/env python3
"""
テスト実行スクリプト
"""
import sys
import unittest
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

def run_all_tests():
    """すべてのテストを実行"""
    # テストディレクトリを検索
    test_dir = Path(__file__).parent.parent / 'tests'
    
    # テストスイートを作成
    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern='test_*.py')
    
    # テストを実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果を返す
    return result.wasSuccessful()

def run_specific_test(test_module):
    """特定のテストモジュールを実行"""
    try:
        # モジュールをインポート
        module = __import__(f'tests.{test_module}', fromlist=[test_module])
        
        # テストスイートを作成
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        # テストを実行
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except ImportError:
        print(f"エラー: テストモジュール '{test_module}' が見つかりません")
        return False

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='大井競馬予想AI テストランナー')
    parser.add_argument(
        '--module', '-m',
        help='実行するテストモジュール名 (test_database, test_scraper, test_models)',
        choices=['test_database', 'test_scraper', 'test_models']
    )
    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='カバレッジを測定してテストを実行'
    )
    
    args = parser.parse_args()
    
    print("🧪 大井競馬予想AI テストランナー")
    print("=" * 50)
    
    success = True
    
    if args.coverage:
        try:
            import coverage
            cov = coverage.Coverage()
            cov.start()
            
            print("📈 カバレッジ測定を開始します...")
            
        except ImportError:
            print("⚠️  coverageパッケージがインストールされていません")
            print("pip install coverage でインストールしてください")
            args.coverage = False
    
    try:
        if args.module:
            print(f"🎯 特定テストを実行: {args.module}")
            success = run_specific_test(args.module)
        else:
            print("🚀 全テストを実行")
            success = run_all_tests()
        
        if args.coverage:
            cov.stop()
            cov.save()
            
            print("\n📈 カバレッジレポート:")
            cov.report()
            
            # HTMLレポートを作成
            cov.html_report(directory='htmlcov')
            print("HTMLレポートが htmlcov/ ディレクトリに作成されました")
        
    except KeyboardInterrupt:
        print("\n⚠️  テストが中断されました")
        success = False
    
    except Exception as e:
        print(f"\n🚨 テスト実行中にエラーが発生しました: {e}")
        success = False
    
    print("\n" + "=" * 50)
    
    if success:
        print("✅ すべてのテストが成功しました！")
        sys.exit(0)
    else:
        print("❌ テストに失敗しました")
        sys.exit(1)

if __name__ == '__main__':
    main()
