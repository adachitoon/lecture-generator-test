# 📚 高品質講義生成システム (Lecture Generator)

MECE原則とシュンスケ式戦術に基づく最高品質の講義台本・構造化アウトライン自動生成システム

## 🎯 概要

このシステムは、目次入力から世界最高レベルの講義コンテンツを自動生成するWebアプリケーションです。

### ✨ 主な機能

- **📋 目次解析**: 入力された目次を個別セクションに精密分割
- **🔍 構造化アウトライン生成**: MECE原則に基づく詳細なアウトライン作成
- **🎤 話し言葉台本生成**: 双方向性を重視した実践的な講義台本作成
- **🔄 APIキーローテーション**: Gemini API制限回避のための自動キー切り替え
- **📊 品質保証**: 相互排他性・網羅性・論理性・実践性の4軸評価

## 🚀 クイックスタート

### 必要要件

- Python 3.8+
- Gemini API キー (複数推奨)

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/adachitoon/lecture-generator.git
cd lecture-generator

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .envファイルにGemini APIキーを設定
```

### 起動

```bash
# アプリケーション起動
python3 run.py

# ブラウザで以下にアクセス
# http://127.0.0.1:8001
```

## 🛠️ システム構成

### ディレクトリ構造

```
lecture-generator/
├── app/
│   ├── main.py                    # メインアプリケーション
│   ├── services/
│   │   ├── outline_parser_service.py     # 目次解析サービス
│   │   ├── section_content_service.py   # コンテンツ生成サービス
│   │   └── api_key_manager.py           # APIキー管理
│   └── generators/
│       └── lecture_generator.py         # 講義生成エンジン
├── templates/
│   ├── index.html                # メインページ
│   └── debug.html               # デバッグページ
├── static/
│   ├── css/
│   └── js/
│       └── app.js               # フロントエンドロジック
├── run.py                       # 起動スクリプト
├── requirements.txt             # 依存関係
└── README.md
```

### 技術スタック

- **バックエンド**: FastAPI, Python 3.8+
- **AI エンジン**: Google Gemini 2.5-pro
- **フロントエンド**: HTML5, CSS3, Vanilla JavaScript
- **デプロイ**: Uvicorn

## 🔧 設定

### 環境変数

`.env`ファイルに以下を設定：

```env
# メインAPIキー
GEMINI_API_KEY=your_primary_key_here

# 追加のAPIキー（ローテーション用）
GEMINI_API_KEY_1=your_secondary_key_here
GEMINI_API_KEY_2=your_tertiary_key_here
GEMINI_API_KEY_3=your_quaternary_key_here

# データベース設定
DATABASE_URL=sqlite:///./data/lectures.db

# 検索設定
MAX_SEARCH_RESULTS=10
SEARCH_TIMEOUT=30
```

## 📊 APIエンドポイント

### メインエンドポイント

- `GET /` - メインページ表示
- `POST /analyze-outline` - 目次解析・セクション分割
- `POST /generate-section` - セクション別コンテンツ生成
- `POST /generate` - 一括講義生成
- `GET /health` - ヘルスチェック

## 🎯 使用方法

### 基本的なワークフロー

1. **講義情報入力**
   - 講義タイトル
   - 講義の目次
   - 対象受講者
   - 難易度レベル
   - 予定時間

2. **目次解析**
   - 自動的にセクションに分割
   - MECE原則に基づく検証
   - 学習パスの最適化

3. **セクション選択**
   - 個別セクションを選択
   - 構造化アウトライン生成

4. **台本生成**
   - アウトラインに基づく話し言葉台本作成
   - 双方向性とエンゲージメント重視

### 高度な機能

- **APIキーローテーション**: 複数のAPIキーを自動切り替えて制限回避
- **品質スコアリング**: MECE原則に基づく4軸評価
- **コンテキスト継承**: セクション間の論理的つながりを保持

## 🔍 トラブルシューティング

### よくある問題

1. **API制限エラー**
   - 複数のAPIキーを設定
   - 生成頻度を調整

2. **目次解析失敗**
   - 番号付き形式で入力（1-1. セクション名）
   - 階層構造を明確にする

3. **生成品質の向上**
   - 詳細な目次情報を提供
   - 対象受講者を具体的に指定

## 🤝 開発・貢献

### 開発環境セットアップ

```bash
# 開発モードで起動
python3 run.py

# 変更の自動リロード有効
# uvicorn使用で自動的にファイル変更を検知
```

### コードスタイル

- PEP 8準拠
- 日本語コメント推奨
- 型ヒント必須

## 📝 ライセンス

このプロジェクトはMITライセンスのもとで公開されています。

## 🙋‍♂️ サポート

問題やご質問がございましたら、[Issues](https://github.com/adachitoon/lecture-generator/issues)までお気軽にお寄せください。

---

**🎓 高品質な教育コンテンツの democratization を目指して**
