#!/usr/bin/env python3
"""
Gemini API統合サービス
シュンスケ式戦術遂行システム準拠のAI統合モジュール
"""

import os
import google.generativeai as genai
from typing import Dict, List, Any, Optional
import logging
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

class GeminiService:
    """Gemini AI API統合サービス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY環境変数が設定されていません")
        
        # Gemini API初期化
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        
        self.logger.info("Gemini APIサービス初期化完了")
    
    async def generate_web_search_queries(self, course_info: Dict[str, Any]) -> List[str]:
        """
        講座情報から最適な検索クエリを生成
        
        Args:
            course_info: 講座情報辞書
            
        Returns:
            検索クエリのリスト
        """
        
        prompt = f"""
あなたは講座コンテンツ作成の専門家です。
以下の講座について、最新かつ最高品質のコンテンツを収集するための検索クエリを5つ生成してください。

【講座情報】
- タイトル: {course_info.get('title', '')}
- 目次/概要: {course_info.get('outline', '')}
- 対象者: {course_info.get('target_audience', '')}
- 難易度: {course_info.get('difficulty', '')}

【検索クエリの条件】
1. 最新の情報を取得できるもの
2. 権威ある情報源を対象とするもの
3. 実践的な事例やケーススタディを含むもの
4. 初心者にも理解しやすい解説があるもの
5. 図解や実例が豊富なもの

各クエリは独立して有用な検索結果をもたらすように設計してください。
出力形式: 1行につき1つの検索クエリ（番号なし）
"""
        
        try:
            response = await self._generate_content(prompt)
            queries = [q.strip() for q in response.split('\n') if q.strip()]
            return queries[:5]  # 最大5つまで
            
        except Exception as e:
            self.logger.error(f"検索クエリ生成エラー: {e}")
            return [course_info.get('title', 'プログラミング 入門')]
    
    async def analyze_and_structure_content(self, 
                                          search_results: List[Dict],
                                          course_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        検索結果を分析し、講座に最適な構造化コンテンツを生成
        
        Args:
            search_results: Web検索結果のリスト
            course_info: 講座情報
            
        Returns:
            構造化された講座コンテンツ
        """
        
        # 検索結果を要約
        content_summary = ""
        for i, result in enumerate(search_results[:10], 1):
            content_summary += f"""
【情報源 {i}】
URL: {result.get('url', 'N/A')}
タイトル: {result.get('title', 'N/A')}
内容: {result.get('content', 'N/A')[:500]}...
---
"""
        
        prompt = f"""
あなたは世界最高レベルの講座設計専門家です。
以下の情報を基に、最高品質の講義台本を作成してください。

【講座情報】
- タイトル: {course_info.get('title', '')}
- 目次/概要: {course_info.get('outline', '')}
- 対象者: {course_info.get('target_audience', '')}
- 難易度: {course_info.get('difficulty', '')}
- 想定時間: {course_info.get('duration', 60)}分

【収集した情報源】
{content_summary}

【講座台本作成の要求事項】
1. **導入部（5-10分）**: 受講者の関心を引く導入
2. **本編（40-50分）**: 構造化された学習内容
3. **まとめ（5-10分）**: 重要ポイントの復習と次のステップ

4. **各セクションに含めるべき要素**:
   - 明確な学習目標
   - 実践的な例や演習
   - 理解度チェック
   - 重要なポイントの強調

5. **台本の形式**:
   - 講師が話すセリフ
   - スライドや資料の指示
   - 演習やワークの説明
   - タイミングの目安

6. **品質基準**:
   - 論理的な流れ
   - 受講者のレベルに適した説明
   - 実用的で価値ある内容
   - 記憶に残りやすい構成

出力は以下のJSON形式でお願いします：
```json
{{
  "title": "講座タイトル",
  "duration": 想定時間,
  "learning_objectives": ["目標1", "目標2", "目標3"],
  "sections": [
    {{
      "title": "セクションタイトル",
      "duration": セクション時間,
      "content": "詳細な台本内容",
      "slides": ["スライド指示1", "スライド指示2"],
      "exercises": ["演習内容"],
      "key_points": ["重要ポイント1", "重要ポイント2"]
    }}
  ],
  "resources": ["参考資料1", "参考資料2"],
  "next_steps": ["次のステップ提案"]
}}
```
"""
        
        try:
            response = await self._generate_content(prompt)
            # JSONの抽出と解析
            import json
            import re
            
            # JSON部分を抽出
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            else:
                # JSONが見つからない場合は、レスポンス全体をテキストとして返す
                return {
                    "title": course_info.get('title', ''),
                    "content": response,
                    "generated_at": "2024-01-01",
                    "source": "gemini_ai"
                }
                
        except Exception as e:
            self.logger.error(f"コンテンツ構造化エラー: {e}")
            raise
    
    async def apply_goal_seek_prompting(self, 
                                      initial_content: Dict[str, Any],
                                      course_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        ゴールシークプロンプトを適用してコンテンツを最適化
        
        Args:
            initial_content: 初期生成されたコンテンツ
            course_info: 講座情報
            
        Returns:
            最適化されたコンテンツ
        """
        
        prompt = f"""
あなたは講座品質の最終審査官です。
以下の講座コンテンツを評価し、最高品質になるよう改善してください。

【目標レベル】
- 受講者満足度: 95%以上
- 学習効果: 目標達成率90%以上  
- 実践適用率: 80%以上

【現在のコンテンツ】
{initial_content}

【講座情報】
{course_info}

【品質改善の観点】
1. **構造性**: 論理的で理解しやすい流れか？
2. **実用性**: 実際に使える知識・スキルか？
3. **魅力度**: 受講者を引きつける要素があるか？
4. **完成度**: 不足している要素はないか？

【改善指示】
上記の観点から、現在のコンテンツを分析し、改善版を作成してください。
特に以下の点に注意：
- より具体的で実践的な例の追加
- 受講者の心を掴む表現の工夫
- 理解度を深める演習の強化
- 記憶に残るキーワードや フレーズの活用

同じJSON形式で出力してください。
"""
        
        try:
            response = await self._generate_content(prompt)
            import json
            import re
            
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            else:
                return initial_content  # 改善に失敗した場合は元のコンテンツを返す
                
        except Exception as e:
            self.logger.error(f"ゴールシーク最適化エラー: {e}")
            return initial_content
    
    async def _generate_content(self, prompt: str) -> str:
        """
        Gemini APIを使用してコンテンツを生成
        
        Args:
            prompt: 生成プロンプト
            
        Returns:
            生成されたテキスト
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            self.logger.error(f"Gemini API呼び出しエラー: {e}")
            raise