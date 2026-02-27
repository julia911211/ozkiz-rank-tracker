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

    let isRunning = false;
    let resultsData = [];

    // Load saved Super Save keywords from LocalStorage
    const saved = localStorage.getItem('superSaveKeywords_v2');
    if (saved) superSaveInput.value = saved;

    // Save to LocalStorage whenever modified
    superSaveInput.addEventListener('input', () => {
        localStorage.setItem('superSaveKeywords_v2', superSaveInput.value);
    });

    // Use startBtn for the click event
    startBtn.addEventListener('click', async () => {
        await startApiScan();
    });

    async function startApiScan() {
        if (isRunning) return; // Prevent multiple runs

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

        // 키워드 파싱 (줄바꿈 및 콤마 분리)
        const keywords = keywordsTxt.split(/[\n,]+/).map(k => k.trim()).filter(k => k);
        const superSaveKws = superSaveInput.value.split(/[\n,]+/).map(k => k.trim()).filter(k => k);
        const totalKeywords = keywords.length;

        if (totalKeywords === 0) return;

        // UI 초기화
        isRunning = true;
        startBtn.disabled = true;
        startBtn.innerHTML = '<span class="btn-icon">⏳</span> 스캔 중...';
        progressSection.classList.remove('hidden');
        resultsBody.innerHTML = '';
        resultsData = [];
        exportCsvBtn.disabled = true;

        for (let i = 0; i < totalKeywords; i++) {
            const kw = keywords[i];

            // 프로그레스 바 업데이트
            const percent = Math.round(((i) / totalKeywords) * 100);
            progressBar.style.width = `${percent}%`;
            progressCount.textContent = `${i} / ${totalKeywords}`;
            currentStatus.textContent = `'${kw}' 검색 중... (웹페이지 분석 중)`;

            try {
                // 백엔드 API 호출
                const response = await fetch('/api/search_single', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        keyword: kw,
                        target_brand: targetBrand,
                        super_save_keywords: superSaveKws
                    })
                });

                const data = await response.json();

                // 테이블에 결과 추가
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

            // 사람처럼 보이게 강제 딜레이 부여 (랜덤 2~4초)
            if (i < keywords.length - 1) {
                currentStatus.textContent = `네이버 보안 우회 중... (대기 시간)`;
                const delayStr = Math.floor(Math.random() * (4000 - 2000 + 1) + 2000);
                await new Promise(r => setTimeout(r, delayStr));
            }
        }

        // 스캔 완료
        progressBar.style.width = '100%';
        progressCount.textContent = `${keywords.length} / ${keywords.length}`;
        currentStatus.textContent = '모든 키워드 스캔 완료!';

        isRunning = false;
        startBtn.disabled = false;
        startBtn.innerHTML = '<span class="btn-icon">🚀</span> 새로운 스캔 시작';
        exportCsvBtn.disabled = false;
    }

    function appendResultRow(data) {
        const tr = document.createElement('tr');

        // 키워드 셀
        const keywordTd = document.createElement('td');
        keywordTd.innerHTML = `<strong>${data.keyword}</strong>`;
        tr.appendChild(keywordTd);

        // 에러 상태인 경우
        if (data.status === 'error') {
            const errorTd = document.createElement('td');
            errorTd.setAttribute('colspan', '5');
            errorTd.innerHTML = `<span style="color: var(--danger);">${data.message || '검색 실패'}</span>`;
            tr.appendChild(errorTd);
            resultsBody.appendChild(tr);
            return;
        }

        // 성공 상태인데 아이템이 없는 경우
        if (!data.target_items || data.target_items.length === 0) {
            const emptyTd = document.createElement('td');
            emptyTd.setAttribute('colspan', '5');
            emptyTd.innerHTML = `<span style="color: var(--text-secondary);">40위 내 검색 결과 없음</span>`;
            tr.appendChild(emptyTd);
            resultsBody.appendChild(tr);
            return;
        }

        // 최대 5개의 상품 셀 생성
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
                            <div class="product-mall">${item.mall}</div>
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

    // CSV 다운로드 기능
    exportCsvBtn.addEventListener('click', () => {
        if (resultsData.length === 0) return;

        let csvContent = "data:text/csv;charset=utf-8,\uFEFF"; // BOM 추가 (엑셀 한글 깨짐 방지)
        csvContent += "키워드,최고순위,상품명,상품링크\n";

        resultsData.forEach(row => {
            if (row.status === 'success') {
                const keyword = `"${row.keyword}"`;
                const topRank = row.top_rank;
                const topTitle = `"${row.top_title.replace(/"/g, '""')}"`;
                let link = "";
                if (row.target_items && row.target_items.length > 0) {
                    link = `"${row.target_items[0].link}"`;
                }
                csvContent += `${keyword},${topRank},${topTitle},${link}\n`;
            } else {
                csvContent += `"${row.keyword}","오류","${row.message}",""\n`;
            }
        });

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `쇼핑랭킹_결과_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
});
