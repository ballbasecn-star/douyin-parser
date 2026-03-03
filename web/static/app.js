/**
 * Douyin Parser — Frontend Logic
 */

// ==================== State ====================
let currentData = null;
let transcriptMode = 'off'; // off | local | groq | siliconflow

// 图片代理（绕过抖音 CDN Referer 限制）
function proxyImg(url) {
    if (!url) return '';
    return '/api/proxy/image?url=' + encodeURIComponent(url);
}

// ==================== Terminal Logs ====================
function clearLog() {
    const body = document.getElementById('terminalBody');
    body.innerHTML = '';
}

function appendLog(msg, type = 'info') {
    const body = document.getElementById('terminalBody');
    const line = document.createElement('div');
    line.className = 'log-line';

    // Time
    const timeSpan = document.createElement('span');
    timeSpan.className = 'log-time';
    const now = new Date();
    timeSpan.textContent = `[${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}]`;

    // Msg
    const msgSpan = document.createElement('span');
    msgSpan.className = `log-msg ${type}`;
    msgSpan.textContent = msg;

    line.appendChild(timeSpan);
    line.appendChild(msgSpan);
    body.appendChild(line);

    // Scroll to bottom
    body.scrollTop = body.scrollHeight;
}

// ==================== Init ====================
document.addEventListener('DOMContentLoaded', () => {
    checkCookieStatus();
    loadHistory();

    // Enter key to parse
    document.getElementById('urlInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') parseVideo();
    });

    // Settings button
    document.getElementById('settingsBtn').addEventListener('click', openSettings);
    document.getElementById('cookieIndicator').addEventListener('click', openSettings);

    // Groq key
    document.getElementById('groqKeyInput').value = groqApiKey;
    document.getElementById('siliconflowKeyInput').value = siliconflowApiKey;

    // Auto-refresh cookie status
    setInterval(checkCookieStatus, 30000);
});

// ==================== Cookie ====================
async function checkCookieStatus() {
    try {
        const res = await fetch('/api/cookie/status');
        const info = await res.json();
        const dot = document.getElementById('cookieDot');
        const label = document.getElementById('cookieLabel');

        if (info.exists) {
            dot.className = 'cookie-dot active';
            label.textContent = `Cookie 有效`;
        } else {
            dot.className = 'cookie-dot error';
            label.textContent = `未设置`;
        }
    } catch {
        document.getElementById('cookieDot').className = 'cookie-dot error';
        document.getElementById('cookieLabel').textContent = '连接失败';
    }
}

// ==================== Parse ====================
async function parseVideo() {
    const input = document.getElementById('urlInput');
    const url = input.value.trim();
    if (!url) {
        showToast('请输入抖音分享链接', 'error');
        input.focus();
        return;
    }

    const btn = document.getElementById('parseBtn');
    const btnText = btn.querySelector('.parse-btn-text');
    const btnLoader = btn.querySelector('.parse-btn-loader');

    // UI: loading
    btn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'flex';

    document.getElementById('resultSection').style.display = 'none';
    document.getElementById('errorCard').style.display = 'none';

    // 开启终端和骨架屏初始状态
    const terminal = document.getElementById('terminalContainer');
    terminal.style.display = 'block';
    clearLog();

    document.getElementById('transcriptBlock').style.display = 'none';
    document.getElementById('analysisBlock').style.display = 'none';
    document.getElementById('transcriptSkeleton').style.display = 'flex';
    document.getElementById('analysisSkeleton').style.display = 'flex';
    document.getElementById('transcriptBody').style.display = 'none';
    document.getElementById('analysisBody').style.display = 'none';
    document.getElementById('transcriptActions').style.display = 'none';
    document.getElementById('analysisActions').style.display = 'none';

    const enableTranscript = transcriptMode !== 'off';
    const useCloud = transcriptMode === 'groq' || transcriptMode === 'siliconflow';
    const cloudProvider = useCloud ? transcriptMode : 'groq';
    const model = document.getElementById('modelSelect').value;
    const aiModel = document.getElementById('aiModelInput') ? document.getElementById('aiModelInput').value : "Pro/deepseek-ai/DeepSeek-V3.2";

    appendLog('系统初始化，准备发送解析请求...', 'info');

    try {
        const payload = {
            url,
            transcript: enableTranscript,
            analyze: document.getElementById('analyzeToggle').checked && enableTranscript,
            cloud: useCloud,
            cloud_provider: cloudProvider,
            model,
            ai_model: aiModel
        };

        const res = await fetch('/api/parse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!res.body) throw new Error("ReadableStream 缺失，无法处理流");

        const reader = res.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            let boundary = buffer.indexOf('\n\n');
            while (boundary !== -1) {
                const chunk = buffer.slice(0, boundary);
                buffer = buffer.slice(boundary + 2);

                if (chunk.startsWith('data: ')) {
                    const dataStr = chunk.slice(6);
                    try {
                        const packet = JSON.parse(dataStr);
                        handleSSEPacket(packet, enableTranscript, document.getElementById('analyzeToggle').checked && enableTranscript);
                    } catch (e) {
                        console.error('SSE JSON 解析错误:', e, dataStr);
                    }
                }
                boundary = buffer.indexOf('\n\n');
            }
        }

    } catch (e) {
        showError(`请求失败: ${e.message}`);
        appendLog(`❌ 请求异常坠机: ${e.message}`, 'error');
    } finally {
        btn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

// 处理来自后端的 SSE 数据包
function handleSSEPacket(packet, expectTranscript, expectAnalysis) {
    if (packet.type === 'log') {
        const msg = packet.message;
        let type = 'info';
        if (msg.includes('❌') || msg.includes('失败')) type = 'error';
        if (msg.includes('⚠️')) type = 'warning';
        if (msg.includes('✅') || msg.includes('🎉')) type = 'success';
        appendLog(msg, type);
    }
    else if (packet.type === 'data') {
        currentData = Object.assign(currentData || {}, packet.data);

        if (packet.step === 'video_info') {
            document.getElementById('resultSection').style.display = 'block';
            renderBaseInfo(currentData);

            if (expectTranscript) document.getElementById('transcriptBlock').style.display = 'block';
            if (expectAnalysis) document.getElementById('analysisBlock').style.display = 'block';
        }
        else if (packet.step === 'transcript') {
            document.getElementById('transcriptSkeleton').style.display = 'none';
            document.getElementById('transcriptBody').style.display = 'block';
            document.getElementById('transcriptActions').style.display = 'flex';
            renderTranscript(currentData);
        }
        else if (packet.step === 'analysis') {
            document.getElementById('analysisSkeleton').style.display = 'none';
            document.getElementById('analysisBody').style.display = 'flex';
            document.getElementById('analysisActions').style.display = 'flex';
            renderAnalysis(currentData);
        }
    }
    else if (packet.type === 'finish') {
        if (packet.success) {
            addToHistory(currentData);
            showToast('流程圆满完成 ✅');
            appendLog('🎉 任务全部完成。', 'success');
        } else {
            showError(packet.error || '解析失败');
            appendLog(`❌ 流程被中断: ${packet.error}`, 'error');
            // Hide skeletons if failed
            document.getElementById('transcriptSkeleton').style.display = 'none';
            document.getElementById('analysisSkeleton').style.display = 'none';
        }
    }
}

// ==================== Sub Renderers ====================
function renderBaseInfo(data) {
    const coverImg = document.getElementById('resultCover');
    if (data.cover_url) {
        coverImg.src = proxyImg(data.cover_url);
        coverImg.onerror = () => { coverImg.style.display = 'none'; };
    }
    document.getElementById('resultDuration').textContent = data.duration_formatted || '00:00';
    document.getElementById('resultTitle').textContent = data.title || data.description || '';
    document.getElementById('authorName').textContent = data.author || '';
    document.getElementById('authorId').textContent = data.author_id ? `@${data.author_id}` : '';

    const avatarEl = document.getElementById('authorAvatar');
    if (data.author_avatar) {
        avatarEl.innerHTML = `<img src="${proxyImg(data.author_avatar)}" alt="">`;
    } else {
        avatarEl.textContent = '👤';
    }

    document.querySelector('#resultDate span').textContent = data.create_time_formatted || '';
    document.querySelector('#resultVideoId span').textContent = data.video_id || '';
    document.getElementById('statLikes').textContent = formatNumber(data.like_count);
    document.getElementById('statComments').textContent = formatNumber(data.comment_count);
    document.getElementById('statShares').textContent = formatNumber(data.share_count);
    document.getElementById('statCollects').textContent = formatNumber(data.collect_count);

    const tagsRow = document.getElementById('tagsRow');
    tagsRow.innerHTML = '';
    if (data.hashtags && data.hashtags.length) {
        data.hashtags.forEach(tag => {
            const el = document.createElement('span');
            el.className = 'tag';
            el.textContent = tag;
            tagsRow.appendChild(el);
        });
    }

    document.getElementById('descContent').textContent = data.description || '';
    document.getElementById('openOriginal').href = data.share_url || `https://www.douyin.com/video/${data.video_id}`;

    // 只在第一次展示基础信息时滚动
    document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderTranscript(data) {
    if (data.transcript) {
        document.getElementById('transcriptContent').textContent = data.transcript;
    }
}

function renderAnalysis(data) {
    const a = data.analysis;
    if (!a) return;

    // Hook
    document.getElementById('analysisHookText').textContent = a.hook_text || '无';
    const typeEl = document.getElementById('analysisHookType');
    if (a.hook_type) {
        typeEl.style.display = 'inline-block';
        typeEl.textContent = a.hook_type;
    } else {
        typeEl.style.display = 'none';
    }

    // Structure
    const structWrapper = document.getElementById('analysisStructWrapper');
    if (a.structure_type) {
        structWrapper.style.display = 'block';
        document.getElementById('analysisStructText').textContent = a.structure_type;
    } else {
        structWrapper.style.display = 'none';
    }

    // Retention
    const retWrapper = document.getElementById('analysisRetentionWrapper');
    if (a.retention_points && a.retention_points.length > 0) {
        retWrapper.style.display = 'block';
        const ul = document.getElementById('analysisRetentionList');
        ul.innerHTML = '';
        a.retention_points.forEach(pt => {
            const li = document.createElement('li');
            li.textContent = pt;
            ul.appendChild(li);
        });
    } else {
        retWrapper.style.display = 'none';
    }

    // Scenario
    const scWrapper = document.getElementById('analysisScenarioWrapper');
    if (a.scenario_expression && a.scenario_expression.length > 0) {
        scWrapper.style.display = 'block';
        const ul = document.getElementById('analysisScenarioList');
        ul.innerHTML = '';
        a.scenario_expression.forEach(pt => {
            const li = document.createElement('li');
            li.textContent = pt;
            ul.appendChild(li);
        });
    } else {
        scWrapper.style.display = 'none';
    }

    // CTA
    const ctaWrapper = document.getElementById('analysisCtaWrapper');
    if (a.cta) {
        ctaWrapper.style.display = 'block';
        document.getElementById('analysisCtaText').textContent = a.cta;
    } else {
        ctaWrapper.style.display = 'none';
    }
}

// ==================== Transcript Mode ====================
function setTranscript(mode) {
    transcriptMode = mode;
    document.querySelectorAll('#transcriptToggle .toggle-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.value === mode);
    });
    document.getElementById('modelGroup').style.display = mode === 'local' ? 'flex' : 'none';
    document.getElementById('analyzeGroup').style.display = mode !== 'off' ? 'flex' : 'none';

    // 如果关闭文案，自动关闭拆解
    if (mode === 'off') {
        document.getElementById('analyzeToggle').checked = false;
    }
}

// ==================== UI Helpers ====================
function toggleBlock(id) {
    const el = document.getElementById(id);
    el.classList.toggle('expanded');
}

function formatNumber(n) {
    if (!n) return '0';
    if (n >= 10000) return (n / 10000).toFixed(1) + '万';
    return n.toLocaleString();
}

function showError(msg) {
    document.getElementById('errorCard').style.display = 'flex';
    document.getElementById('errorText').textContent = msg;
}

function showToast(msg, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ==================== Copy ====================
function copyText(elementId) {
    const text = document.getElementById(elementId).textContent;
    navigator.clipboard.writeText(text).then(() => showToast('已复制 ✅'));
}

function copyAll() {
    if (!currentData) return;
    const parts = [
        `标题: ${currentData.title}`,
        `作者: ${currentData.author}`,
        `视频ID: ${currentData.video_id}`,
        `时长: ${currentData.duration_formatted}`,
        `发布时间: ${currentData.create_time_formatted}`,
        `点赞: ${currentData.like_count} | 评论: ${currentData.comment_count} | 分享: ${currentData.share_count} | 收藏: ${currentData.collect_count}`,
        `\n描述:\n${currentData.description}`,
    ];
    if (currentData.transcript) {
        parts.push(`\n语音转录:\n${currentData.transcript}`);
    }
    parts.push(`\n链接: ${currentData.share_url}`);
    navigator.clipboard.writeText(parts.join('\n')).then(() => showToast('已复制全部信息 ✅'));
}

function exportJSON() {
    if (!currentData) return;
    const blob = new Blob([JSON.stringify(currentData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `douyin_${currentData.video_id || 'video'}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('JSON 已导出 ✅');
}

// ==================== Settings ====================
function openSettings(e) {
    if (e) e.stopPropagation();
    document.getElementById('settingsModal').style.display = 'flex';
    updateCookieStatusDetail();
}

function closeSettings(e) {
    if (e && e.target !== e.currentTarget) return;
    document.getElementById('settingsModal').style.display = 'none';
}

async function updateCookieStatusDetail() {
    try {
        const res = await fetch('/api/cookie/status');
        const info = await res.json();
        const el = document.getElementById('cookieStatusDetail');
        if (info.exists) {
            el.innerHTML = `✅ Cookie 已设置<br>来源: ${info.source}<br>更新: ${info.timestamp}<br>长度: ${info.cookie_length} 字符`;
        } else {
            el.innerHTML = '⚠️ 未设置 Cookie，解析可能返回空数据';
        }
    } catch {
        document.getElementById('cookieStatusDetail').textContent = '❌ 无法连接服务';
    }
}

async function saveCookie() {
    const cookie = document.getElementById('cookieInput').value.trim();
    if (!cookie) { showToast('请输入 Cookie', 'error'); return; }

    try {
        const res = await fetch('/api/cookie/set', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cookie }),
        });
        const json = await res.json();
        if (json.success) {
            showToast('Cookie 已保存 ✅');
            document.getElementById('cookieInput').value = '';
            checkCookieStatus();
            updateCookieStatusDetail();
        } else {
            showToast(json.error || '保存失败', 'error');
        }
    } catch (e) {
        showToast(`保存失败: ${e.message}`, 'error');
    }
}

async function saveGroqKey() {
    const key = document.getElementById('groqKeyInput').value.trim();
    if (!key) { showToast('请输入 API Key', 'error'); return; }
    try {
        await fetch('/api/config/set', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ GROQ_API_KEY: key }),
        });
        document.getElementById('groqKeyInput').value = '';
        showToast('Groq API Key 已安全保存到服务器 ✅');
    } catch (e) { showToast('保存失败', 'error'); }
}

async function saveSiliconFlowKey() {
    const key = document.getElementById('siliconflowKeyInput').value.trim();
    if (!key) { showToast('请输入 API Key', 'error'); return; }
    try {
        await fetch('/api/config/set', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ SILICONFLOW_API_KEY: key }),
        });
        document.getElementById('siliconflowKeyInput').value = '';
        showToast('SiliconFlow API Key 已安全保存到服务器 ✅');
    } catch (e) { showToast('保存失败', 'error'); }
}

async function saveAiModel() {
    // 仅仅保存在本地UI，发送请求时携带
    const val = document.getElementById('aiModelInput').value.trim();
    if (!val) { showToast('请输入有效的模型名称', 'error'); return; }
    showToast(`AI 拆解模型已设置为: ${val} ✅`);
}

// ==================== History ====================
function addToHistory(data) {
    let history = JSON.parse(localStorage.getItem('parse_history') || '[]');
    history.unshift({
        video_id: data.video_id,
        title: data.title || data.description || '',
        author: data.author,
        cover_url: data.cover_url,
        time: new Date().toLocaleString(),
    });
    history = history.slice(0, 20);
    localStorage.setItem('parse_history', JSON.stringify(history));
    loadHistory();
}

function loadHistory() {
    const history = JSON.parse(localStorage.getItem('parse_history') || '[]');
    const section = document.getElementById('historySection');
    const list = document.getElementById('historyList');

    if (!history.length) { section.style.display = 'none'; return; }

    section.style.display = 'block';
    list.innerHTML = '';

    history.slice(0, 8).forEach(item => {
        const el = document.createElement('div');
        el.className = 'history-item';
        el.onclick = () => {
            document.getElementById('urlInput').value = `https://www.douyin.com/video/${item.video_id}`;
            parseVideo();
        };
        const coverSrc = item.cover_url ? proxyImg(item.cover_url) : '';
        el.innerHTML = `
            <img class="history-cover" src="${coverSrc}" alt="" onerror="this.style.display='none'">
            <div class="history-info">
                <div class="history-title">${escapeHtml(item.title)}</div>
                <div class="history-meta">${escapeHtml(item.author)} · ${item.time}</div>
            </div>
        `;
        list.appendChild(el);
    });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
