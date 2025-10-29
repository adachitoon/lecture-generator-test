#!/usr/bin/env python3
"""
講座コンテンツ生成システム - メインアプリケーション
シュンスケ式戦術遂行システム v3.0.0 準拠

MVP機能:
- 目次入力フォーム
- Gemini API連携
- Web検索統合
- コンテキストエンジニアリング
- ゴールシークプロンプト生成
- 講義台本出力
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from typing import List, Dict, Any
import logging

# アプリケーション設定
app = FastAPI(
    title="講座コンテンツ生成システム",
    description="目次から最高品質の講義台本を自動生成",
    version="1.0.0"
)

# 静的ファイルとテンプレート設定
BASE_DIR = Path(__file__).parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """メインページ - 講座生成フォーム"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/debug", response_class=HTMLResponse)
async def debug(request: Request):
    """デバッグページ"""
    return templates.TemplateResponse("debug.html", {"request": request})

@app.post("/generate", response_class=JSONResponse)
async def generate_lecture(
    request: Request,
    course_title: str = Form(...),
    outline: str = Form(...),
    target_audience: str = Form(default="初心者"),
    duration: int = Form(default=60),
    tone: str = Form(default="通常")
):
    """
    講座コンテンツ生成エンドポイント
    
    Args:
        course_title: 講座タイトル
        outline: 講座の目次・概要
        target_audience: ターゲット受講者
        duration: 予定時間（分）
        tone: 口調・話し方のスタイル
    
    Returns:
        生成された講義台本のJSON
    """
    try:
        # ここで実際の生成処理を呼び出し
        from .generators.lecture_generator import LectureGenerator
        
        generator = LectureGenerator()
        result = await generator.generate_lecture_content({
            "title": course_title,
            "outline": outline,
            "target_audience": target_audience,
            "duration": duration,
            "tone": tone
        })
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"講座生成エラー: {str(e)}")
        
        # より親切なエラーメッセージを生成
        if "quota" in str(e).lower() or "429" in str(e):
            error_message = {
                "error_type": "API_QUOTA_EXCEEDED",
                "message": "Gemini APIの無料制限に到達しました。デモモードで講座を生成しています。",
                "suggestion": "完全なAI機能をご利用の場合は、しばらくお待ちいただくか、Gemini APIの有料プランをご検討ください。",
                "demo_available": True
            }
        elif "api" in str(e).lower():
            error_message = {
                "error_type": "API_ERROR", 
                "message": "AI APIでエラーが発生しました。デモモードで講座を生成します。",
                "suggestion": "インターネット接続とAPIキーの設定をご確認ください。",
                "demo_available": True
            }
        else:
            error_message = {
                "error_type": "SYSTEM_ERROR",
                "message": "システムエラーが発生しました。",
                "suggestion": "しばらく時間をおいてから再度お試しください。",
                "demo_available": False
            }
        
        return JSONResponse(
            status_code=200,  # あえて200で返してフロントエンドで処理
            content={
                "status": "warning",
                "error_info": error_message,
                "course_content": {
                    "title": course_title,
                    "content": "現在API制限により、デモモードで動作しています。基本的な機能は正常に動作しますが、AI生成機能は制限されています。",
                    "sections": []
                },
                "quality_assurance": {
                    "sources_analyzed": 0,
                    "content_quality_score": 0,
                    "optimization_applied": False
                }
            }
        )

@app.post("/analyze-outline", response_class=JSONResponse)
async def analyze_outline(
    request: Request,
    course_title: str = Form(...),
    outline: str = Form(...),
    target_audience: str = Form(default="初心者"),
    duration: int = Form(default=60),
    tone: str = Form(default="通常")
):
    """
    目次解析エンドポイント - 目次を個別セクションに分割
    
    Args:
        course_title: 講座タイトル
        outline: 講座の目次・概要
        target_audience: ターゲット受講者
        duration: 予定時間（分）
        tone: 口調・話し方のスタイル
    
    Returns:
        解析されたセクション情報
    """
    try:
        from .services.outline_parser_service import OutlineParserService
        
        parser = OutlineParserService()
        sections = parser.parse_outline(outline)
        
        # MECE検証
        validation = parser.validate_mece_structure(sections, course_title)
        
        # 学習パス生成
        course_info = {
            "title": course_title,
            "target_audience": target_audience,
            "duration": duration,
            "tone": tone
        }
        learning_path = parser.generate_learning_path(sections, course_info)
        
        return JSONResponse(content={
            "status": "success",
            "sections": sections,
            "validation": validation,
            "learning_path": learning_path,
            "total_sections": len(sections)
        })
        
    except Exception as e:
        logger.error(f"目次解析エラー: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "目次の解析に失敗しました",
                "error": str(e)
            }
        )

@app.post("/generate-section", response_class=JSONResponse)
async def generate_section_content(request: Request):
    """
    セクション別コンテンツ生成エンドポイント
    
    Args:
        request: JSONリクエスト（section, course_info, context_sectionsを含む）
    
    Returns:
        生成されたセクションコンテンツ
    """
    try:
        from .services.section_content_service import SectionContentService
        
        # リクエストボディを取得
        request_data = await request.json()
        
        section = request_data.get('section')
        course_info = request_data.get('course_info')
        context_sections = request_data.get('context_sections', [])
        additional_elements = request_data.get('additional_elements', '')
        section_duration = request_data.get('section_duration')

        if not section or not course_info:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "必要なデータが不足しています"
                }
            )

        # セクションコンテンツ生成
        service = SectionContentService()
        content = await service.generate_section_content(
            section=section,
            course_info=course_info,
            context_sections=context_sections,
            additional_elements=additional_elements,
            section_duration=section_duration
        )
        
        return JSONResponse(content={
            "status": "success",
            **content
        })
        
    except Exception as e:
        logger.error(f"セクションコンテンツ生成エラー: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "セクションコンテンツの生成に失敗しました",
                "error": str(e)
            }
        )

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "operational", "service": "lecture-generator"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )