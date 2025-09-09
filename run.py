#!/usr/bin/env python3
"""
講座コンテンツ生成システム - 起動スクリプト
シュンスケ式戦術遂行システム v3.0.0
"""

import os
import sys
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """アプリケーション起動"""
    
    # 環境変数の確認
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️  警告: GEMINI_API_KEY環境変数が設定されていません")
        print("   .envファイルを作成し、Gemini APIキーを設定してください")
        print("   例: GEMINI_API_KEY=your_api_key_here")
        print()
    
    # データディレクトリの作成
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    contexts_dir = data_dir / "contexts"
    contexts_dir.mkdir(exist_ok=True)
    
    # ポート設定（環境変数から取得、デフォルトは8001）
    port = int(os.getenv('PORT', 8001))
    
    print("🎯 シュンスケ式講座生成システム v3.0.0 起動中...")
    print("=" * 60)
    print(f"📡 アクセスURL: http://127.0.0.1:{port}")
    print("🛑 停止方法: Ctrl+C")
    print("=" * 60)
    
    # FastAPIアプリケーションの起動
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        reload=True,
        reload_dirs=["app"],
        log_level="info"
    )

if __name__ == "__main__":
    main()