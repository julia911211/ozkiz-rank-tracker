document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('startBtn');
    const keywordInput = document.getElementById('keywords');
    const brandInput = document.getElementById('brandInput');
    const superSaveInput = document.getElementById('superSaveKeywords');
    const progressSection = document.getElementById('progressSection');
    const currentStatus = document.getElementById('currentStatus');
    const progressCount = document.getElementById('progressCount');
    const progressBar = document.getElementById('progressBar');
    const resultsBody = document.getElementById('resultsBody');
    const exportCsvBtn = document.getElementById('exportCsvBtn');

    // Tab Elements
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const historyBody = document.getElementById('historyBody');
    const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');

    let isRunning = false;
    let resultsData = [];

    // --- Tab Switching Logic ---
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-tab');

            // Toggle active class on buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Toggle active class on contents
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === target) {
                    content.classList.add('active');
                }
            });

            // If history tab, load data
            if (target === 'history-tab') {
                loadHistory();
            }
        });
    });

    // --- History Loading (Grid View) ---
    async function loadHistory() {
        historyBody.innerHTML = '<tr class="empty-row"><td colspan="2">데이터를 불러오는 중...</td></tr>';
        try {
            const response = await fetch('/api/get_history_grid');
            const data = await response.json();
            renderHistoryGrid(data);
        } catch (error) {
            console.error('History Error:', error);
            historyBody.innerHTML = '<tr class="empty-row"><td colspan="2" style="color: var(--danger);">히스토리를 불러오지 못했습니다.</td></tr>';
        }
    }

    function renderHistoryGrid(data) {
        const { dates, rows } = data;
        const headerRow = document.getElementById('historyHeaderRow');

        // 1. 헤더 초기화 및 날짜 추가
        headerRow.innerHTML = `
            <th style="min-width: 120px;">키워드</th>
            <th style="min-width: 250px;">연결 상품명</th>
        `;
        dates.forEach(date => {
            const th = document.createElement('th');
            th.style.minWidth = '100px';
            th.textContent = date.split('-').slice(1).join('/'); // MM/DD 형식
            headerRow.appendChild(th);
        });

        if (!dates || dates.length === 0 || !rows || rows.length === 0) {
            historyBody.innerHTML = `<tr class="empty-row"><td colspan="2">저장된 기록이 없습니다. 먼저 스캔을 시작해 주세요.</td></tr>`;
            return;
        }

        // 2. 바디 렌더링
        historyBody.innerHTML = '';
        let lastKeyword = null;

        rows.forEach(row => {
            const tr = document.createElement('tr');

            // 키워드가 바뀌는 시점에 구분선 추가를 위한 클래스
            if (lastKeyword !== null && lastKeyword !== row.keyword) {
                tr.classList.add('keyword-separator');
            }

            // 키워드명 (중복 제거 로직)
            const keywordDisplay = (row.keyword === lastKeyword) ? '<span class="hidden-keyword">' + row.keyword + '</span>' : `<strong>${row.keyword}</strong>`;
            lastKeyword = row.keyword;

            // 키워드 & 상품 정보 (고정 컬럼)
            tr.innerHTML = `
                <td class="keyword-cell">${keywordDisplay}</td>
                <td>
                    <div class="grid-product-cell">
                        <img src="${row.image}" class="grid-product-img" onerror="this.src='https://via.placeholder.com/40'">
                        <a href="${row.link}" target="_blank" class="grid-product-title" title="${row.title}">
                            ${row.title}
                        </a>
                    </div>
                </td>
            `;

            // 날짜별 순위 (동적 컬럼)
            row.history.forEach(h => {
                const td = document.createElement('td');
                td.style.textAlign = 'center';

                if (h.rank === '-') {
                    td.innerHTML = `<span style="color: var(--text-secondary);">-</span>`;
                } else {
                    let diffHtml = '';
                    if (h.is_new) {
                        diffHtml = `<span class="rank-new-badge">NEW</span>`;
                    } else if (h.diff !== null) {
                        if (h.diff > 0) diffHtml = `<span class="rank-diff diff-up" style="margin:0; font-size:0.7rem;">▲${h.diff}</span>`;
                        else if (h.diff < 0) diffHtml = `<span class="rank-diff diff-down" style="margin:0; font-size:0.7rem;">▼${Math.abs(h.diff)}</span>`;
                        else diffHtml = `<span class="rank-diff diff-stable" style="margin:0; font-size:0.7rem;">-</span>`;
                    }

                    td.innerHTML = `
                        <div class="rank-cell-content">
                            <span class="rank-value-text">${h.rank}</span>
                            ${diffHtml}
                        </div>
                    `;
                }
                tr.appendChild(td);
            });

            historyBody.appendChild(tr);
        });
    }

    refreshHistoryBtn.addEventListener('click', loadHistory);

    // --- Tracked Keywords Management ---
    const trackedKeywordsList = document.getElementById('trackedKeywordsList');
    const saveKeywordsBtn = document.getElementById('saveKeywordsBtn');

    async function loadTrackedKeywords() {
        try {
            const response = await fetch('/api/keywords');
            const data = await response.json();
            renderTrackedKeywords(data);
        } catch (error) {
            console.error('Load Keywords Error:', error);
        }
    }

    function renderTrackedKeywords(keywords) {
        if (!keywords || keywords.length === 0) {
            trackedKeywordsList.innerHTML = '<span class="no-keywords">등록된 자동 추적 키워드가 없습니다.</span>';
            return;
        }

        trackedKeywordsList.innerHTML = '';
        keywords.forEach(kw => {
            const span = document.createElement('span');
            span.className = 'keyword-tag';
            span.innerHTML = `
                ${kw.keyword}
                <span class="remove-kw" data-id="${kw.id}" data-keyword="${kw.keyword}">×</span>
            `;
            trackedKeywordsList.appendChild(span);
        });

        // 삭제 이벤트
        document.querySelectorAll('.remove-kw').forEach(btn => {
            btn.onclick = async (e) => {
                const kw = e.target.getAttribute('data-keyword');
                if (confirm(`'${kw}' 키워드를 자동 추적 목록에서 삭제할까요?`)) {
                    await updateMasterKeywords(keywords.filter(k => k.keyword !== kw).map(k => k.keyword));
                }
            };
        });
    }

    async function updateMasterKeywords(keywordArray) {
        try {
            const response = await fetch('/api/keywords', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    keywords: keywordArray,
                    target_brand: brandInput.value
                })
            });
            const result = await response.json();
            if (result.status === 'success') {
                loadTrackedKeywords();
            }
        } catch (error) {
            alert('키워드 저장 실패');
        }
    }

    saveKeywordsBtn.addEventListener('click', async () => {
        const keywordsTxt = keywordInput.value;
        const keywords = keywordsTxt.split(/[\n,]+/).map(k => k.trim()).filter(k => k);
        if (keywords.length === 0) {
            alert('입력창에 키워드를 먼저 입력해주세요.');
            return;
        }

        if (confirm(`${keywords.length}개의 키워드를 마스터 목록으로 등록하고 매일 자동 추적하시겠습니까?`)) {
            await updateMasterKeywords(keywords);
            alert('마스터 목록에 저장되었습니다. 이제 매일 새벽 자동으로 스캔됩니다!');
        }
    });

    // --- Master List Accordion Toggle ---
    const masterListToggle = document.getElementById('masterListToggle');
    const masterListPanel = document.getElementById('masterListPanel');
    const toggleIcon = document.getElementById('toggleIcon');

    if (masterListToggle) {
        masterListToggle.addEventListener('click', () => {
            const isCollapsed = masterListPanel.classList.toggle('collapsed');
            toggleIcon.style.transform = isCollapsed ? 'rotate(0deg)' : 'rotate(180deg)';
        });
    }

    // 초기 로드
    loadTrackedKeywords();

    // --- Existing Scan Logic ---
    const saved = localStorage.getItem('superSaveKeywords_v2');
    if (saved) superSaveInput.value = saved;

    superSaveInput.addEventListener('input', () => {
        localStorage.setItem('superSaveKeywords_v2', superSaveInput.value);
    });

    startBtn.addEventListener('click', async () => {
        await startApiScan();
    });

    async function startApiScan() {
        if (isRunning) return;

        const keywordsTxt = keywordInput.value;
        const targetBrand = brandInput.value.trim();

        if (!keywordsTxt.trim()) {
            alert('키워드를 1개 이상 입력해주세요.');
            return;
        }

        if (!targetBrand) {
            alert('타겟 브랜드명을 입력해주세요.');
            return;
        }

        const keywords = keywordsTxt.split(/[\n,]+/).map(k => k.trim()).filter(k => k);
        const superSaveKws = superSaveInput.value.split(/[\n,]+/).map(k => k.trim()).filter(k => k);
        const totalKeywords = keywords.length;

        if (totalKeywords === 0) return;

        isRunning = true;
        startBtn.disabled = true;
        startBtn.innerHTML = '<span class="btn-icon">⏳</span> 스캔 중...';
        progressSection.classList.remove('hidden');
        resultsBody.innerHTML = '';
        resultsData = [];
        exportCsvBtn.disabled = true;

        for (let i = 0; i < totalKeywords; i++) {
            const kw = keywords[i];

            const percent = Math.round(((i) / totalKeywords) * 100);
            progressBar.style.width = `${percent}%`;
            progressCount.textContent = `${i} / ${totalKeywords}`;
            currentStatus.textContent = `'${kw}' 검색 및 최신 히스토리 분석 중...`;

            try {
                const response = await fetch('/api/search_single', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        keyword: kw,
                        target_brand: targetBrand,
                        super_save_keywords: superSaveKws
                    })
                });

                const data = await response.json();
                appendResultRow(data);
                resultsData.push(data);

            } catch (error) {
                console.error(error);
                appendResultRow({
                    keyword: kw,
                    status: 'error',
                    message: '서버 통신 오류'
                });
            }

            if (i < keywords.length - 1) {
                currentStatus.textContent = `네이버 보안 우회 중... (안전한 검색 보장)`;
                const delayStr = Math.floor(Math.random() * (3000 - 1500 + 1) + 1500);
                await new Promise(r => setTimeout(r, delayStr));
            }
        }

        progressBar.style.width = '100%';
        progressCount.textContent = `${keywords.length} / ${keywords.length}`;
        currentStatus.textContent = '모든 키워드 스캔 및 실시간 히스토리 업데이트 완료!';

        isRunning = false;
        startBtn.disabled = false;
        startBtn.innerHTML = '<span class="btn-icon">🚀</span> 새로운 스캔 시작';
        exportCsvBtn.disabled = false;
    }

    function appendResultRow(data) {
        const tr = document.createElement('tr');

        const keywordTd = document.createElement('td');
        keywordTd.innerHTML = `<strong>${data.keyword}</strong>`;
        tr.appendChild(keywordTd);

        if (data.status === 'error') {
            const errorTd = document.createElement('td');
            errorTd.setAttribute('colspan', '5');
            errorTd.innerHTML = `<span style="color: var(--danger);">${data.message || '검색 실패'}</span>`;
            tr.appendChild(errorTd);
            resultsBody.appendChild(tr);
            return;
        }

        if (!data.target_items || data.target_items.length === 0) {
            const emptyTd = document.createElement('td');
            emptyTd.setAttribute('colspan', '5');
            emptyTd.innerHTML = `<span style="color: var(--text-secondary);">40위 내 검색 결과 없음</span>`;
            tr.appendChild(emptyTd);
            resultsBody.appendChild(tr);
            return;
        }

        for (let i = 0; i < 5; i++) {
            const td = document.createElement('td');
            const item = data.target_items[i];

            if (item) {
                let rankClass = 'rank-low';
                if (item.rank_display === '슈퍼적립') {
                    rankClass = 'rank-super';
                } else {
                    const r = parseInt(item.rank);
                    if (r <= 5) rankClass = 'rank-top';
                    else if (r <= 20) rankClass = 'rank-mid';
                }

                // 순위 변동 표시 (1순위 상품에만 표시)
                let diffHtml = '';
                if (i === 0 && data.rank_diff !== undefined && data.rank_diff !== null) {
                    const diff = data.rank_diff;
                    if (diff > 0) {
                        diffHtml = `<span class="rank-diff diff-up">▲ ${diff}</span>`;
                    } else if (diff < 0) {
                        diffHtml = `<span class="rank-diff diff-down">▼ ${Math.abs(diff)}</span>`;
                    } else {
                        diffHtml = `<span class="rank-diff diff-stable">-</span>`;
                    }
                }

                td.innerHTML = `
                    <div class="product-card">
                        <div class="product-img-wrapper">
                            <img src="${item.image}" alt="${item.title}" class="product-img">
                            <span class="rank-badge-floated ${rankClass}">${item.rank_display}</span>
                        </div>
                        <div class="product-info">
                            <a href="${item.link}" target="_blank" class="product-title" title="${item.title}">
                                ${item.title}
                            </a>
                            <div class="product-mall">${item.mall} ${diffHtml}</div>
                        </div>
                    </div>
                `;
            } else {
                td.innerHTML = `<div class="product-card empty">-</div>`;
            }
            tr.appendChild(td);
        }

        resultsBody.appendChild(tr);
    }

    exportCsvBtn.addEventListener('click', () => {
        if (resultsData.length === 0) return;

        let csvContent = "data:text/csv;charset=utf-8,\uFEFF";
        csvContent += "키워드,최고순위,순위변동,상품명,상품링크\n";

        resultsData.forEach(row => {
            if (row.status === 'success') {
                const keyword = `"${row.keyword}"`;
                const topRank = row.top_rank;
                const diff = row.rank_diff !== undefined && row.rank_diff !== null ? row.rank_diff : "신규";
                const topTitle = `"${row.top_title.replace(/"/g, '""')}"`;
                let link = "";
                if (row.target_items && row.target_items.length > 0) {
                    link = `"${row.target_items[0].link}"`;
                }
                csvContent += `${keyword},${topRank},${diff},${topTitle},${link}\n`;
            } else {
                csvContent += `"${row.keyword}","오류","-","${row.message}",""\n`;
            }
        });

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `쇼핑랭킹_히스토리포함_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
});
