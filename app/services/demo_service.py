#!/usr/bin/env python3
"""
デモサービス - API制限時のフォールバック機能
シュンスケ式戦術遂行システム準拠のデモンストレーション機能
"""

import json
import random
from typing import Dict, List, Any
from datetime import datetime
import logging

class DemoService:
    """
    デモンストレーション用サービス
    
    Gemini API制限時やデモ環境でのフォールバック機能として、
    高品質なサンプル講座コンテンツを提供する。
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # サンプル検索クエリのテンプレート
        self.sample_queries = [
            "{topic} 基礎入門",
            "{topic} 実践ガイド", 
            "{topic} チュートリアル",
            "{topic} 最新動向",
            "{topic} ベストプラクティス"
        ]
        
        # 高品質サンプルコンテンツ
        self.sample_content_templates = {
            "プログラミング": {
                "sections": [
                    {
                        "title": "基礎概念の理解",
                        "content": "プログラミングの基本概念から始め、変数、データ型、制御構造を学習します。実際のコード例を通じて、理論と実践を結びつけます。",
                        "key_points": ["変数とデータ型", "制御構造", "関数の基本"],
                        "exercises": ["Hello World プログラム", "簡単な計算プログラム"]
                    },
                    {
                        "title": "実践的なプログラミング",
                        "content": "実際のプロジェクトを通じて、プログラミングスキルを向上させます。エラーハンドリング、デバッグ技術、コードの最適化について学習します。",
                        "key_points": ["エラーハンドリング", "デバッグ技術", "コード最適化"],
                        "exercises": ["小さなアプリケーション開発", "バグ修正演習"]
                    }
                ]
            },
            "ビジネス": {
                "sections": [
                    {
                        "title": "ビジネス基礎理論",
                        "content": "現代ビジネスの基本原理と戦略的思考について学習します。市場分析、競合分析、価値提案の構築方法を実例を通じて理解します。",
                        "key_points": ["市場分析", "競合分析", "価値提案"],
                        "exercises": ["SWOT分析演習", "ビジネスモデル設計"]
                    },
                    {
                        "title": "実践的ビジネススキル",
                        "content": "コミュニケーション、プレゼンテーション、チームワークなど、実際のビジネス現場で必要なスキルを習得します。",
                        "key_points": ["効果的コミュニケーション", "プレゼン技術", "チーム運営"],
                        "exercises": ["プレゼンテーション実践", "チームプロジェクト"]
                    }
                ]
            },
            "デザイン": {
                "sections": [
                    {
                        "title": "デザイン原則と理論",
                        "content": "デザインの基本原則、色彩理論、タイポグラフィについて学習します。優れたデザインの共通要素を理解し、実際の作品分析を行います。",
                        "key_points": ["デザイン原則", "色彩理論", "タイポグラフィ"],
                        "exercises": ["色彩配色演習", "レイアウト設計"]
                    },
                    {
                        "title": "デジタルデザイン実践",
                        "content": "デジタルツールを使用した実践的なデザイン制作を行います。UI/UXデザインの基礎から応用まで、幅広くカバーします。",
                        "key_points": ["UI/UXデザイン", "デザインツール活用", "プロトタイピング"],
                        "exercises": ["Webサイトデザイン", "モバイルアプリUI設計"]
                    }
                ]
            }
        }
        
        self.logger.info("デモサービス初期化完了")
    
    async def generate_demo_search_queries(self, course_info: Dict[str, Any]) -> List[str]:
        """
        デモ用検索クエリを生成
        
        Args:
            course_info: 講座情報
            
        Returns:
            生成されたデモ検索クエリのリスト
        """
        title = course_info.get('title', '')
        queries = []
        
        # タイトルから主要トピックを抽出（簡易版）
        topic = title.split()[0] if title.split() else "プログラミング"
        
        for template in self.sample_queries:
            queries.append(template.format(topic=topic))
        
        # ランダムに3-5個を選択
        selected_queries = random.sample(queries, min(len(queries), random.randint(3, 5)))
        
        self.logger.info(f"デモ検索クエリ生成完了: {len(selected_queries)}個")
        return selected_queries
    
    async def generate_demo_search_results(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        デモ用検索結果を生成
        
        Args:
            queries: 検索クエリのリスト
            
        Returns:
            模擬検索結果のリスト
        """
        results = []
        
        sample_domains = [
            "wikipedia.org",
            "github.com", 
            "stackoverflow.com",
            "medium.com",
            "qiita.com",
            "zenn.dev"
        ]
        
        for i, query in enumerate(queries):
            for j in range(random.randint(2, 4)):  # 各クエリで2-4件の結果
                result = {
                    'query': query,
                    'title': f'{query}に関する詳細ガイド - 第{j+1}部',
                    'url': f'https://{random.choice(sample_domains)}/article/{i}_{j}',
                    'snippet': f'{query}について詳しく解説しています。基礎から応用まで、実践的な内容をカバー。',
                    'content': f"""
                    {query}に関する包括的な内容です。

                    ## 主要ポイント
                    - 基礎概念の理解
                    - 実践的な応用方法  
                    - よくある課題と解決策
                    - 最新のトレンドと動向

                    ## 詳細説明
                    この分野では、理論と実践のバランスが重要です。基礎をしっかり固めた上で、
                    実際のプロジェクトを通じてスキルを向上させることが効果的です。

                    ## 推奨学習アプローチ
                    1. 基礎理論の学習
                    2. 簡単な演習から開始
                    3. 実践プロジェクトへの応用
                    4. 継続的な改善と最適化

                    このように段階的にアプローチすることで、確実にスキルアップが可能です。
                    """,
                    'relevance_score': random.randint(15, 25),
                    'word_count': random.randint(400, 800),
                    'extracted_at': datetime.now().isoformat()
                }
                results.append(result)
        
        self.logger.info(f"デモ検索結果生成完了: {len(results)}件")
        return results
    
    async def generate_demo_lecture_content(self, course_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        デモ用講座コンテンツを生成（話し言葉台本 + 構造的アウトライン対応）
        
        Args:
            course_info: 講座情報
            
        Returns:
            話し言葉台本と構造的アウトラインを含む高品質なデモ講座コンテンツ
        """
        
        title = course_info.get('title', 'サンプル講座')
        duration = course_info.get('duration', 60)
        target_audience = course_info.get('target_audience', '一般')
        difficulty = course_info.get('difficulty', '中級')
        outline = course_info.get('outline', '')
        
        # 既存のコンテンツ生成
        basic_content = await self._generate_basic_content(course_info)
        
        # 話し言葉台本の生成
        spoken_script = await self._generate_spoken_script(course_info, basic_content)
        
        # 構造的アウトラインの生成
        structured_outline = await self._generate_structured_outline(course_info, basic_content)
        
        return {
            **basic_content,
            "spoken_script": spoken_script,
            "structured_outline": structured_outline,
            "output_formats": {
                "copyable_script": self._format_for_copy(spoken_script),
                "copyable_outline": self._format_for_copy(structured_outline)
            }
        }
    
    async def _generate_basic_content(self, course_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        基本的な講座コンテンツを生成
        
        Args:
            course_info: 講座情報
            
        Returns:
            基本的な講座コンテンツ
        """
        
        title = course_info.get('title', 'サンプル講座')
        duration = course_info.get('duration', 60)
        target_audience = course_info.get('target_audience', '一般')
        difficulty = course_info.get('difficulty', '中級')
        
        # カテゴリ判定（簡易版）
        category = "プログラミング"  # デフォルト
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['ビジネス', 'business', '経営', 'マーケティング']):
            category = "ビジネス"
        elif any(word in title_lower for word in ['デザイン', 'design', 'ui', 'ux']):
            category = "デザイン"
        
        # テンプレートベースのコンテンツ生成
        sections = self.sample_content_templates.get(category, self.sample_content_templates["プログラミング"])["sections"].copy()
        
        # セクション時間の調整
        section_duration = duration // len(sections)
        for section in sections:
            section['duration'] = section_duration
        
        # 学習目標の生成
        learning_objectives = [
            f"{title}の基本概念を理解し、実践できるようになる",
            f"{target_audience}向けの実用的なスキルを習得する", 
            f"{difficulty}レベルの課題を自力で解決できるようになる",
            "学習した内容を実際のプロジェクトに応用できる"
        ]
        
        demo_content = {
            "title": title,
            "duration": duration,
            "learning_objectives": learning_objectives,
            "sections": sections,
            "resources": [
                "推奨参考書籍リスト",
                "オンライン学習リソース",
                "実践プロジェクト例",
                "コミュニティフォーラム"
            ],
            "next_steps": [
                "より高度なトピックへの発展学習",
                "関連分野との連携学習",
                "実際のプロジェクト参加",
                "専門コミュニティへの参加"
            ]
        }
        
        return demo_content
    
    async def _generate_spoken_script(self, course_info: Dict[str, Any], basic_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        話し言葉での講座台本を生成
        
        Args:
            course_info: 講座情報
            basic_content: 基本コンテンツ
            
        Returns:
            話し言葉形式の講座台本
        """
        
        title = course_info.get('title', 'サンプル講座')
        target_audience = course_info.get('target_audience', '一般')
        duration = course_info.get('duration', 60)
        
        spoken_sections = []
        
        # 導入部分の台本
        intro_script = f"""
【導入】（約5分）

こんにちは、皆さん！今日は『{title}』について一緒に学んでいきましょう。

この講座は{target_audience}の皆さんを対象に、約{duration}分間でお届けします。

まず、今日の学習目標を確認しておきましょう。
この講座を受講することで、皆さんは：
"""
        
        for i, objective in enumerate(basic_content.get('learning_objectives', []), 1):
            intro_script += f"\n{i}. {objective}"
        
        intro_script += "\n\nこれらのスキルを身につけることができます。それでは、さっそく始めていきましょう！"
        
        spoken_sections.append({
            "section_type": "導入",
            "duration": 5,
            "script": intro_script
        })
        
        # 各セクションの話し言葉台本生成
        for i, section in enumerate(basic_content.get('sections', []), 1):
            section_script = f"""
【第{i}部: {section.get('title', '')}】（約{section.get('duration', 15)}分）

それでは、第{i}部の『{section.get('title', '')}』について説明していきます。

{section.get('content', '')}

特に覚えておいていただきたいポイントは以下の通りです：
"""
            
            for point in section.get('key_points', []):
                section_script += f"\n・{point}"
            
            if section.get('exercises'):
                section_script += "\n\nでは、実際に hands-on で体験してみましょう！"
                for exercise in section.get('exercises', []):
                    section_script += f"\n\n【演習】\n{exercise}\n\n皆さん、いかがでしょうか。うまくできましたか？"
            
            section_script += f"\n\n以上で第{i}部を終了します。何かご質問があれば、遠慮なくお聞かせください！"
            
            spoken_sections.append({
                "section_type": f"本編第{i}部",
                "duration": section.get('duration', 15),
                "script": section_script
            })
        
        # まとめ部分の台本
        conclusion_script = f"""
【まとめ】（約5分）

皆さん、お疲れ様でした！今日の『{title}』はいかがでしたでしょうか。

今日学んだことを簡単に振り返ってみましょう：
"""
        
        for i, section in enumerate(basic_content.get('sections', []), 1):
            conclusion_script += f"\n・第{i}部では、{section.get('title', '')}について学びました"
        
        conclusion_script += f"\n\nこれで今日の講座は終了ですが、学習はここからが本番です！\n\n次のステップとしては："
        
        for step in basic_content.get('next_steps', []):
            conclusion_script += f"\n・{step}"
        
        conclusion_script += "\n\nこれらに取り組んでいただけると、さらにスキルアップできると思います。\n\n今日はありがとうございました。また次の機会にお会いしましょう！"
        
        spoken_sections.append({
            "section_type": "まとめ",
            "duration": 5,
            "script": conclusion_script
        })
        
        return {
            "title": f"{title} - 講師用台本",
            "total_duration": duration,
            "sections": spoken_sections,
            "script_notes": [
                "各セクション間で2-3分の休憩を取ることをお勧めします",
                "受講者の理解度に応じて、説明の速度を調整してください",
                "質疑応答の時間を適宜設けてください",
                "実際の講義では、受講者との対話を重視してください"
            ]
        }
    
    async def _generate_structured_outline(self, course_info: Dict[str, Any], basic_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        構造的なアウトライン形式で講座内容を生成
        
        Args:
            course_info: 講座情報  
            basic_content: 基本コンテンツ
            
        Returns:
            構造化されたアウトライン
        """
        
        title = course_info.get('title', 'サンプル講座')
        target_audience = course_info.get('target_audience', '一般')
        difficulty = course_info.get('difficulty', '中級')
        duration = course_info.get('duration', 60)
        
        structured_sections = []
        
        for i, section in enumerate(basic_content.get('sections', []), 1):
            section_outline = {
                "section_number": f"{i}-1",
                "section_title": f"{section.get('title', '')}の全体像",
                "content": {
                    "講義の目的": f"{section.get('title', '')}の基本概念を理解し、実践的なスキルを身につけること。",
                    f"{section.get('title', '')}とは": f"{section.get('content', '')[:100]}...",
                    f"{section.get('title', '')}の重要性": [
                        "・実践的なスキル習得への第一歩",
                        "・{target_audience}にとって必要不可欠な知識",
                        f"・{difficulty}レベルでの理解と応用"
                    ],
                    f"{section.get('title', '')}の全体像": f"この分野は以下の主要な要素で構成されます。これらの要素が連携することで、総合的な理解が得られます。",
                    "具体的な解説": {}
                }
            }
            
            # キーポイントを構造化
            if section.get('key_points'):
                for j, point in enumerate(section.get('key_points', []), 1):
                    section_outline["content"]["具体的な解説"][f"{j}：{point}"] = f"{point}について詳しく解説します。実践的な視点から、具体的な手法とその効果について学習します。"
            
            # 演習情報の追加
            if section.get('exercises'):
                section_outline["content"]["補足"] = {
                    "実践演習": section.get('exercises', []),
                    "学習のポイント": "理論だけでなく、実際に hands-on で体験することで、確実なスキル習得を目指します。"
                }
            
            structured_sections.append(section_outline)
        
        return {
            "course_title": title,
            "course_metadata": {
                "対象者": target_audience,
                "難易度": difficulty,
                "想定時間": f"{duration}分",
                "学習目標": basic_content.get('learning_objectives', [])
            },
            "structured_sections": structured_sections,
            "resources": {
                "参考資料": basic_content.get('resources', []),
                "次のステップ": basic_content.get('next_steps', [])
            }
        }
    
    def _format_for_copy(self, content: Dict[str, Any]) -> str:
        """
        コンテンツをコピペしやすい形式にフォーマット
        
        Args:
            content: フォーマット対象のコンテンツ
            
        Returns:
            コピペ可能な文字列
        """
        
        if "script" in str(content).lower() or "sections" in content:
            # 話し言葉台本の場合
            formatted_text = f"# {content.get('title', '')}\n\n"
            
            if content.get('script_notes'):
                formatted_text += "## 講師用注意事項\n"
                for note in content.get('script_notes', []):
                    formatted_text += f"- {note}\n"
                formatted_text += "\n"
            
            for section in content.get('sections', []):
                formatted_text += f"## {section.get('section_type', '')} ({section.get('duration', 0)}分)\n\n"
                formatted_text += f"{section.get('script', '')}\n\n"
                formatted_text += "---\n\n"
            
            return formatted_text
            
        else:
            # 構造的アウトラインの場合
            formatted_text = f"# {content.get('course_title', '')}\n\n"
            
            # メタデータ
            if content.get('course_metadata'):
                formatted_text += "## 講座概要\n"
                metadata = content.get('course_metadata', {})
                formatted_text += f"- **対象者**: {metadata.get('対象者', '')}\n"
                formatted_text += f"- **難易度**: {metadata.get('難易度', '')}\n" 
                formatted_text += f"- **想定時間**: {metadata.get('想定時間', '')}\n\n"
                
                formatted_text += "### 学習目標\n"
                for objective in metadata.get('学習目標', []):
                    formatted_text += f"- {objective}\n"
                formatted_text += "\n"
            
            # 構造化セクション
            for section in content.get('structured_sections', []):
                formatted_text += f"## {section.get('section_number', '')}. {section.get('section_title', '')}\n\n"
                
                section_content = section.get('content', {})
                for key, value in section_content.items():
                    formatted_text += f"### ■ {key}\n\n"
                    
                    if isinstance(value, list):
                        for item in value:
                            formatted_text += f"{item}\n"
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            formatted_text += f"**{subkey}**\n{subvalue}\n\n"
                    else:
                        formatted_text += f"{value}\n"
                    formatted_text += "\n"
                
                formatted_text += "---\n\n"
            
            return formatted_text
    
    def create_demo_quality_metrics(self) -> Dict[str, Any]:
        """
        デモ用品質メトリクスを生成
        
        Returns:
            模擬品質評価データ
        """
        return {
            'completeness': random.uniform(85, 95),
            'consistency': random.uniform(80, 92), 
            'accuracy': random.uniform(88, 96),
            'usability': random.uniform(83, 94),
            'overall_score': random.uniform(84, 94),
            'total_sources': random.randint(8, 15),
            'total_words': random.randint(3000, 8000),
            'unique_domains': random.randint(5, 8)
        }