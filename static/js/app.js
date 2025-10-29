/**
 * 講座コンテンツ生成システム - フロントエンドアプリケーション
 * シュンスケ式戦術遂行システム v3.0.0 準拠
 */

class LectureGeneratorApp {
    constructor() {
        this.isGenerating = false;
        this.currentResult = null;
        this.parsedSections = [];
        this.currentSectionContent = null;
        this.phases = [
            { id: 1, name: '諜報活動（Web検索）', icon: 'fas fa-search' },
            { id: 2, name: 'コンテキストエンジニアリング', icon: 'fas fa-brain' },
            { id: 3, name: 'AI分析＆構造化', icon: 'fas fa-robot' },
            { id: 4, name: 'ゴールシーク最適化', icon: 'fas fa-target' },
            { id: 5, name: '品質保証＆完成', icon: 'fas fa-check-circle' }
        ];
        
        this.init();
    }

    init() {
        // イベントリスナーの設定（DOM要素の存在チェック付き）
        const addEventListenerSafely = (id, event, handler) => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener(event, handler);
                console.log(`✅ イベントリスナー追加: ${id}`);
            } else {
                console.warn(`⚠️ 要素が見つかりません: ${id}`);
            }
        };

        addEventListenerSafely('generateBtn', 'click', (e) => {
            e.preventDefault();
            this.generateAllSections();
        });

        addEventListenerSafely('downloadJSON', 'click', () => {
            this.downloadJSON();
        });

        addEventListenerSafely('viewContent', 'click', () => {
            this.toggleContentPreview();
        });

        addEventListenerSafely('copyScript', 'click', () => {
            this.copySpokenScript();
        });

        addEventListenerSafely('copyOutline', 'click', () => {
            this.copyStructuredOutline();
        });

        // 新機能のイベントリスナー
        addEventListenerSafely('analyzeOutlineBtn', 'click', (e) => {
            e.preventDefault();
            console.log('🔍 目次解析ボタンがクリックされました');
            this.analyzeOutline();
        });

        // 目次内容変更時の処理
        addEventListenerSafely('courseOutline', 'input', () => {
            this.onOutlineChange();
        });

        // 初期状態でも目次を確認
        this.onOutlineChange();

        console.log('🎯 講座生成システム初期化完了');
    }

    async handleSubmit() {
        if (this.isGenerating) return;

        const formData = new FormData(document.getElementById('lectureForm'));
        const data = Object.fromEntries(formData.entries());

        // バリデーション
        if (!data.course_title.trim() || !data.outline.trim()) {
            this.showError('講座タイトルと目次は必須です。');
            return;
        }

        this.isGenerating = true;
        this.showLoadingState();
        this.startPhaseAnimation();

        try {
            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`サーバーエラー: ${response.status}`);
            }

            const result = await response.json();
            this.currentResult = result;
            this.showSuccess(result);

        } catch (error) {
            console.error('Generation error:', error);
            this.showError(error.message || 'システムエラーが発生しました。');
        } finally {
            this.isGenerating = false;
            this.hideLoadingState();
        }
    }

    async generateAllSections() {
        // セクションが解析されているか確認
        if (!this.parsedSections || this.parsedSections.length === 0) {
            this.showToast('まず「目次を解析してセクション別ボタンを表示」をクリックしてください', 'error');
            return;
        }

        if (this.isGenerating) {
            this.showToast('既に生成処理が実行中です', 'error');
            return;
        }

        const formData = new FormData(document.getElementById('lectureForm'));
        const courseData = Object.fromEntries(formData.entries());

        // 確認ダイアログ
        const confirmed = confirm(`${this.parsedSections.length}個のセクションを順番に生成します。\n完了まで時間がかかる場合があります。\n\n続行しますか？`);
        if (!confirmed) return;

        this.isGenerating = true;

        // ボタンを無効化
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>全セクション生成中...';

        let successCount = 0;
        let errorCount = 0;

        try {
            for (let i = 0; i < this.parsedSections.length; i++) {
                const section = this.parsedSections[i];

                this.showToast(`セクション ${i + 1}/${this.parsedSections.length}: 「${section.title}」を生成中...`, 'info');

                try {
                    // セクションの生成ボタンをプログラム的にトリガー
                    await this.generateSectionContent(section, courseData, this.parsedSections);
                    successCount++;

                    // 少し待機（API制限対策）
                    if (i < this.parsedSections.length - 1) {
                        await new Promise(resolve => setTimeout(resolve, 1000));
                    }
                } catch (error) {
                    console.error(`セクション「${section.title}」の生成エラー:`, error);
                    errorCount++;
                    this.showToast(`セクション「${section.title}」の生成に失敗しました`, 'error');
                }
            }

            // 完了メッセージ
            if (errorCount === 0) {
                this.showToast(`✅ 全${successCount}セクションの生成が完了しました！`, 'success');
            } else {
                this.showToast(`⚠️ 生成完了: 成功 ${successCount}件 / 失敗 ${errorCount}件`, 'error');
            }

        } catch (error) {
            console.error('一括生成エラー:', error);
            this.showToast('一括生成中にエラーが発生しました', 'error');
        } finally {
            this.isGenerating = false;

            // ボタンを有効化
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-bolt mr-2"></i>全セクションを一括生成する';
        }
    }

    showLoadingState() {
        document.getElementById('initialState').style.display = 'none';
        document.getElementById('resultsDisplay').style.display = 'none';
        document.getElementById('loadingState').style.display = 'block';
        document.getElementById('phaseIndicators').style.display = 'block';
        
        // ボタンを無効化
        const btn = document.getElementById('generateBtn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>生成中...';
    }

    hideLoadingState() {
        document.getElementById('loadingState').style.display = 'none';
        
        // ボタンを有効化
        const btn = document.getElementById('generateBtn');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-magic mr-2"></i>最高品質講座を生成する';
    }

    startPhaseAnimation() {
        let currentPhase = 1;
        const totalPhases = this.phases.length;
        
        const interval = setInterval(() => {
            // 前のフェーズを完了状態に
            if (currentPhase > 1) {
                const prevIndicator = document.querySelector(`[data-phase="${currentPhase - 1}"]`);
                prevIndicator.classList.remove('phase-active');
                prevIndicator.classList.add('phase-completed');
            }

            // 現在のフェーズをアクティブ状態に
            if (currentPhase <= totalPhases) {
                const currentIndicator = document.querySelector(`[data-phase="${currentPhase}"]`);
                currentIndicator.classList.add('phase-active');
            }

            currentPhase++;

            // 全フェーズ完了で停止
            if (currentPhase > totalPhases + 1) {
                clearInterval(interval);
            }
        }, 3000); // 3秒間隔
    }

    showSuccess(result) {
        document.getElementById('phaseIndicators').style.display = 'none';
        document.getElementById('resultsDisplay').style.display = 'block';
        
        // フェーズインジケーターをリセット
        document.querySelectorAll('.phase-indicator').forEach(indicator => {
            indicator.classList.remove('phase-active', 'phase-completed');
            indicator.classList.add('bg-gray-200', 'text-gray-600');
        });
        
        console.log('✅ 講座生成完了:', result);
    }

    showError(message) {
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('phaseIndicators').style.display = 'none';
        document.getElementById('initialState').style.display = 'block';
        
        // エラートーストを表示
        this.showToast(message, 'error');
        
        console.error('❌ エラー:', message);
    }

    downloadJSON() {
        if (!this.currentResult) return;

        const dataStr = JSON.stringify(this.currentResult, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `lecture_${Date.now()}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();

        this.showToast('JSONファイルをダウンロードしました', 'success');
    }

    toggleContentPreview() {
        const preview = document.getElementById('contentPreview');
        const display = document.getElementById('contentDisplay');
        
        if (preview.style.display === 'none') {
            this.renderContentPreview();
            preview.style.display = 'block';
            preview.scrollIntoView({ behavior: 'smooth' });
        } else {
            preview.style.display = 'none';
        }
    }

    renderContentPreview() {
        if (!this.currentResult) return;

        const display = document.getElementById('contentDisplay');
        const content = this.currentResult.course_content;
        
        let html = `
            <div class="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg mb-6">
                <h4 class="text-2xl font-bold text-gray-800 mb-2">${content.title || '講座タイトル'}</h4>
                <div class="flex flex-wrap gap-2 text-sm">
                    <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
                        ⏱️ ${content.duration || 60}分
                    </span>
                    <span class="bg-green-100 text-green-800 px-3 py-1 rounded-full">
                        📊 品質スコア: ${this.currentResult.quality_assurance?.content_quality_score || 0}%
                    </span>
                    <span class="bg-purple-100 text-purple-800 px-3 py-1 rounded-full">
                        📚 情報源: ${this.currentResult.quality_assurance?.sources_analyzed || 0}個
                    </span>
                </div>
            </div>
        `;

        // 学習目標
        if (content.learning_objectives) {
            html += `
                <div class="section-card bg-white p-6 rounded-lg shadow-sm mb-6">
                    <h5 class="text-xl font-bold text-gray-800 mb-4">
                        <i class="fas fa-bullseye mr-2 text-red-500"></i>学習目標
                    </h5>
                    <ul class="space-y-2">
                        ${content.learning_objectives.map(obj => 
                            `<li class="flex items-start">
                                <i class="fas fa-check-circle text-green-500 mr-2 mt-1"></i>
                                <span>${obj}</span>
                            </li>`
                        ).join('')}
                    </ul>
                </div>
            `;
        }

        // セクション
        if (content.sections) {
            content.sections.forEach((section, index) => {
                html += `
                    <div class="section-card bg-white p-6 rounded-lg shadow-sm mb-6">
                        <h5 class="text-xl font-bold text-gray-800 mb-4">
                            <i class="fas fa-play-circle mr-2 text-blue-500"></i>
                            ${section.title} 
                            <span class="text-sm font-normal text-gray-500">(${section.duration || 10}分)</span>
                        </h5>
                        
                        <div class="prose max-w-none text-gray-700 mb-4">
                            ${this.formatContent(section.content)}
                        </div>

                        ${section.key_points ? `
                            <div class="bg-yellow-50 p-4 rounded-lg mb-4">
                                <h6 class="font-semibold text-yellow-800 mb-2">
                                    <i class="fas fa-star mr-1"></i>重要ポイント
                                </h6>
                                <ul class="text-sm text-yellow-700 space-y-1">
                                    ${section.key_points.map(point => 
                                        `<li class="flex items-start">
                                            <i class="fas fa-arrow-right mr-2 mt-1"></i>
                                            ${point}
                                        </li>`
                                    ).join('')}
                                </ul>
                            </div>
                        ` : ''}

                        ${section.exercises ? `
                            <div class="bg-green-50 p-4 rounded-lg">
                                <h6 class="font-semibold text-green-800 mb-2">
                                    <i class="fas fa-tasks mr-1"></i>演習
                                </h6>
                                <ul class="text-sm text-green-700 space-y-1">
                                    ${section.exercises.map(exercise => 
                                        `<li>${exercise}</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                `;
            });
        } else if (typeof content.content === 'string') {
            // シンプルなテキストコンテンツの場合
            html += `
                <div class="section-card bg-white p-6 rounded-lg shadow-sm">
                    <div class="prose max-w-none text-gray-700">
                        ${this.formatContent(content.content)}
                    </div>
                </div>
            `;
        }

        display.innerHTML = html;
    }

    formatContent(content) {
        if (!content) return '';
        
        // 改行をHTMLに変換
        return content
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/^/, '<p>')
            .replace(/$/, '</p>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    copySpokenScript() {
        if (!this.currentResult || !this.currentResult.course_content) {
            this.showToast('講座を生成してから台本をコピーしてください', 'error');
            return;
        }

        const spokenScript = this.currentResult.course_content.spoken_script;
        const copyableScript = this.currentResult.course_content.output_formats?.copyable_script;

        if (spokenScript || copyableScript) {
            const textToCopy = copyableScript || this.formatSpokenScript(spokenScript);
            this.copyToClipboard(textToCopy, '話し言葉台本をクリップボードにコピーしました！');
        } else {
            this.showToast('話し言葉台本が見つかりません', 'error');
        }
    }

    copyStructuredOutline() {
        if (!this.currentResult || !this.currentResult.course_content) {
            this.showToast('講座を生成してからアウトラインをコピーしてください', 'error');
            return;
        }

        const structuredOutline = this.currentResult.course_content.structured_outline;
        const copyableOutline = this.currentResult.course_content.output_formats?.copyable_outline;

        if (structuredOutline || copyableOutline) {
            const textToCopy = copyableOutline || this.formatStructuredOutline(structuredOutline);
            this.copyToClipboard(textToCopy, '構造的アウトラインをクリップボードにコピーしました！');
        } else {
            this.showToast('構造的アウトラインが見つかりません', 'error');
        }
    }

    formatSpokenScript(script) {
        if (!script) return '';
        
        let formatted = `# ${script.title || '講座台本'}\n\n`;
        
        if (script.script_notes) {
            formatted += '## 講師用注意事項\n';
            script.script_notes.forEach(note => {
                formatted += `- ${note}\n`;
            });
            formatted += '\n';
        }

        if (script.sections) {
            script.sections.forEach(section => {
                formatted += `## ${section.section_type} (${section.duration}分)\n\n`;
                formatted += `${section.script}\n\n`;
                formatted += '---\n\n';
            });
        }

        return formatted;
    }

    formatStructuredOutline(outline) {
        if (!outline) return '';

        let formatted = `# ${outline.course_title || '講座アウトライン'}\n\n`;

        if (outline.course_metadata) {
            formatted += '## 講座概要\n';
            const metadata = outline.course_metadata;
            formatted += `- **対象者**: ${metadata['対象者'] || ''}\n`;
            formatted += `- **難易度**: ${metadata['難易度'] || ''}\n`;
            formatted += `- **想定時間**: ${metadata['想定時間'] || ''}\n\n`;

            if (metadata['学習目標']) {
                formatted += '### 学習目標\n';
                metadata['学習目標'].forEach(objective => {
                    formatted += `- ${objective}\n`;
                });
                formatted += '\n';
            }
        }

        if (outline.structured_sections) {
            outline.structured_sections.forEach(section => {
                formatted += `## ${section.section_number}. ${section.section_title}\n\n`;
                
                if (section.content) {
                    for (const [key, value] of Object.entries(section.content)) {
                        formatted += `### ■ ${key}\n\n`;
                        
                        if (Array.isArray(value)) {
                            value.forEach(item => {
                                formatted += `${item}\n`;
                            });
                        } else if (typeof value === 'object') {
                            for (const [subkey, subvalue] of Object.entries(value)) {
                                formatted += `**${subkey}**\n${subvalue}\n\n`;
                            }
                        } else {
                            formatted += `${value}\n`;
                        }
                        formatted += '\n';
                    }
                }
                
                formatted += '---\n\n';
            });
        }

        return formatted;
    }

    async copyToClipboard(text, successMessage) {
        try {
            if (navigator.clipboard) {
                await navigator.clipboard.writeText(text);
                this.showToast(successMessage, 'success');
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                
                const successful = document.execCommand('copy');
                document.body.removeChild(textArea);
                
                if (successful) {
                    this.showToast(successMessage, 'success');
                } else {
                    throw new Error('Copy command failed');
                }
            }
        } catch (err) {
            console.error('クリップボードコピーエラー:', err);
            this.showToast('クリップボードへのコピーに失敗しました', 'error');
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-300 ${
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'success' ? 'bg-green-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        
        toast.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${
                    type === 'error' ? 'fa-exclamation-triangle' :
                    type === 'success' ? 'fa-check-circle' :
                    'fa-info-circle'
                } mr-2"></i>
                ${message}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    // 新機能のメソッド群

    onOutlineChange() {
        const outlineEl = document.getElementById('courseOutline');
        const analyzeBtn = document.getElementById('analyzeOutlineBtn');
        
        if (!outlineEl || !analyzeBtn) {
            console.warn('⚠️ 必要な要素が見つかりません:', { outlineEl: !!outlineEl, analyzeBtn: !!analyzeBtn });
            return;
        }
        
        const outline = outlineEl.value.trim();
        console.log('🔍 目次変更検知:', outline.length, '文字');
        
        // 目次解析ボタンは常に表示（hiddenクラスをHTMLから削除済み）
        // ボタンの有効/無効を切り替える
        if (outline.length >= 5) {
            analyzeBtn.disabled = false;
            console.log('✅ ボタン有効');
        } else {
            analyzeBtn.disabled = true;
            console.log('❌ ボタン無効');
            this.clearIndividualSections();
        }
    }

    async analyzeOutline() {
        console.log('📋 analyzeOutline関数が呼び出されました');
        
        const formData = new FormData(document.getElementById('lectureForm'));
        const data = Object.fromEntries(formData.entries());

        console.log('📝 フォームデータ:', data);

        if (!data.outline.trim()) {
            console.log('❌ 目次が空です');
            this.showToast('目次を入力してください', 'error');
            return;
        }

        try {
            const response = await fetch('/analyze-outline', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`サーバーエラー: ${response.status}`);
            }

            const result = await response.json();
            this.parsedSections = result.sections;
            this.createIndividualSections(result.sections, data);
            this.showToast(`${result.sections.length}個のセクションを検出しました`, 'success');

        } catch (error) {
            console.error('Outline analysis error:', error);
            // フォールバック: フロントエンドで簡易解析
            this.parsedSections = this.parseOutlineLocally(data.outline);
            this.createIndividualSections(this.parsedSections, data);
            this.showToast(`${this.parsedSections.length}個のセクションを検出しました（ローカル解析）`, 'success');
        }
    }

    parseOutlineLocally(outline) {
        const lines = outline.split('\n').filter(line => line.trim());
        const sections = [];

        lines.forEach((line, index) => {
            const trimmed = line.trim();
            // より詳細な番号パターンマッチング（1-1, 第1章, (1)など）
            const sectionMatch = trimmed.match(/^(\d+-\d+\.?|\d+\.\d+\.?|\d+\.?|第\d+[章節]\.?|[IVX]+\.?|\(\d+\)|\d+\)|[a-z]\)|[A-Z]\)|\*|\-|\•)/);
            
            if (sectionMatch || (!sectionMatch && trimmed.length > 0)) {
                let number, title;
                
                if (sectionMatch) {
                    // 番号部分を取得（括弧や点を適切に処理）
                    number = sectionMatch[1];
                    // 末尾の点や括弧を除去
                    if (number.endsWith('.') || number.endsWith(')')) {
                        number = number.slice(0, -1);
                    }
                    if (number.startsWith('(')) {
                        number = number.slice(1);
                    }
                    
                    title = trimmed.substring(sectionMatch[0].length).trim();
                } else {
                    number = (index + 1).toString();
                    title = trimmed;
                }
                
                sections.push({
                    id: `section_${index + 1}`,
                    number: number,
                    title: title,
                    original_line: trimmed,
                    index: index
                });
            }
        });

        return sections;
    }

    createIndividualSections(sections, courseData) {
        const container = document.getElementById('individualSections');
        const statusBadge = document.getElementById('sectionStatusBadge');
        const sectionCountElement = document.getElementById('sectionCount');
        const initialState = document.getElementById('sectionsInitialState');

        container.innerHTML = '';

        // 講座全体の想定時間を取得
        const totalDuration = parseInt(courseData.duration) || 60;
        const totalSections = sections.length;
        const estimatedDurationPerSection = Math.max(5, Math.floor(totalDuration / totalSections));

        sections.forEach((section, index) => {
            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'individual-section bg-white p-4 rounded-lg border border-gray-200';
            sectionDiv.setAttribute('data-section-id', section.id);
            
            sectionDiv.innerHTML = `
                <div class="mb-4">
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center">
                            <span class="bg-purple-100 text-purple-800 px-2 py-1 rounded text-sm mr-3 font-medium">
                                ${section.number}
                            </span>
                            <h3 class="text-lg font-semibold text-gray-800">${section.title}</h3>
                        </div>
                        <div class="flex items-center space-x-2">
                            <label class="text-sm text-gray-600">⏱️</label>
                            <input
                                type="number"
                                min="1"
                                max="120"
                                value="${estimatedDurationPerSection}"
                                class="w-16 px-2 py-1 border border-gray-300 rounded text-sm text-center focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                data-section-duration="${section.id}"
                            />
                            <span class="text-sm text-gray-600">分</span>
                        </div>
                    </div>
                    <div class="text-xs text-gray-500 ml-2">
                        推定時間: ${estimatedDurationPerSection}分 (全体: ${totalDuration}分 ÷ ${totalSections}セクション)
                    </div>
                </div>

                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        追加で入れ込みたい要素 <span class="text-gray-400">(任意)</span>
                    </label>
                    <textarea
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                        rows="2"
                        placeholder="例：具体的な事例、実践演習、特別な注意点など..."
                        data-section-additional="${section.id}"
                    ></textarea>
                </div>
                
                <button 
                    class="w-full section-generate-btn text-white px-4 py-3 rounded-lg font-medium flex items-center justify-center mb-4"
                    data-section-id="${section.id}"
                    data-section-index="${index}"
                >
                    <i class="fas fa-magic mr-2"></i>台本と構造化アウトラインを生成する
                </button>
                
                <div class="section-results" style="display: none;">
                    <!-- Generated content will be displayed here -->
                    <div class="border-t border-gray-200 pt-4 mt-4">
                        <div class="flex space-x-2 mb-4">
                            <button class="tab-btn active flex-1 px-4 py-2 text-sm font-medium rounded-lg bg-blue-50 text-blue-700" 
                                    data-tab="spoken-${section.id}">
                                <i class="fas fa-microphone mr-1"></i>話し言葉台本
                            </button>
                            <button class="tab-btn flex-1 px-4 py-2 text-sm font-medium rounded-lg bg-gray-100 text-gray-600"
                                    data-tab="structured-${section.id}">
                                <i class="fas fa-list mr-1"></i>構造化アウトライン
                            </button>
                        </div>
                        
                        <div class="tab-content-area">
                            <div class="tab-content-panel" data-panel="spoken-${section.id}">
                                <div class="bg-blue-50 p-3 rounded-lg mb-3 flex justify-between items-center">
                                    <span class="text-blue-800 font-medium">話し言葉台本</span>
                                    <button class="copy-btn bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                                            data-copy="spoken-${section.id}">
                                        <i class="fas fa-copy mr-1"></i>コピー
                                    </button>
                                </div>
                                <div class="content-display spoken-content" data-content="spoken-${section.id}">
                                    <!-- Spoken script content -->
                                </div>
                            </div>
                            
                            <div class="tab-content-panel" data-panel="structured-${section.id}" style="display: none;">
                                <div class="bg-green-50 p-3 rounded-lg mb-3 flex justify-between items-center">
                                    <span class="text-green-800 font-medium">構造化アウトライン</span>
                                    <button class="copy-btn bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                                            data-copy="structured-${section.id}">
                                        <i class="fas fa-copy mr-1"></i>コピー
                                    </button>
                                </div>
                                <div class="content-display structured-content" data-content="structured-${section.id}">
                                    <!-- Structured outline content -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // イベントリスナーの追加
            const generateBtn = sectionDiv.querySelector('.section-generate-btn');
            generateBtn.addEventListener('click', () => {
                this.generateSectionContent(section, courseData, sections);
            });
            
            // タブ切り替えイベント
            const tabBtns = sectionDiv.querySelectorAll('.tab-btn');
            tabBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    this.switchSectionTab(btn.dataset.tab, sectionDiv);
                });
            });
            
            // コピーボタンイベント
            const copyBtns = sectionDiv.querySelectorAll('.copy-btn');
            copyBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    this.copySectionContent(btn.dataset.copy, section);
                });
            });
            
            container.appendChild(sectionDiv);
        });
        
        // 状態を更新
        initialState.style.display = 'none';
        container.style.display = 'block';
        statusBadge.style.display = 'block';
        sectionCountElement.textContent = sections.length;
    }

    clearIndividualSections() {
        const container = document.getElementById('individualSections');
        const statusBadge = document.getElementById('sectionStatusBadge');
        const initialState = document.getElementById('sectionsInitialState');
        
        container.innerHTML = '';
        container.style.display = 'none';
        statusBadge.style.display = 'none';
        initialState.style.display = 'block';
        this.parsedSections = [];
    }

    async generateSectionContent(section, courseData, allSections) {
        const sectionDiv = document.querySelector(`[data-section-id="${section.id}"]`);
        const generateBtn = sectionDiv.querySelector('.section-generate-btn');
        const resultsDiv = sectionDiv.querySelector('.section-results');

        // 追加要素を取得
        const additionalInput = sectionDiv.querySelector(`[data-section-additional="${section.id}"]`);
        const additionalElements = additionalInput.value.trim();

        // セクションの個別時間を取得
        const durationInput = sectionDiv.querySelector(`[data-section-duration="${section.id}"]`);
        const sectionDuration = parseInt(durationInput.value) || 10;
        
        try {
            // ボタンを無効化
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>生成中...';
            
            // セクションを生成中状態に
            sectionDiv.classList.add('generating');
            
            // 進行状況表示を開始
            this.showMiniProgress(section.title);
            
            const requestData = {
                section: section,
                course_info: {
                    title: courseData.course_title,
                    outline: courseData.outline,
                    target_audience: courseData.target_audience,
                    duration: parseInt(courseData.duration),
                    tone: courseData.tone
                },
                context_sections: allSections,
                additional_elements: additionalElements,
                section_duration: sectionDuration
            };

            const response = await fetch('/generate-section', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`サーバーエラー: ${response.status}`);
            }

            const result = await response.json();
            this.displaySectionResults(result, sectionDiv);
            this.showToast(`「${section.title}」の生成が完了しました`, 'success');

        } catch (error) {
            console.error('Section generation error:', error);
            this.showToast(`生成エラー: ${error.message}`, 'error');
            
            // フォールバック処理
            const fallbackResult = this.generateFallbackSectionContent(section, courseData);
            this.displaySectionResults(fallbackResult, sectionDiv);
            
        } finally {
            // ボタンを復活
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-magic mr-2"></i>台本と構造化アウトラインを生成する';
            
            // 生成中状態を解除
            sectionDiv.classList.remove('generating');
            
            // 進行状況を非表示
            this.hideMiniProgress();
        }
    }

    generateFallbackSectionContent(section, courseData) {
        return {
            section_id: section.id,
            section_title: section.title,
            section_number: section.number,
            spoken_script: {
                section_title: section.title,
                duration: 10,
                script_parts: [
                    {
                        part_type: "導入",
                        duration: 2,
                        script: `それでは、${section.title}について学習していきましょう。このセクションでは重要な概念を中心に進めていきます。`,
                        speaker_notes: ["聴衆の注意を引くよう、明るいトーンで"],
                        visual_aids: ["セクションタイトルスライド"]
                    },
                    {
                        part_type: "本編", 
                        duration: 6,
                        script: `${section.title}について詳しく見ていきます。基本的な概念から実践的な応用まで段階的に学習しましょう。`,
                        speaker_notes: ["インタラクティブに進める"],
                        visual_aids: ["概念図", "実例スライド"]
                    },
                    {
                        part_type: "まとめ",
                        duration: 2,
                        script: `以上で${section.title}のセクションを終了します。重要なポイントを再度確認しましょう。`,
                        speaker_notes: ["要点を明確に整理"],
                        visual_aids: ["まとめスライド"]
                    }
                ],
                key_phrases: [section.title],
                interaction_points: ["理解度確認", "質疑応答"],
                transition_to_next: "次のセクションに進みます"
            },
            structured_outline: {
                section_title: section.title,
                section_number: section.number,
                structured_outline_text: `I. ${section.title}について

A. 学習目的
   1. ${section.title}の基本概念を理解する
   2. 実践的な活用方法を学ぶ
   3. 重要なポイントを把握する

B. ${section.title}とは
   1. 基本的な定義
      a. ${section.title}の意味と概念
      b. 関連する重要な用語
   2. 主要な特徴
      a. 基本的な性質や機能
      b. 他の概念との違い
   3. 重要性と必要性
      a. なぜ学習する必要があるのか
      b. 実務での応用場面

C. 学習のポイント
   1. 理解度チェック
      a. ${section.title}の基本概念が説明できるか
      b. 実例を挙げて説明できるか
   2. 実践演習
      a. 基本的な操作や手順の確認
      b. 実際の場面での応用練習

D. まとめ
   1. ${section.title}の要点整理
   2. 次のステップへの準備`
            },
            generation_metadata: {
                generated_at: new Date().toISOString(),
                model_used: "fallback_mode",
                quality_score: 75
            }
        };
    }

    displaySectionResults(content, sectionDiv) {
        const resultsDiv = sectionDiv.querySelector('.section-results');
        
        // 話し言葉台本を表示
        const spokenContent = sectionDiv.querySelector(`[data-content="spoken-${content.section_id}"]`);
        this.renderSpokenScriptInSection(content.spoken_script, spokenContent);
        
        // 構造化アウトラインを表示
        const structuredContent = sectionDiv.querySelector(`[data-content="structured-${content.section_id}"]`);
        this.renderStructuredOutlineInSection(content.structured_outline, structuredContent);
        
        // 結果エリアを表示
        resultsDiv.style.display = 'block';
        
        // 生成されたコンテンツをセクションデータに保存
        sectionDiv.sectionData = content;
    }

    renderSpokenScriptInSection(scriptData, display) {
        let html = `
            <div class="bg-blue-50 p-3 rounded-lg mb-3">
                <h4 class="text-base font-bold text-blue-800 mb-1">${scriptData.section_title}</h4>
                <p class="text-xs text-blue-600">推定時間: ${scriptData.duration}分</p>
            </div>
        `;
        
        if (scriptData.script_parts) {
            scriptData.script_parts.forEach((part, index) => {
                html += `
                    <div class="mb-4 border-l-4 border-blue-400 pl-3">
                        <h5 class="font-semibold text-gray-800 mb-2 text-sm">
                            ${part.part_type} (${part.duration}分)
                        </h5>
                        <div class="bg-gray-50 p-3 rounded-lg">
                            <p class="text-gray-800 leading-relaxed text-sm">${part.script}</p>
                        </div>
                    </div>
                `;
            });
        }
        
        display.innerHTML = html;
    }

    renderStructuredOutlineInSection(outlineData, display) {
        // 新しいstructured_outline_text形式の場合は、単一のテキストボックスで表示
        if (outlineData.structured_outline_text) {
            const html = `
                <div class="bg-green-50 p-3 rounded-lg mb-3">
                    <h4 class="text-base font-bold text-green-800">${outlineData.section_number}. ${outlineData.section_title}</h4>
                    <p class="text-sm text-green-600 mt-1">📋 構造化アウトライン（階層テキスト形式）</p>
                </div>
                <div class="bg-white border border-gray-200 rounded-lg">
                    <textarea 
                        class="w-full h-80 p-4 border-0 rounded-lg resize-none focus:ring-2 focus:ring-green-500 focus:outline-none text-sm font-mono"
                        readonly
                    >${outlineData.structured_outline_text}</textarea>
                </div>
                <div class="mt-3 text-right">
                    <button 
                        class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm transition duration-200 flex items-center justify-center ml-auto"
                        onclick="navigator.clipboard.writeText(\`${outlineData.structured_outline_text.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`).then(() => alert('アウトラインをコピーしました！'))"
                    >
                        <i class="fas fa-copy mr-1"></i>
                        アウトラインをコピー
                    </button>
                </div>
            `;
            display.innerHTML = html;
            return;
        }

        // 既存のマインドマップ形式の処理（後方互換性）
        let html = `
            <div class="bg-green-50 p-3 rounded-lg mb-3">
                <h4 class="text-base font-bold text-green-800">${outlineData.section_number}. ${outlineData.section_title}</h4>
                ${outlineData.central_concept ? `<p class="text-sm text-green-600 mt-1">💡 中心概念: ${outlineData.central_concept}</p>` : ''}
            </div>
        `;
        
        // マインドマップ構造の表示
        if (outlineData.mindmap_structure) {
            for (const [branchKey, branchData] of Object.entries(outlineData.mindmap_structure)) {
                html += `
                    <div class="mb-4 border-l-4 border-green-400 pl-3">
                        <h5 class="font-bold text-gray-800 mb-2 text-sm">${branchKey}</h5>
                        <div class="space-y-3">
                `;
                
                // 各ブランチの詳細を展開
                for (const [subKey, subData] of Object.entries(branchData)) {
                    html += `
                        <div class="bg-gray-50 p-2 rounded">
                            <h6 class="font-semibold text-gray-700 text-xs mb-1">${subKey}</h6>
                            ${Array.isArray(subData) ? `
                                <ul class="list-disc list-inside text-gray-600 space-y-1 text-xs pl-2">
                                    ${subData.map(item => `<li>${item}</li>`).join('')}
                                </ul>
                            ` : `
                                <p class="text-gray-600 text-xs">${subData}</p>
                            `}
                        </div>
                    `;
                }
                
                html += `
                        </div>
                    </div>
                `;
            }
        }
        
        // レビューチェックリストの表示
        if (outlineData.review_checklist) {
            html += `
                <div class="mb-4 border-l-4 border-blue-400 pl-3">
                    <h5 class="font-bold text-gray-800 mb-2 text-sm">📋 復習チェックリスト</h5>
                    <div class="space-y-1">
                        ${outlineData.review_checklist.map(item => `
                            <div class="flex items-start text-xs">
                                <span class="text-green-500 mr-1">${item.startsWith('✅') ? item.substring(0, 2) : '□'}</span>
                                <span class="text-gray-600">${item.replace('✅ ', '')}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // 記憶支援の表示
        if (outlineData.memory_aids && outlineData.memory_aids.length > 0) {
            html += `
                <div class="mb-4 border-l-4 border-purple-400 pl-3">
                    <h5 class="font-bold text-gray-800 mb-2 text-sm">🧠 記憶のコツ</h5>
                    <ul class="list-disc list-inside text-gray-600 space-y-1 text-xs">
                        ${outlineData.memory_aids.map(aid => `<li>${aid}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // 旧構造との互換性（フォールバック）
        if (!outlineData.mindmap_structure && outlineData.structure) {
            for (const [key, value] of Object.entries(outlineData.structure)) {
                html += `
                    <div class="mb-4 border-l-4 border-green-400 pl-3">
                        <h5 class="font-bold text-gray-800 mb-2 text-sm">${key}</h5>
                        <p class="text-gray-700 mb-2 text-sm">${value.description || ''}</p>
                        ${value.details ? `
                            <ul class="list-disc list-inside text-gray-600 space-y-1 text-sm">
                                ${value.details.map(detail => `<li>${detail}</li>`).join('')}
                            </ul>
                        ` : ''}
                    </div>
                `;
            }
        }
        
        display.innerHTML = html;
    }

    switchSectionTab(tabId, sectionDiv) {
        // セクション内のタブボタンの状態更新
        const tabBtns = sectionDiv.querySelectorAll('.tab-btn');
        tabBtns.forEach(btn => {
            btn.classList.remove('active', 'bg-blue-50', 'text-blue-700', 'bg-green-50', 'text-green-700');
            btn.classList.add('bg-gray-100', 'text-gray-600');
        });
        
        // セクション内のパネルの表示切り替え
        const panels = sectionDiv.querySelectorAll('.tab-content-panel');
        panels.forEach(panel => {
            panel.style.display = 'none';
        });
        
        // アクティブなタブとパネルを設定
        const activeBtn = sectionDiv.querySelector(`[data-tab="${tabId}"]`);
        const activePanel = sectionDiv.querySelector(`[data-panel="${tabId}"]`);
        
        if (activeBtn && activePanel) {
            activeBtn.classList.remove('bg-gray-100', 'text-gray-600');
            
            if (tabId.startsWith('spoken-')) {
                activeBtn.classList.add('bg-blue-50', 'text-blue-700');
            } else {
                activeBtn.classList.add('bg-green-50', 'text-green-700');
            }
            
            activeBtn.classList.add('active');
            activePanel.style.display = 'block';
        }
    }

    async copySectionContent(contentType, section) {
        // セクションDivからコンテンツデータを取得
        const sectionDiv = document.querySelector(`[data-section-id="${section.id}"]`);
        if (!sectionDiv || !sectionDiv.sectionData) {
            this.showToast('コピーするコンテンツがありません', 'error');
            return;
        }

        const sectionData = sectionDiv.sectionData;
        let textToCopy = '';
        
        if (contentType.startsWith('spoken-')) {
            textToCopy = this.formatSectionSpokenScript(sectionData.spoken_script);
            await this.copyToClipboard(textToCopy, 'セクション話し言葉台本をコピーしました！');
        } else if (contentType.startsWith('structured-')) {
            textToCopy = this.formatSectionStructuredOutline(sectionData.structured_outline);
            await this.copyToClipboard(textToCopy, 'セクション構造化アウトラインをコピーしました！');
        }
    }

    showMiniProgress(sectionTitle) {
        const progressDiv = document.getElementById('sectionProgress');
        const progressText = document.getElementById('progressText');
        const miniPhases = document.querySelectorAll('.mini-phase');
        
        // プログレステキストを更新
        progressText.textContent = `「${sectionTitle}」のコンテンツを生成中...`;
        
        // すべてのミニフェーズをリセット
        miniPhases.forEach(phase => {
            phase.classList.remove('active', 'completed');
        });
        
        // プログレス表示
        progressDiv.style.display = 'block';
        
        // ミニフェーズアニメーション
        let currentPhase = 1;
        const phases = miniPhases.length;
        
        const interval = setInterval(() => {
            if (currentPhase > 1) {
                const prevPhase = document.querySelector(`[data-mini-phase="${currentPhase - 1}"]`);
                if (prevPhase) {
                    prevPhase.classList.remove('active');
                    prevPhase.classList.add('completed');
                }
            }
            
            if (currentPhase <= phases) {
                const currentPhaseEl = document.querySelector(`[data-mini-phase="${currentPhase}"]`);
                if (currentPhaseEl) {
                    currentPhaseEl.classList.add('active');
                }
            }
            
            currentPhase++;
            
            if (currentPhase > phases + 1) {
                clearInterval(interval);
                // 最後のフェーズも完了状態に
                const lastPhase = document.querySelector(`[data-mini-phase="${phases}"]`);
                if (lastPhase) {
                    lastPhase.classList.remove('active');
                    lastPhase.classList.add('completed');
                }
            }
        }, 1000);
        
        // インターバルIDを保存（後で停止用）
        this.currentProgressInterval = interval;
    }
    
    hideMiniProgress() {
        const progressDiv = document.getElementById('sectionProgress');
        progressDiv.style.display = 'none';
        
        // アニメーションを停止
        if (this.currentProgressInterval) {
            clearInterval(this.currentProgressInterval);
            this.currentProgressInterval = null;
        }
        
        // ミニフェーズをリセット
        document.querySelectorAll('.mini-phase').forEach(phase => {
            phase.classList.remove('active', 'completed');
        });
    }

    formatSectionSpokenScript(scriptData) {
        let formatted = `# ${scriptData.section_title}\n\n`;
        formatted += `**推定時間**: ${scriptData.duration}分\n\n`;
        
        if (scriptData.script_parts) {
            scriptData.script_parts.forEach(part => {
                formatted += `## ${part.part_type} (${part.duration}分)\n\n`;
                formatted += `${part.script}\n\n`;
                formatted += '---\n\n';
            });
        }
        
        return formatted;
    }

    formatSectionStructuredOutline(outlineData) {
        // 新しいstructured_outline_text形式の場合は、そのまま返す
        if (outlineData.structured_outline_text) {
            return outlineData.structured_outline_text;
        }
        
        // 既存の形式のフォーマット処理（後方互換性）
        let formatted = `# ${outlineData.section_number}. ${outlineData.section_title}\n\n`;
        
        if (outlineData.structure) {
            for (const [key, value] of Object.entries(outlineData.structure)) {
                formatted += `## ${key}\n\n`;
                
                if (value.description) {
                    formatted += `${value.description}\n\n`;
                }
                
                if (value.details && value.details.length > 0) {
                    value.details.forEach(detail => {
                        formatted += `- ${detail}\n`;
                    });
                    formatted += '\n';
                }
                
                formatted += '---\n\n';
            }
        }
        
        return formatted;
    }

}

// アプリケーション初期化
document.addEventListener('DOMContentLoaded', () => {
    new LectureGeneratorApp();
});