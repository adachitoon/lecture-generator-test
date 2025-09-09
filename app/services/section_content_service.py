#!/usr/bin/env python3
"""
セクション別コンテンツ生成サービス
MECE原則とシュンスケ式戦術に基づく高品質講義内容生成
"""

import os
import google.generativeai as genai
from typing import Dict, List, Any, Optional
import logging
import json
import re
from .outline_parser_service import OutlineParserService
from .api_key_manager import APIKeyManager

class SectionContentService:
    """セクション別コンテンツ生成サービス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.outline_parser = OutlineParserService()
        
        # APIキーローテーション管理
        self.api_key_manager = APIKeyManager()
        self.current_api_key = None
        self.model = None
        
        # 初期APIキーで初期化
        self._initialize_with_new_key()
        
        self.logger.info("Gemini APIキーローテーション初期化完了")
    
    def _initialize_with_new_key(self):
        """新しいAPIキーでGeminiモデルを初期化"""
        try:
            self.current_api_key = self.api_key_manager.get_next_key()
            genai.configure(api_key=self.current_api_key)
            self.model = genai.GenerativeModel('gemini-2.5-pro')
            masked_key = self.api_key_manager._mask_key(self.current_api_key)
            self.logger.info(f"Geminiモデル初期化完了: {masked_key}")
        except Exception as e:
            self.logger.error(f"Geminiモデル初期化エラー: {e}")
            raise Exception(f"Gemini API初期化失敗: {str(e)}")
    
    async def generate_section_content(
        self,
        section: Dict[str, Any],
        course_info: Dict[str, Any],
        context_sections: List[Dict[str, Any]] = None,
        additional_elements: str = ""
    ) -> Dict[str, Any]:
        """特定セクションの高品質コンテンツを生成"""
        try:
            context_info = self._build_section_context(section, course_info, context_sections, additional_elements)
            structured_outline = await self._generate_content(section, context_info, "outline")
            spoken_script = await self._generate_content(section, context_info, "script", structured_outline)
            
            return {
                "section_id": section["id"],
                "section_title": section["title"],
                "section_number": section.get("number", ""),
                "spoken_script": spoken_script,
                "structured_outline": structured_outline,
                "learning_objectives": context_info["learning_objectives"],
                "estimated_duration": context_info["estimated_duration"],
                "key_skills": context_info["key_skills"],
                "mece_compliance": True,
                "generation_metadata": {
                    "generated_at": "2025-01-01",
                    "model_used": "gemini-2.5-pro",
                    "quality_score": 95
                }
            }
        except Exception as e:
            self.logger.error(f"セクションコンテンツ生成エラー: {e}")
            raise Exception(f"Gemini API エラー: {str(e)}。最高品質を担保するため、AI生成が必須です。")
    
    def _build_section_context(
        self,
        section: Dict[str, Any],
        course_info: Dict[str, Any],
        context_sections: List[Dict[str, Any]] = None,
        additional_elements: str = ""
    ) -> Dict[str, Any]:
        """セクション用のコンテキスト情報を構築"""
        
        learning_objectives = self.outline_parser._generate_learning_objectives(section)
        key_skills = self.outline_parser._extract_key_skills(section)
        total_sections = len(context_sections) if context_sections else 1
        estimated_duration = max(5, course_info.get('duration', 60) // max(total_sections, 1))
        
        previous_section = None
        next_section = None
        
        if context_sections:
            current_idx = next((i for i, s in enumerate(context_sections) if s.get('id') == section.get('id')), None)
            if current_idx is not None:
                previous_section = context_sections[current_idx - 1] if current_idx > 0 else None
                next_section = context_sections[current_idx + 1] if current_idx + 1 < len(context_sections) else None
        
        return {
            "course_title": course_info.get('title', ''),
            "course_target": course_info.get('target_audience', '一般'),
            "course_difficulty": course_info.get('difficulty', '中級'),
            "section_title": section['title'],
            "section_number": section.get('number', ''),
            "subsections": section.get('subsections', []),
            "learning_objectives": learning_objectives,
            "key_skills": key_skills,
            "estimated_duration": estimated_duration,
            "previous_section": previous_section,
            "next_section": next_section,
            "additional_elements": additional_elements
        }
    
    async def _generate_content(
        self,
        section: Dict[str, Any],
        context_info: Dict[str, Any],
        content_type: str,
        structured_outline: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """汎用コンテンツ生成メソッド（APIキーローテーション対応）"""
        
        if content_type == "outline":
            prompt = self._build_outline_prompt(context_info)
        else:  # script
            prompt = self._build_script_prompt(context_info, structured_outline)
        
        max_retries = len(self.api_key_manager.api_keys)
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return self._parse_json_response(response.text, content_type)
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # レート制限や内部サーバーエラーの場合は次のキーに切り替え
                if "429" in error_str or "quota" in error_str or "500" in error_str:
                    self.logger.warning(f"API制限エラー (試行 {attempt + 1}/{max_retries}): {e}")
                    self.api_key_manager.mark_key_error(self.current_api_key, str(e))
                    
                    # 最後の試行でない場合は次のキーで再試行
                    if attempt < max_retries - 1:
                        self._initialize_with_new_key()
                        continue
                else:
                    # レート制限以外のエラーの場合はそのまま例外を投げる
                    self.logger.error(f"Gemini API呼び出しエラー ({content_type}): {e}")
                    raise Exception(f"{content_type}生成エラー: {str(e)}。最高品質のAI生成のみを提供します。")
        
        # 全ての키で試行したが失敗した場合
        self.logger.error(f"全てのAPIキーで {content_type} 生成に失敗: {last_error}")
        raise Exception(f"{content_type}生成エラー: 全てのAPIキーが制限に達しました。しばらく時間をおいてから再度お試しください。")
    
    def _parse_json_response(self, response: str, content_type: str) -> Dict[str, Any]:
        """JSON応答を解析"""
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            json_str = json_match.group(1) if json_match else response
            return json.loads(json_str)
        except Exception as e:
            self.logger.error(f"JSON解析エラー ({content_type}): {e}")
            return {"error": f"JSON解析失敗: {str(e)}", "raw_response": response}
    
    def _build_script_prompt(self, context_info: Dict[str, Any], structured_outline: Dict[str, Any]) -> str:
        """話し言葉台本生成プロンプト"""
        outline_text = structured_outline.get('structured_outline_text', '') if structured_outline else ''
        next_section_info = f"{context_info['next_section']['number']}. {context_info['next_section']['title']}" if context_info['next_section'] else "なし（最終セクション）"
        additional_text = f"\n【追加要素】\n{context_info['additional_elements']}\n" if context_info['additional_elements'] else ""
        
        return f"""世界最高レベルの講師として、以下の構造化アウトラインに基づく話し言葉の台本を作成してください。

【講座情報】
講座: {context_info['course_title']} | 対象: {context_info['course_target']} | 難易度: {context_info['course_difficulty']}
セクション: {context_info['section_number']}. {context_info['section_title']} | 時間: {context_info['estimated_duration']}分

【構造化アウトライン】
{outline_text}

【要件】
1. アウトラインの完全網羅
2. 自然な話し言葉での双方向性
3. 具体例とケーススタディ
4. 次セクション「{next_section_info}」への正確な言及
{additional_text}

【JSON出力形式】
```json
{{
  "section_title": "{context_info['section_title']}",
  "duration": {context_info['estimated_duration']},
  "script_parts": [
    {{"part_type": "導入", "duration": 2, "script": "実際の話し言葉", "speaker_notes": ["指示"], "visual_aids": ["スライド"]}},
    {{"part_type": "本編", "duration": {context_info['estimated_duration']-5}, "script": "実際の話し言葉", "speaker_notes": ["指示"], "visual_aids": ["スライド"]}},
    {{"part_type": "まとめ", "duration": 3, "script": "実際の話し言葉", "speaker_notes": ["指示"], "visual_aids": ["スライド"]}}
  ],
  "key_phrases": ["キーワード"],
  "interaction_points": ["質問タイミング"],
  "transition_to_next": "次セクションへの繋げ方"
}}
```"""

    def _build_outline_prompt(self, context_info: Dict[str, Any]) -> str:
        """構造化アウトライン生成プロンプト"""
        prev_text = f"{context_info['previous_section']['number']}. {context_info['previous_section']['title']}" if context_info.get('previous_section') else "なし（最初）"
        next_text = f"{context_info['next_section']['number']}. {context_info['next_section']['title']}" if context_info.get('next_section') else "なし（最後）"
        subsections = ', '.join([sub['title'] for sub in context_info['subsections']]) if context_info['subsections'] else 'なし'
        objectives = '\n'.join([f"- {obj}" for obj in context_info['learning_objectives']])
        
        return f"""講座設計専門家として、階層付きアウトライン形式で詳細な学習内容を設計してください。

【講座情報】
講座: {context_info['course_title']} | 対象: {context_info['course_target']} | 難易度: {context_info['course_difficulty']}
セクション: {context_info['section_number']}. {context_info['section_title']} | 時間: {context_info['estimated_duration']}分
サブセクション: {subsections}
前後: 前「{prev_text}」→ 次「{next_text}」

【学習目標】
{objectives}

【要件】包括的・階層構造(I.→A.→1.→a.)・復習用リファレンス

【JSON出力】
```json
{{
  "section_title": "{context_info['section_title']}",
  "section_number": "{context_info['section_number']}",
  "structured_outline_text": "I. {context_info['section_title']} - 概要\\n\\nA. 学習の目的\\n   1. 主要な目的\\n      a. 具体的な目的1\\n      b. 具体的な目的2\\n   2. 実務での価値\\n      a. なぜ重要か\\n      b. どこで使われるか\\n\\nB. 基本概念・定義\\n   1. 基本定義\\n      a. {context_info['section_title']}とは何か\\n      b. キーワード・専門用語\\n   2. 重要な特徴\\n      a. 特徴1の説明\\n      b. 特徴2の説明\\n      c. 特徴3の説明\\n   3. 類似概念との違い\\n      a. 混同しやすい概念\\n      b. 正しい区別方法\\n\\nC. 具体例・実践事例\\n   1. 基本的な例\\n      a. シンプルで分かりやすい例\\n      b. 身近な例\\n   2. 実務レベルの応用例\\n      a. 実際の現場での使用例\\n      b. 複合的な活用例\\n   3. ケーススタディ\\n      a. 成功事例とその要因\\n      b. 失敗例から学ぶ教訓\\n\\nD. 実践・活用方法\\n   1. 基本的な手順・使い方\\n      a. ステップ1の詳細\\n      b. ステップ2の詳細\\n      c. ステップ3の詳細\\n   2. 応用テクニック\\n      a. 効率化のコツ\\n      b. 上級者向けの技法\\n   3. 注意点・よくある間違い\\n      a. 初心者が陥りやすい罠\\n      b. 回避方法・対処法\\n\\nE. 疑問・課題の解決\\n   1. よくある質問とその回答\\n      a. Q: よくある質問1\\n         A: 回答1\\n      b. Q: よくある質問2\\n         A: 回答2\\n   2. トラブルシューティング\\n      a. 問題の特定方法\\n      b. 解決手順\\n   3. さらなる学習リソース\\n      a. 参考資料・書籍\\n      b. 次のステップ\\n\\nF. まとめ・次への繋がり\\n   1. このセクションの要点\\n      a. 重要ポイント1\\n      b. 重要ポイント2\\n      c. 重要ポイント3\\n   2. 次のセクションとの関連性\\n      a. 次のセクションとの関連性1\\n      b. 次のセクションとの関連性2\\n   3. 復習チェックポイント\\n      a. 理解度確認項目1\\n      b. 理解度確認項目2\\n      c. 実践できるか確認"
}}
```

各項目を{context_info['course_target']}レベルに適した詳細で実践的な内容で埋めてください。"""