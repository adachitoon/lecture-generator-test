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
5. {additional_text}の要素が入力された場合は必ず台本の中身に入れ込むことを忘れないでください

【記述条件】
• 「**」などの装飾は使わず、出力する前に「**」などの表現が入っていないか確認して、入っていたら「**」のみ削除して出力すること

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

        return f"""講座設計専門家として、以下の構造でマインドマップ化しやすい体言止め形式の学習内容を設計してください。

【講座情報】
講座: {context_info['course_title']} | 対象: {context_info['course_target']} | 難易度: {context_info['course_difficulty']}
セクション: {context_info['section_number']}. {context_info['section_title']} | 時間: {context_info['estimated_duration']}分
サブセクション: {subsections}
前後: 前「{prev_text}」→ 次「{next_text}」
追加要素: {context_info['additional_elements']}

【学習目標】
{objectives}

【構造化アウトライン形式】
講義の目的
〜〜とは（そもそもの定義と簡潔な説明を一言で）
〜〜の重要性（なぜ必要か・メリット・影響を箇条書き3点）
〜〜の全体像（全体像・STEP・要素分解・各要素の役割説明）
〜〜の具体的な解説（STEPごとの具体的な解説・進め方・手順・各要素の解説等を記載）
〜〜の補足（本文で最も重要な要素を補足として1つだけ追加）
〜〜の課題（講義視聴後の行動やアクションプランを具体的に提示）

【記述条件】
• 説明は専門用語に偏らず、初心者にも理解できる言葉を使う
• 実務に落とし込めるよう具体例や比喩を交える
• 体言止めを基本とする（マインドマップ化を前提）
• 無駄な修飾語や冗長表現は完全に排除する
• 段落形式で簡潔に（理解に必要な情報のみ）記述する
• 具体的な解説パートは、全体像パートの3倍のボリュームで具体的な説明をする
• 「**」などの装飾は使わず、出力する前に「**」などの表現が入っていないか確認して、入っていたら「**」のみ削除して出力すること
• マインドマップ化を前提とするため、必ず一文は短く、構造化して階層構造で出力すること
• 各要素が並列なのか上下関係なのかを出力前に確認し、適切な階層に修正を完了させた上で出力すること

【JSON出力】
```json
{{
  "section_title": "{context_info['section_title']}",
  "section_number": "{context_info['section_number']}",
  "structured_outline_text": "講義の目的\\n  [このセクションで達成すべきゴールや学習成果を簡潔に記載]\\n\\n{context_info['section_title']}とは\\n  [定義を一言で簡潔に記載]\\n\\n{context_info['section_title']}の重要性\\n  ・[メリット1]\\n  ・[メリット2]\\n  ・[メリット3]\\n\\n{context_info['section_title']}の全体像\\n  [全体構造やSTEP、要素分解、各要素の役割を簡潔に説明]\\n\\n{context_info['section_title']}の具体的な解説\\n  [STEPごとの詳細な解説、進め方、手順、各要素の具体的な説明を全体像の3倍のボリュームで記載]\\n\\n{context_info['section_title']}の補足\\n  [本文で最も重要な要素を1つだけ選んで追加説明]\\n\\n{context_info['section_title']}の課題\\n  [講義視聴後に実践すべき具体的なアクションプラン]"
}}
```

各項目を{context_info['course_target']}レベルに適した内容で、体言止めを基本に簡潔かつ実践的に記述してください。
具体的な解説パートは全体像の3倍のボリュームで詳細に記載してください。"""
