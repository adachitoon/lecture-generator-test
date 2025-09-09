#!/usr/bin/env python3
"""
目次解析・セクション別コンテンツ生成サービス
MECE原則に基づく高品質カリキュラム設計システム
"""

import re
from typing import Dict, List, Any, Optional
import logging

class OutlineParserService:
    """目次解析・セクション別コンテンツ生成サービス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_outline(self, outline_text: str) -> List[Dict[str, Any]]:
        """
        目次テキストを解析して個別セクションに分割
        
        Args:
            outline_text: 目次テキスト
            
        Returns:
            セクション情報のリスト
        """
        sections = []
        
        # 改行で分割して各行を処理
        lines = [line.strip() for line in outline_text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            # 【第X章】のような中目次は除外
            if re.match(r'^【第\d+[章節]】', line):
                self.logger.debug(f"中目次をスキップ: {line}")
                continue
            
            # 小目次のみを認識（X-Y. 形式を優先）
            section_match = re.match(r'^(\d+-\d+\.?)', line)
            
            if section_match:
                # セクション番号と内容を分離
                section_number_raw = section_match.group(1)
                
                # 番号の正規化（点の処理）
                section_number = section_number_raw.rstrip('.')
                section_title = line[len(section_number_raw):].strip()
                
                sections.append({
                    'id': f'section_{len(sections)+1}',
                    'number': section_number,
                    'title': section_title,
                    'original_line': line,
                    'index': i,
                    'subsections': []
                })
                self.logger.debug(f"小目次を認識: {section_number} - {section_title}")
            elif sections and line.startswith((' ', '\t', '  ')):
                # インデントされた行はサブセクションとして扱う
                subsection_match = re.match(r'^\s*(\d+\.?\d*|[a-z]\)|[A-Z]\)|\*|\-|\•)', line)
                
                if subsection_match:
                    sub_number = subsection_match.group(1)
                    sub_title = line[len(sub_number):].strip()
                    
                    sections[-1]['subsections'].append({
                        'number': sub_number.rstrip('.'),
                        'title': sub_title,
                        'original_line': line.strip()
                    })
            # 他の番号パターンも許可（フォールバック用）
            elif not section_match:
                fallback_match = re.match(r'^(\d+\.?|\d+\.\d+\.?|第\d+[章節]\.?|[IVX]+\.?|\(\d+\)|\d+\)|[a-z]\)|[A-Z]\)|\*|\-|\•)', line)
                
                if fallback_match and not re.match(r'^【.*】', line):
                    section_number_raw = fallback_match.group(1)
                    
                    # 番号の正規化（括弧や点の処理）
                    section_number = section_number_raw
                    if section_number.endswith('.') or section_number.endswith(')'):
                        section_number = section_number[:-1]
                    if section_number.startswith('('):
                        section_number = section_number[1:]
                    
                    section_title = line[len(section_number_raw):].strip()
                    
                    sections.append({
                        'id': f'section_{len(sections)+1}',
                        'number': section_number,
                        'title': section_title,
                        'original_line': line,
                        'index': i,
                        'subsections': []
                    })
                    self.logger.debug(f"フォールバック認識: {section_number} - {section_title}")
        
        self.logger.info(f"目次解析完了: {len(sections)}個のセクションを検出")
        return sections
    
    def validate_mece_structure(self, sections: List[Dict[str, Any]], course_title: str) -> Dict[str, Any]:
        """
        MECE原則に基づくカリキュラム構造の検証
        
        Args:
            sections: セクションリスト
            course_title: 講座タイトル
            
        Returns:
            検証結果と改善提案
        """
        validation_result = {
            'is_valid': True,
            'issues': [],
            'suggestions': [],
            'mece_score': 0
        }
        
        # 1. 相互排他性（Mutually Exclusive）のチェック
        for i, section_a in enumerate(sections):
            for j, section_b in enumerate(sections[i+1:], i+1):
                similarity = self._calculate_content_similarity(section_a['title'], section_b['title'])
                if similarity > 0.7:
                    validation_result['issues'].append(
                        f"セクション{section_a['number']}と{section_b['number']}に内容の重複があります"
                    )
        
        # 2. 網羅性（Collectively Exhaustive）のチェック
        course_keywords = self._extract_keywords(course_title)
        covered_keywords = set()
        
        for section in sections:
            section_keywords = self._extract_keywords(section['title'])
            covered_keywords.update(section_keywords)
        
        coverage_ratio = len(covered_keywords.intersection(course_keywords)) / max(len(course_keywords), 1)
        
        # 3. 論理的順序性のチェック
        logical_flow_score = self._validate_logical_flow(sections, course_title)
        
        # 4. 実践バランスのチェック
        practical_balance_score = self._validate_practical_balance(sections)
        
        # 総合MECE スコアを計算
        mece_score = (
            (1.0 - len(validation_result['issues']) * 0.1) * 0.3 +  # 相互排他性
            coverage_ratio * 0.3 +  # 網羅性
            logical_flow_score * 0.2 +  # 論理性
            practical_balance_score * 0.2  # 実践性
        ) * 100
        
        validation_result['mece_score'] = max(0, min(100, mece_score))
        
        # 改善提案の生成
        if validation_result['mece_score'] < 80:
            validation_result['suggestions'].extend([
                "セクション間の重複を減らし、相互排他性を高めてください",
                "講座目標に対する網羅性を向上させてください",
                "学習者にとって自然な順序で構成してください",
                "理論と実践のバランスを調整してください"
            ])
        
        return validation_result
    
    def _calculate_content_similarity(self, text1: str, text2: str) -> float:
        """2つのテキストの類似度を計算"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _extract_keywords(self, text: str) -> set:
        """テキストからキーワードを抽出"""
        # 日本語の助詞・助動詞を除外するための簡易フィルタ
        stop_words = {'の', 'に', 'は', 'を', 'が', 'と', 'で', 'から', 'まで', 'より', 'への', 'による', '入門', '基礎', '応用', '実践'}
        
        # 単語に分割（簡易版）
        words = re.findall(r'[ぁ-んァ-ンa-zA-Z0-9]+', text)
        keywords = {word.lower() for word in words if word.lower() not in stop_words and len(word) > 1}
        
        return keywords
    
    def _validate_logical_flow(self, sections: List[Dict[str, Any]], course_title: str) -> float:
        """論理的な流れの妥当性を検証"""
        flow_patterns = {
            '入門': ['基礎', '概要', '理論', '実践', 'まとめ'],
            '基礎': ['入門', '概要', '詳細', '演習', '応用'],
            '応用': ['基礎', '発展', '実務', '事例', 'プロジェクト'],
            '実践': ['理論', '演習', '事例', 'ハンズオン', 'プロジェクト']
        }
        
        # コースのレベルを判定
        course_level = 'basic'
        for level_key in flow_patterns.keys():
            if level_key in course_title:
                course_level = level_key
                break
        
        # 順序の妥当性をスコア化（簡易版）
        score = 0.8  # デフォルトスコア
        
        # 明らかに逆順になっているパターンをチェック
        section_titles = [s['title'] for s in sections]
        for i, title in enumerate(section_titles[:-1]):
            next_title = section_titles[i+1]
            
            if ('まとめ' in title or '総括' in title) and i < len(section_titles) - 2:
                score -= 0.2  # まとめが最後でない
            if ('入門' in next_title or '基礎' in next_title) and ('応用' in title or '実践' in title):
                score -= 0.2  # 応用の後に基礎
        
        return max(0, score)
    
    def _validate_practical_balance(self, sections: List[Dict[str, Any]]) -> float:
        """理論と実践のバランスを検証"""
        theory_keywords = {'理論', '概念', '定義', '原理', '基礎知識', '背景', '歴史'}
        practice_keywords = {'実践', '演習', 'ハンズオン', 'プロジェクト', '事例', 'ケーススタディ', '実装', '開発'}
        
        theory_count = 0
        practice_count = 0
        
        for section in sections:
            title_lower = section['title'].lower()
            if any(keyword in title_lower for keyword in theory_keywords):
                theory_count += 1
            if any(keyword in title_lower for keyword in practice_keywords):
                practice_count += 1
        
        total_sections = len(sections)
        if total_sections == 0:
            return 0.0
        
        # 理想的なバランスは理論40%、実践60%
        theory_ratio = theory_count / total_sections
        practice_ratio = practice_count / total_sections
        
        ideal_theory = 0.4
        ideal_practice = 0.6
        
        balance_score = 1.0 - (
            abs(theory_ratio - ideal_theory) + 
            abs(practice_ratio - ideal_practice)
        ) / 2
        
        return max(0, balance_score)
    
    def generate_learning_path(self, sections: List[Dict[str, Any]], course_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        最短距離学習パスの生成
        
        Args:
            sections: セクションリスト
            course_info: 講座情報
            
        Returns:
            最適化された学習パス
        """
        learning_path = {
            'total_sections': len(sections),
            'estimated_total_duration': 0,
            'path': [],
            'prerequisites': {},
            'skill_progression': []
        }
        
        # 各セクションの難易度と所要時間を推定
        total_duration = course_info.get('duration', 60)
        section_duration = total_duration // max(len(sections), 1)
        
        for i, section in enumerate(sections):
            # 前提条件の分析
            prerequisites = []
            if i > 0:
                # 前のセクションが前提条件
                prerequisites.append(sections[i-1]['id'])
            
            # セクションの複雑さを分析
            complexity_score = self._analyze_section_complexity(section)
            adjusted_duration = int(section_duration * (0.5 + complexity_score))
            
            path_item = {
                'section_id': section['id'],
                'title': section['title'],
                'duration': adjusted_duration,
                'complexity': complexity_score,
                'prerequisites': prerequisites,
                'learning_objectives': self._generate_learning_objectives(section),
                'key_skills': self._extract_key_skills(section)
            }
            
            learning_path['path'].append(path_item)
            learning_path['estimated_total_duration'] += adjusted_duration
        
        return learning_path
    
    def _analyze_section_complexity(self, section: Dict[str, Any]) -> float:
        """セクションの複雑さを分析"""
        complex_keywords = {'応用', '実装', '開発', 'プロジェクト', '統合', '最適化', 'デバッグ'}
        simple_keywords = {'入門', '基礎', '概要', '紹介', '理解'}
        
        title = section['title'].lower()
        subsection_count = len(section.get('subsections', []))
        
        complexity = 0.5  # ベースライン
        
        if any(keyword in title for keyword in complex_keywords):
            complexity += 0.3
        if any(keyword in title for keyword in simple_keywords):
            complexity -= 0.2
        
        # サブセクションが多いほど複雑
        complexity += min(subsection_count * 0.1, 0.3)
        
        return max(0.1, min(1.0, complexity))
    
    def _generate_learning_objectives(self, section: Dict[str, Any]) -> List[str]:
        """セクションの学習目標を生成"""
        title = section['title']
        objectives = []
        
        # セクション内容に基づく目標生成（簡易版）
        if '入門' in title or '基礎' in title:
            objectives.append(f"{title}の基本概念を理解する")
            objectives.append(f"{title}の重要なポイントを説明できる")
        elif '実践' in title or '演習' in title:
            objectives.append(f"{title}を実際に行うことができる")
            objectives.append(f"{title}における問題を解決できる")
        elif '応用' in title:
            objectives.append(f"{title}を実務で活用できる")
            objectives.append(f"{title}の発展的な内容を理解する")
        else:
            objectives.append(f"{title}について説明できる")
            objectives.append(f"{title}を適切に活用できる")
        
        return objectives
    
    def _extract_key_skills(self, section: Dict[str, Any]) -> List[str]:
        """セクションのキースキルを抽出"""
        title = section['title']
        skills = []
        
        # タイトルから技術やスキルキーワードを抽出
        skill_patterns = [
            r'([A-Za-z]+(?:\s+[A-Za-z]+)?)',  # 英語の技術用語
            r'([ぁ-んァ-ン一-龯]{2,}(?:技術|スキル|手法|方法))',  # 日本語の技術用語
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, title)
            skills.extend(matches)
        
        # デフォルトスキルを追加
        if not skills:
            skills.append(f"{title}に関する知識")
        
        return list(set(skills))[:3]  # 上位3つまで