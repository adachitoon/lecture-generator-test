#!/usr/bin/env python3
"""
コンテキストエンジニアリングサービス
シュンスケ式戦術遂行システム準拠のコンテキスト構造化モジュール

既存のシュンスケスカウトMCPシステムとの統合を行い、
収集した情報を講座生成に最適な形で構造化する。
"""

import os
import yaml
import json
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import asyncio
from datetime import datetime

class ContextEngineeringService:
    """
    コンテキストエンジニアリングサービス
    
    既存のシュンスケスカウトMCPシステムの機能を活用し、
    講座生成に特化したコンテキスト構造化を行う。
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # 出力ディレクトリの設定
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent.parent.parent / "data" / "contexts"
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # シュンスケスカウトMCPとの統合設定
        self.scout_mcp_dir = Path(__file__).parent.parent.parent.parent / "shunsuke-scout-mcp"
        
        self.logger.info(f"コンテキストエンジニアリングサービス初期化完了: {self.output_dir}")
    
    async def structure_lecture_context(self, 
                                      search_results: List[Dict[str, Any]],
                                      course_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        講座生成用のコンテキスト構造化
        
        Args:
            search_results: Web検索結果
            course_info: 講座情報
            
        Returns:
            構造化されたコンテキストデータ
        """
        try:
            # 1. 基本情報の整理
            context = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'course_title': course_info.get('title', ''),
                    'target_audience': course_info.get('target_audience', ''),
                    'difficulty': course_info.get('difficulty', ''),
                    'duration': course_info.get('duration', 60),
                    'total_sources': len(search_results)
                },
                'course_outline': self._parse_course_outline(course_info.get('outline', '')),
                'knowledge_base': await self._build_knowledge_base(search_results),
                'content_hierarchy': await self._create_content_hierarchy(search_results, course_info),
                'quality_metrics': self._calculate_quality_metrics(search_results)
            }
            
            # 2. YAMLファイルとして保存
            context_file = self.output_dir / f"lecture_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
            with open(context_file, 'w', encoding='utf-8') as f:
                yaml.dump(context, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            self.logger.info(f"コンテキスト構造化完了: {context_file}")
            
            return context
            
        except Exception as e:
            self.logger.error(f"コンテキスト構造化エラー: {e}")
            raise
    
    def _parse_course_outline(self, outline_text: str) -> Dict[str, Any]:
        """
        講座の目次テキストを構造化
        
        Args:
            outline_text: 目次テキスト
            
        Returns:
            構造化された目次データ
        """
        lines = [line.strip() for line in outline_text.split('\n') if line.strip()]
        
        structured_outline = {
            'raw_text': outline_text,
            'sections': [],
            'estimated_sections': len([l for l in lines if l.startswith(('1.', '2.', '3.', '4.', '5.', '-', '*'))]),
            'key_topics': []
        }
        
        current_section = None
        section_number = 0
        
        for line in lines:
            # 数字付きの見出しを検出
            if any(line.startswith(f'{i}.') for i in range(1, 20)):
                section_number += 1
                current_section = {
                    'number': section_number,
                    'title': line,
                    'subsections': [],
                    'key_points': []
                }
                structured_outline['sections'].append(current_section)
                
            # 箇条書きの検出
            elif line.startswith(('-', '*', '•')) and current_section:
                subsection = line.lstrip('-*• ')
                current_section['subsections'].append(subsection)
                
            # その他の重要なトピック
            elif line and not current_section:
                structured_outline['key_topics'].append(line)
        
        return structured_outline
    
    async def _build_knowledge_base(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        検索結果から知識ベースを構築
        
        Args:
            search_results: 検索結果のリスト
            
        Returns:
            構造化された知識ベース
        """
        knowledge_base = {
            'sources': [],
            'concepts': {},
            'examples': [],
            'references': []
        }
        
        concept_keywords = {}
        
        for result in search_results:
            # ソース情報の整理
            source_info = {
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'domain': result.get('url', '').split('/')[2] if result.get('url') else '',
                'relevance_score': result.get('relevance_score', 0),
                'word_count': result.get('word_count', 0),
                'content_summary': result.get('content', '')[:200] + '...' if len(result.get('content', '')) > 200 else result.get('content', '')
            }
            knowledge_base['sources'].append(source_info)
            
            # コンセプト抽出（簡易版）
            content = result.get('content', '').lower()
            
            # 技術的なキーワードを抽出
            tech_keywords = [
                'python', 'javascript', 'react', 'vue', 'angular', 'node.js',
                'api', 'database', 'sql', 'nosql', 'mongodb', 'postgresql',
                'machine learning', 'ai', 'deep learning', 'neural network',
                'cloud', 'aws', 'azure', 'gcp', 'docker', 'kubernetes',
                'frontend', 'backend', 'fullstack', 'microservices'
            ]
            
            for keyword in tech_keywords:
                if keyword in content:
                    if keyword not in concept_keywords:
                        concept_keywords[keyword] = []
                    concept_keywords[keyword].append({
                        'source': result.get('url', ''),
                        'context': self._extract_keyword_context(content, keyword)
                    })
            
            # 実例の抽出
            if any(indicator in content for indicator in ['example', '例', 'sample', 'demo', 'tutorial']):
                knowledge_base['examples'].append({
                    'source': result.get('title', ''),
                    'url': result.get('url', ''),
                    'snippet': result.get('snippet', '')
                })
        
        knowledge_base['concepts'] = concept_keywords
        
        return knowledge_base
    
    def _extract_keyword_context(self, content: str, keyword: str, window: int = 100) -> str:
        """
        キーワード周辺のコンテキストを抽出
        
        Args:
            content: コンテンツテキスト
            keyword: 対象キーワード
            window: 前後の文字数
            
        Returns:
            コンテキストテキスト
        """
        index = content.find(keyword)
        if index == -1:
            return ""
        
        start = max(0, index - window)
        end = min(len(content), index + len(keyword) + window)
        
        return content[start:end].strip()
    
    async def _create_content_hierarchy(self, 
                                      search_results: List[Dict[str, Any]],
                                      course_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        コンテンツの階層構造を作成
        
        Args:
            search_results: 検索結果
            course_info: 講座情報
            
        Returns:
            階層構造化されたコンテンツ
        """
        hierarchy = {
            'beginner': {'sources': [], 'concepts': [], 'weight': 0},
            'intermediate': {'sources': [], 'concepts': [], 'weight': 0},
            'advanced': {'sources': [], 'concepts': [], 'weight': 0}
        }
        
        # 難易度の判定キーワード
        difficulty_indicators = {
            'beginner': ['basic', 'introduction', 'getting started', '入門', '基礎', '初心者'],
            'intermediate': ['intermediate', 'practical', 'application', '実践', '応用', '中級'],
            'advanced': ['advanced', 'expert', 'optimization', 'performance', '上級', '最適化', 'アーキテクチャ']
        }
        
        for result in search_results:
            content_lower = result.get('content', '').lower()
            title_lower = result.get('title', '').lower()
            
            # 難易度の判定
            scores = {}
            for level, indicators in difficulty_indicators.items():
                score = sum(1 for indicator in indicators 
                          if indicator in content_lower or indicator in title_lower)
                scores[level] = score
            
            # 最も高いスコアの難易度に分類
            best_level = max(scores, key=scores.get) if any(scores.values()) else 'intermediate'
            
            hierarchy[best_level]['sources'].append({
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'relevance': result.get('relevance_score', 0)
            })
            
            hierarchy[best_level]['weight'] += result.get('relevance_score', 0)
        
        return hierarchy
    
    def _calculate_quality_metrics(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        コンテンツの品質メトリクスを計算
        
        Args:
            search_results: 検索結果
            
        Returns:
            品質メトリクス
        """
        if not search_results:
            return {
                'completeness': 0,
                'consistency': 0,
                'accuracy': 0,
                'usability': 0,
                'overall_score': 0
            }
        
        total_results = len(search_results)
        total_words = sum(result.get('word_count', 0) for result in search_results)
        avg_relevance = sum(result.get('relevance_score', 0) for result in search_results) / total_results
        
        # ドメインの多様性
        domains = set(result.get('url', '').split('/')[2] if result.get('url') else '' 
                     for result in search_results)
        domain_diversity = len(domains) / total_results if total_results > 0 else 0
        
        # 品質スコア計算
        completeness = min(total_results / 10, 1.0) * 100  # 10個以上で満点
        consistency = domain_diversity * 100  # ドメインの多様性
        accuracy = min(avg_relevance / 20, 1.0) * 100  # 関連スコア基準
        usability = min(total_words / 10000, 1.0) * 100  # 総文字数基準
        
        overall_score = (completeness + consistency + accuracy + usability) / 4
        
        return {
            'completeness': round(completeness, 2),
            'consistency': round(consistency, 2),
            'accuracy': round(accuracy, 2),
            'usability': round(usability, 2),
            'overall_score': round(overall_score, 2),
            'total_sources': total_results,
            'total_words': total_words,
            'unique_domains': len(domains)
        }
    
    def load_context_from_file(self, context_file: str) -> Dict[str, Any]:
        """
        保存されたコンテキストファイルを読み込み
        
        Args:
            context_file: コンテキストファイルのパス
            
        Returns:
            コンテキストデータ
        """
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"コンテキストファイル読み込みエラー: {e}")
            return {}