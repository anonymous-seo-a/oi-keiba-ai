#!/usr/bin/env python3
"""
大井競馬予想AIプロジェクト初期化スクリプト
このスクリプトを実行して、プロジェクトの基本構造を作成します。
"""

import os
import sys
from pathlib import Path

def create_directory_structure():
    """プロジェクトのディレクトリ構造を作成"""
    directories = [
        'src/data_collection',
        'src/feature_engineering', 
        'src/models',
        'src/prediction',
        'src/utils',
        'data/raw',
        'data/processed',
        'data/external',
        'notebooks',
        'tests',
        'docs',
        'scripts',
        'web_app/pages',
        'web_app/static',
        'logs',
        'models',
        'cache'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # __init__.pyファイルを作成（Pythonパッケージとして認識させる）
        if directory.startswith('src/'):
            init_file = Path(directory) / '__init__.py'
            if not init_file.exists():
                init_file.touch()
        
        # .gitkeepファイルを作成（空のディレクトリをGitで管理）
        if directory in ['data/raw', 'data/processed', 'data/external', 'logs', 'models', 'cache']:
            gitkeep_file = Path(directory) / '.gitkeep'
            if not gitkeep_file.exists():
                gitkeep_file.touch()
    
    print("✅ ディレクトリ構造を作成しました")

def main():
    """メイン実行関数"""
    print("🏇 大井競馬予想AI プロジェクト初期化開始")
    print("=" * 50)
    
    try:
        create_directory_structure()
        
        print("=" * 50)
        print("✅ プロジェクト初期化が完了しました！")
        print()
        print("次のステップ:")
        print("1. requirements.txtの依存関係をインストール:")
        print("   pip install -r requirements.txt")
        print()
        print("2. .envファイルを作成して環境変数を設定:")
        print("   cp .env.example .env")
        print("   # .envファイルを編集")
        print()
        print("3. データ収集を開始:")
        print("   python scripts/run_data_collection.py")
        print()
        print("Happy Coding! 🚀")
        
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
