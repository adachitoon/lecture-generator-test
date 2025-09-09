#!/usr/bin/env python3
"""
Gemini API Key Rotation Manager
APIキー制限回避のためのローテーション管理
"""

import os
import logging
from typing import List, Optional
import time

class APIKeyManager:
    """Gemini APIキーのローテーション管理クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_keys = self._load_api_keys()
        self.current_index = 0
        self.key_usage_count = {}
        self.key_last_used = {}
        
        if not self.api_keys:
            raise Exception("GEMINI_API_KEYが設定されていません。最高品質のAI生成のみを提供します。")
        
        # 使用回数を初期化
        for key in self.api_keys:
            self.key_usage_count[key] = 0
            self.key_last_used[key] = 0
        
        self.logger.info(f"APIキーマネージャー初期化完了: {len(self.api_keys)}個のキーを管理")
    
    def _load_api_keys(self) -> List[str]:
        """環境変数からAPIキーを読み込み"""
        keys = []
        
        # メインのAPIキー
        main_key = os.getenv("GEMINI_API_KEY")
        if main_key:
            keys.append(main_key)
        
        # 追加のAPIキー（GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...）
        for i in range(1, 10):  # 最大9個の追加キーをサポート
            additional_key = os.getenv(f"GEMINI_API_KEY_{i}")
            if additional_key:
                keys.append(additional_key)
        
        # 重複を除去
        keys = list(set(keys))
        
        return keys
    
    def get_next_key(self) -> str:
        """次のAPIキーを取得（ローテーション）"""
        if not self.api_keys:
            raise Exception("利用可能なAPIキーがありません")
        
        # 現在時刻
        current_time = time.time()
        
        # レート制限を考慮してキーを選択
        selected_key = self._select_optimal_key(current_time)
        
        # 使用統計を更新
        self.key_usage_count[selected_key] += 1
        self.key_last_used[selected_key] = current_time
        
        # マスクされたキーでログ出力
        masked_key = self._mask_key(selected_key)
        self.logger.debug(f"APIキー使用: {masked_key} (使用回数: {self.key_usage_count[selected_key]})")
        
        return selected_key
    
    def _select_optimal_key(self, current_time: float) -> str:
        """最適なAPIキーを選択"""
        # 60秒以上使われていないキーを優先
        for key in self.api_keys:
            if current_time - self.key_last_used[key] >= 60:
                return key
        
        # 全てのキーが最近使われている場合、使用回数が最も少ないキーを選択
        min_usage_key = min(self.api_keys, key=lambda k: self.key_usage_count[k])
        
        # 最後の手段として、ラウンドロビン
        key = self.api_keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        
        return key
    
    def mark_key_error(self, api_key: str, error_type: str):
        """キーでエラーが発生した場合の記録"""
        masked_key = self._mask_key(api_key)
        self.logger.warning(f"APIキーエラー: {masked_key} - {error_type}")
        
        # 429エラー（レート制限）の場合、そのキーを一時的に避ける
        if "429" in error_type or "quota" in error_type.lower():
            self.key_last_used[api_key] = time.time() + 60  # 60秒間このキーを避ける
    
    def _mask_key(self, api_key: str) -> str:
        """APIキーをマスク（セキュリティのため）"""
        if len(api_key) <= 8:
            return "***"
        return api_key[:4] + "***" + api_key[-4:]
    
    def get_statistics(self) -> dict:
        """使用統計を取得"""
        return {
            "total_keys": len(self.api_keys),
            "key_usage": {self._mask_key(key): count for key, count in self.key_usage_count.items()},
            "current_index": self.current_index
        }