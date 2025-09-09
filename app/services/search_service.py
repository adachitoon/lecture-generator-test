#!/usr/bin/env python3
"""
Web検索統合サービス
シュンスケ式戦術遂行システム準拠のWeb検索モジュール
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import logging
from urllib.parse import urljoin, urlparse
import re
import time

class SearchService:
    """Web検索統合サービス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session_timeout = 30
        self.max_results_per_query = 10
        self.max_content_length = 5000
        
        # 検索対象となる信頼できるドメイン
        self.trusted_domains = [
            'wikipedia.org',
            'github.com',
            'stackoverflow.com',
            'medium.com',
            'qiita.com',
            'zenn.dev',
            'docs.python.org',
            'developer.mozilla.org',
            'reactjs.org',
            'vuejs.org',
            'angular.io',
            'nodejs.org'
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        self.logger.info("Web検索サービス初期化完了")
    
    async def search_multiple_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        複数の検索クエリを並行実行
        
        Args:
            queries: 検索クエリのリスト
            
        Returns:
            検索結果のリスト
        """
        all_results = []
        
        try:
            # 並行検索の実行
            tasks = [self._search_single_query(query) for query in queries]
            query_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 結果の統合
            for i, result in enumerate(query_results):
                if isinstance(result, Exception):
                    self.logger.error(f"クエリ '{queries[i]}' の検索失敗: {result}")
                    continue
                
                if isinstance(result, list):
                    all_results.extend(result)
            
            # 重複除去とスコアリング
            deduplicated_results = self._deduplicate_results(all_results)
            scored_results = self._score_results(deduplicated_results, queries)
            
            return scored_results[:20]  # 上位20件を返す
            
        except Exception as e:
            self.logger.error(f"複数クエリ検索エラー: {e}")
            return []
    
    async def _search_single_query(self, query: str) -> List[Dict[str, Any]]:
        """
        単一クエリの検索実行
        
        Args:
            query: 検索クエリ
            
        Returns:
            検索結果のリスト
        """
        results = []
        
        try:
            # Google Custom Search APIやSerp APIの代わりに
            # シンプルなWeb検索を実装
            search_results = await self._simple_web_search(query)
            
            # 各結果からコンテンツを抽出
            for result in search_results[:self.max_results_per_query]:
                content_data = await self._extract_content(result.get('url', ''))
                
                if content_data:
                    results.append({
                        'query': query,
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'snippet': result.get('snippet', ''),
                        'content': content_data.get('content', ''),
                        'extracted_at': content_data.get('extracted_at', ''),
                        'word_count': len(content_data.get('content', '').split()),
                        'relevance_score': 0  # 後でスコアリング
                    })
                    
                # レート制限対応
                await asyncio.sleep(0.5)
            
            return results
            
        except Exception as e:
            self.logger.error(f"単一クエリ検索エラー ({query}): {e}")
            return []
    
    async def _simple_web_search(self, query: str) -> List[Dict[str, Any]]:
        """
        シンプルなWeb検索（DuckDuckGo等の利用）
        
        Args:
            query: 検索クエリ
            
        Returns:
            基本的な検索結果
        """
        results = []
        
        try:
            # DuckDuckGoのインスタント結果APIを使用
            search_url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
                async with session.get(search_url, params=params, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 関連リンクを抽出
                        related_topics = data.get('RelatedTopics', [])
                        for topic in related_topics[:10]:
                            if 'FirstURL' in topic:
                                results.append({
                                    'title': topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else topic.get('Text', ''),
                                    'url': topic['FirstURL'],
                                    'snippet': topic.get('Text', '')
                                })
            
            # 信頼できるドメインからの結果を優先
            trusted_results = []
            other_results = []
            
            for result in results:
                domain = urlparse(result['url']).netloc.lower()
                if any(trusted_domain in domain for trusted_domain in self.trusted_domains):
                    trusted_results.append(result)
                else:
                    other_results.append(result)
            
            return trusted_results + other_results
            
        except Exception as e:
            self.logger.error(f"Web検索エラー: {e}")
            return self._fallback_search_results(query)
    
    async def _extract_content(self, url: str) -> Optional[Dict[str, Any]]:
        """
        URLからコンテンツを抽出
        
        Args:
            url: 対象URL
            
        Returns:
            抽出されたコンテンツ情報
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        return None
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 不要な要素を除去
                    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                        element.decompose()
                    
                    # メインコンテンツを抽出
                    content = ""
                    
                    # 一般的なコンテンツセレクタを試行
                    content_selectors = [
                        'article',
                        '.content',
                        '#content',
                        'main',
                        '.main-content',
                        '.post-content',
                        '.entry-content'
                    ]
                    
                    for selector in content_selectors:
                        elements = soup.select(selector)
                        if elements:
                            content = ' '.join([elem.get_text(strip=True) for elem in elements])
                            break
                    
                    # セレクタで見つからない場合は、body全体から抽出
                    if not content:
                        body = soup.find('body')
                        if body:
                            content = body.get_text(separator=' ', strip=True)
                    
                    # コンテンツの長さ制限
                    if len(content) > self.max_content_length:
                        content = content[:self.max_content_length] + "..."
                    
                    return {
                        'content': content,
                        'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'source_url': url
                    }
                    
        except Exception as e:
            self.logger.error(f"コンテンツ抽出エラー ({url}): {e}")
            return None
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        検索結果の重複除去
        
        Args:
            results: 検索結果のリスト
            
        Returns:
            重複除去された結果
        """
        seen_urls = set()
        deduplicated = []
        
        for result in results:
            url = result.get('url', '')
            if url not in seen_urls:
                seen_urls.add(url)
                deduplicated.append(result)
        
        return deduplicated
    
    def _score_results(self, results: List[Dict[str, Any]], queries: List[str]) -> List[Dict[str, Any]]:
        """
        検索結果のスコアリング
        
        Args:
            results: 検索結果のリスト
            queries: 元の検索クエリのリスト
            
        Returns:
            スコア付きの検索結果（高スコア順）
        """
        for result in results:
            score = 0
            
            # ドメインスコア
            domain = urlparse(result.get('url', '')).netloc.lower()
            if any(trusted_domain in domain for trusted_domain in self.trusted_domains):
                score += 20
            
            # コンテンツ量スコア
            word_count = result.get('word_count', 0)
            if word_count > 500:
                score += 10
            elif word_count > 200:
                score += 5
            
            # キーワードマッチスコア
            content_lower = result.get('content', '').lower()
            title_lower = result.get('title', '').lower()
            
            for query in queries:
                query_words = query.lower().split()
                for word in query_words:
                    if word in title_lower:
                        score += 5
                    if word in content_lower:
                        score += 2
            
            result['relevance_score'] = score
        
        # スコア順にソート
        return sorted(results, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    def _fallback_search_results(self, query: str) -> List[Dict[str, Any]]:
        """
        検索に失敗した場合のフォールバック結果
        
        Args:
            query: 検索クエリ
            
        Returns:
            基本的なフォールバック結果
        """
        return [
            {
                'title': f'{query}に関する一般的な情報',
                'url': 'https://example.com',
                'snippet': f'{query}について学習するための基本的な内容を生成します。',
                'content': f'{query}は重要なトピックです。基本的な概念から実践的な応用まで、段階的に学習することが効果的です。'
            }
        ]