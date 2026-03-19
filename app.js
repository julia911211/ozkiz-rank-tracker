/**
 * Ozkiz Rank Tracker - Premium SaaS Edition
 * Complete Frontend Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- Elements ---
    const btnTabScan = document.getElementById('btn-tab-scan');
    const btnTabHistory = document.getElementById('btn-tab-history');
    const panelScan = document.getElementById('panel-scan');
    const panelHistory = document.getElementById('panel-history');
    
    const selectKeyword = document.getElementById('select-keyword');
    const inputSupersave = document.getElementById('input-supersave');
    const btnRunScan = document.getElementById('btn-run-scan');
    const btnOpenMaster = document.getElementById('btn-open-master');
    const btnDownloadCsv = document.getElementById('btn-download-csv');
    
    const scanEmpty = document.getElementById('scan-empty');
    const scanLoading = document.getElementById('scan-loading');
    const scanContent = document.getElementById('scan-content');
    const tbodyScan = document.getElementById('tbody-scan');
    
    const btnRefreshHistory = document.getElementById('btn-refresh-history');
    const btnUiClean = document.getElementById('btn-ui-clean');
    const tableHistory = document.getElementById('table-history');
    const theadHistory = document.getElementById('thead-history');
    const tbodyHistory = document.getElementById('tbody-history');
    
    const modalMaster = document.getElementById('modal-master');
    const btnCloseModal = document.getElementById('btn-close-modal');
    const textMasterInput = document.getElementById('text-master-input');
    const btnSaveMasterBulk = document.getElementById('btn-save-master-bulk');
    const listMasterKeywords = document.getElementById('list-master-keywords');

    let currentResults = JSON.parse(localStorage.getItem('last_scan_results') || '[]');
    let supersaveKeywords = JSON.parse(localStorage.getItem('supersave_keywords') || '[]');
    inputSupersave.value = supersaveKeywords.join(', ');

    // Persistence: Selected Keyword
    const savedSelectedKeyword = localStorage.getItem('last_selected_keyword');
    
    // Immediate save on input
    inputSupersave.addEventListener('input', () => {
        const val = inputSupersave.value;
        const ssk = val.split(',').map(s => s.trim()).filter(s => s);
        localStorage.setItem('supersave_keywords', JSON.stringify(ssk));
    });

    selectKeyword.addEventListener('change', () => {
        localStorage.setItem('last_selected_keyword', selectKeyword.value);
    });

    // Master keyword input persistence
    const savedMasterInput = localStorage.getItem('last_master_input');
    if (savedMasterInput) textMasterInput.value = savedMasterInput;
    
    textMasterInput.addEventListener('input', () => {
        localStorage.setItem('last_master_input', textMasterInput.value);
    });

    // --- Tab Logic ---
    function switchTab(tab) {
        if (tab === 'scan') {
            btnTabScan.classList.add('active');
            btnTabHistory.classList.remove('active');
            panelScan.classList.remove('hidden');
            panelHistory.classList.add('hidden');
        } else {
            btnTabScan.classList.remove('active');
            btnTabHistory.classList.add('active');
            panelScan.classList.add('hidden');
            panelHistory.classList.remove('hidden');
            loadHistory();
        }
    }

    btnTabScan.addEventListener('click', () => switchTab('scan'));
    btnTabHistory.addEventListener('click', () => switchTab('history'));

    // --- Master Modal Logic ---
    btnOpenMaster.addEventListener('click', () => {
        modalMaster.classList.remove('hidden');
        setTimeout(() => {
            modalMaster.classList.remove('opacity-0');
            modalMaster.firstElementChild.classList.remove('translate-y-4');
        }, 10);
        loadMasterKeywords();
    });

    const closeModal = () => {
        modalMaster.classList.add('opacity-0');
        modalMaster.firstElementChild.classList.add('translate-y-4');
        setTimeout(() => modalMaster.classList.add('hidden'), 300);
    };

    btnCloseModal.addEventListener('click', closeModal);
    modalMaster.addEventListener('click', (e) => { if (e.target === modalMaster) closeModal(); });

    // --- API Interactions ---

    async function loadMasterKeywords() {
        try {
            const response = await fetch('/api/keywords');
            const data = await response.json();
            
            if (data.error) {
                console.error('DB Error:', data.error);
                listMasterKeywords.innerHTML = `
                    <div class="p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm">
                        ⚠️ <strong>데이터베이스 연결 오류</strong><br>
                        <p class='mt-1 opacity-80'>${data.error}</p>
                        <p class='mt-2 text-[11px] font-bold underline'>Walkthrough 가이드를 확인하여 DB 주소를 수정해 주세요.</p>
                    </div>`;
                return;
            }
            
            renderMasterKeywords(data);
            
            // Update the select dropdown in scan panel
            selectKeyword.innerHTML = '<option value="">적용할 키워드 선택</option>';
            if (Array.isArray(data)) {
                data.forEach(kw => {
                    const opt = document.createElement('option');
                    opt.value = kw.keyword;
                    opt.textContent = `${kw.is_active ? '✅' : '💤'} ${kw.keyword}`;
                    selectKeyword.appendChild(opt);
                });
                
                // Restore selection if it exists in the new list
                if (savedSelectedKeyword) {
                    selectKeyword.value = savedSelectedKeyword;
                }
            }
        } catch (err) {
            console.error('Failed to load keywords:', err);
            listMasterKeywords.innerHTML = `
                <div class="p-4 bg-amber-50 border border-amber-100 rounded-xl text-amber-600 text-sm">
                    ⚠️ <strong>데이터 로드 실패</strong><br>
                    <p class='mt-1 opacity-80'>${err.message}</p>
                </div>`;
        }
    }

    function renderMasterKeywords(kws) {
        listMasterKeywords.innerHTML = '';
        if (kws.length === 0) {
            listMasterKeywords.innerHTML = '<p class="text-sm text-slate-400 py-4 text-center">등록된 키워드가 없습니다.</p>';
            return;
        }
        
        kws.forEach(kw => {
            const item = document.createElement('div');
            item.className = 'flex items-center justify-between p-4 bg-white rounded-xl border border-slate-100 hover:border-purple-200 transition-all group';
            item.innerHTML = `
                <div class="flex items-center gap-3">
                    <span class="status-dot ${kw.is_active ? 'bg-emerald-500' : 'bg-slate-300'}"></span>
                    <span class="font-bold text-slate-700">${kw.keyword}</span>
                </div>
                <div class="flex items-center gap-2">
                    <button class="scan-now-btn p-2 text-purple-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-all" 
                            title="즉시 스캔" data-keyword="${kw.keyword}">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                    </button>
                    <button class="toggle-btn px-3 py-1 text-[10px] font-black uppercase tracking-tighter rounded-lg border ${kw.is_active ? 'border-emerald-200 text-emerald-600' : 'border-slate-200 text-slate-400'}" 
                            data-keyword="${kw.keyword}" data-active="${kw.is_active}">
                        ${kw.is_active ? '활성' : '비활성'}
                    </button>
                    <button class="delete-btn opacity-0 group-hover:opacity-100 p-1 text-slate-300 hover:text-red-500 transition-all" data-keyword="${kw.keyword}">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                    </button>
                </div>
            `;
            listMasterKeywords.appendChild(item);
        });

        // Bind events
        listMasterKeywords.querySelectorAll('.toggle-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const kw = btn.dataset.keyword;
                const nextActive = btn.dataset.active === '1' ? 0 : 1;
                await toggleKeyword(kw, nextActive);
            });
        });

        listMasterKeywords.querySelectorAll('.scan-now-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const kw = btn.dataset.keyword;
                closeModal();
                selectKeyword.value = kw;
                btnRunScan.click();
            });
        });
    }

    async function toggleKeyword(keyword, is_active) {
        try {
            await fetch('/api/toggle_keyword_active', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword, is_active })
            });
            loadMasterKeywords();
            loadHistory();
        } catch (err) { console.error(err); }
    }

    btnSaveMasterBulk.addEventListener('click', async () => {
        const text = textMasterInput.value.trim();
        if (!text) return alert('키워드를 입력해주세요.');
        const keywords = text.split('\n').map(k => k.trim()).filter(k => k);
        
        try {
            btnSaveMasterBulk.disabled = true;
            btnSaveMasterBulk.textContent = '저장 중...';
            const response = await fetch('/api/keywords', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keywords })
            });
            const data = await response.json();
            if (data.status === 'success') {
                alert('키워드 목록이 업데이트 되었습니다.');
                loadMasterKeywords();
            } else {
                alert('저장 실패: ' + (data.message || '알 수 없는 오류'));
            }
        } catch (err) { alert('통신 실패: ' + err.message); }
        finally {
            btnSaveMasterBulk.disabled = false;
            btnSaveMasterBulk.textContent = '리스트 업데이트';
        }
    });

    // --- Scan Processing ---
    btnRunScan.addEventListener('click', async () => {
        const keyword = selectKeyword.value;
        if (!keyword) return alert('키워드를 선택해주세요.');
        
        const superSaveStr = inputSupersave.value;
        supersaveKeywords = superSaveStr.split(',').map(s => s.trim()).filter(s => s);
        localStorage.setItem('supersave_keywords', JSON.stringify(supersaveKeywords));
        
        scanEmpty.classList.add('hidden');
        scanLoading.classList.remove('hidden');
        scanContent.classList.add('hidden');
        
        try {
            const response = await fetch('/api/search_single', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword, target_brand: '오즈키즈', super_save_keywords: supersaveKeywords })
            });
            const data = await response.json();
            if (data.status === 'success') {
                renderScanResults(data);
                // Persistence
                localStorage.setItem('last_scan_results', JSON.stringify(data));
            } else {
                throw new Error(data.message || '스캔 실패');
            }
        } catch (err) {
            alert('오류 발생: ' + err.message);
            if (!currentResults || currentResults.length === 0) {
                scanEmpty.classList.remove('hidden');
            } else {
                scanContent.classList.remove('hidden');
            }
        } finally {
            scanLoading.classList.add('hidden');
        }
    });

    function renderScanResults(data) {
        if (!data || !data.target_items) {
            scanEmpty.classList.remove('hidden');
            scanContent.classList.add('hidden');
            return;
        }

        scanEmpty.classList.add('hidden');
        scanContent.classList.remove('hidden');
        tbodyScan.innerHTML = '';
        currentResults = data.target_items || [];
        
        if (currentResults.length === 0) {
            tbodyScan.innerHTML = '<tr><td colspan="3" class="px-6 py-10 text-center text-slate-400">발견된 상품이 없습니다.</td></tr>';
            return;
        }

        currentResults.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="px-6 py-4">
                    <span class="rank-badge ${item.rank <= 10 ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-600'}">
                        ${item.rank_display}
                    </span>
                    ${item.rank_diff ? `<span class="ml-2 text-[10px] font-bold ${item.rank_diff > 0 ? 'text-emerald-500' : 'text-rose-500'}">
                        ${item.rank_diff > 0 ? '▲' : '▼'}${Math.abs(item.rank_diff)}
                    </span>` : ''}
                </td>
                <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                        <img src="${item.image || ''}" class="w-10 h-10 rounded-lg object-cover bg-slate-100">
                        <div>
                            <p class="font-bold text-slate-700 line-clamp-1">${item.title}</p>
                            <p class="text-[10px] text-slate-400">브랜드: 오즈키즈</p>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4">
                    <a href="${item.link}" target="_blank" class="text-indigo-600 hover:text-indigo-800 font-bold transition-colors">상품보기 &rarr;</a>
                </td>
            `;
            tbodyScan.appendChild(row);
        });
    }

    // --- History Logic ---
    async function loadHistory() {
        tbodyHistory.innerHTML = '<tr><td colspan="10" class="py-20 text-center"><div class="loading-ring mx-auto mb-4"></div><p class="text-slate-400">데이터를 집계 중입니다...</p></td></tr>';
        try {
            const response = await fetch('/api/get_history_grid');
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            renderHistoryTable(data);
        } catch (err) {
            tbodyHistory.innerHTML = `<tr><td colspan="10" class="py-20 text-center text-rose-500 font-bold">⚠️ 오류: ${err.message}</td></tr>`;
        }
    }

    function renderHistoryTable(data) {
        const { dates, rows } = data;
        
        // Headers
        theadHistory.innerHTML = `
            <tr class="uppercase text-[10px] font-black text-slate-400 tracking-wider">
                <th class="px-6 py-4 text-left sticky left-0 bg-slate-50/95 backdrop-blur z-20 w-16">ON</th>
                <th class="px-6 py-4 text-left sticky left-16 bg-slate-50/95 backdrop-blur z-20">키워드</th>
                <th class="px-6 py-4 text-left border-r border-slate-100">최근 순위 상품</th>
                <th class="px-6 py-4 text-center">Trend</th>
                ${dates.map(d => `<th class="px-6 py-4 text-center whitespace-nowrap">${d.split('-').slice(1).join('/')}</th>`).join('')}
            </tr>
        `;

        tbodyHistory.innerHTML = '';
        if (rows.length === 0) {
            tbodyHistory.innerHTML = '<tr><td colspan="10" class="py-20 text-center text-slate-400">누적된 이력이 없습니다.</td></tr>';
            return;
        }

        rows.forEach(row => {
            const tr = document.createElement('tr');
            tr.className = row.is_active ? '' : 'opacity-40 grayscale';
            
            let dateCells = '';
            row.history.forEach(h => {
                let diffHtml = '';
                if (h.diff !== null && h.diff !== 0) {
                    const color = h.diff > 0 ? 'text-emerald-500' : 'text-rose-500';
                    const arrow = h.diff > 0 ? '▲' : '▼';
                    diffHtml = `<div class="${color} text-[8px] font-bold">${arrow}${Math.abs(h.diff)}</div>`;
                }
                dateCells += `<td class="px-4 py-4 text-center">
                    <div class="font-black text-slate-700 ${h.rank === '1위' ? 'text-purple-600' : ''}">${h.rank}</div>
                    ${diffHtml}
                </td>`;
            });

            tr.innerHTML = `
                <td class="px-6 py-4 sticky left-0 bg-white/95 backdrop-blur z-10">
                    <button class="small-toggle ${row.is_active ? 'active' : ''}" data-keyword="${row.keyword}" data-active="${row.is_active}">
                        <div class="knob"></div>
                    </button>
                </td>
                <td class="px-6 py-4 font-black text-slate-800 sticky left-16 bg-white/95 backdrop-blur z-10">${row.keyword}</td>
                <td class="px-6 py-4 border-r border-slate-50">
                    <div class="flex items-center gap-2">
                        <img src="${row.image || ''}" class="w-6 h-6 rounded bg-slate-100 object-cover">
                        <span class="text-[11px] font-medium text-slate-500 line-clamp-1 max-w-[150px]">${row.title}</span>
                    </div>
                </td>
                <td class="px-6 py-4">
                    <canvas id="spark-${row.keyword}-${row.title.substring(0,5)}" width="80" height="24" class="sparkline-canvas mx-auto"></canvas>
                </td>
                ${dateCells}
            `;
            tbodyHistory.appendChild(tr);
            
            // Draw Sparkline
            setTimeout(() => {
                const canvas = document.getElementById(`spark-${row.keyword}-${row.title.substring(0,5)}`);
                if (canvas) drawSpark(canvas, row.history.map(h => h.rank_value).filter(v => v !== null).reverse());
            }, 50);
        });

        // Small Toggle Bind
        tbodyHistory.querySelectorAll('.small-toggle').forEach(btn => {
            btn.addEventListener('click', () => {
                const kw = btn.dataset.keyword;
                const next = btn.dataset.active === '1' ? 0 : 1;
                toggleKeyword(kw, next);
            });
        });
    }

    function drawSpark(canvas, values) {
        if (values.length < 2) return;
        const ctx = canvas.getContext('2d');
        const max = Math.max(...values, 40);
        const min = Math.min(...values, 1);
        const range = max - min || 1;
        const w = canvas.width;
        const h = canvas.height;
        const step = w / (values.length - 1);
        
        ctx.beginPath();
        ctx.strokeStyle = '#7c3aed';
        ctx.lineWidth = 2;
        ctx.lineJoin = 'round';
        
        values.forEach((v, i) => {
            const x = i * step;
            // Rank 1 is top, Rank 40 is bottom
            const y = h - ((max - v) / range * (h - 4)) - 2;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();
    }

    btnRefreshHistory.addEventListener('click', loadHistory);
    btnUiClean.addEventListener('click', async () => {
        if (!confirm('테스트용 데이터들이 기록에서 모두 지워집니다. 진행하시겠습니까?')) return;
        try {
            await fetch('/api/clean_tests');
            loadHistory();
            loadMasterKeywords();
        } catch (err) { alert(err.message); }
    });

    // --- CSV Download ---
    btnDownloadCsv.addEventListener('click', () => {
        if (currentResults.length === 0) return;
        let csv = '순위,상품명,링크\n';
        currentResults.forEach(r => {
            csv += `"${r.rank_display}","${r.title.replace(/"/g, '""')}","${r.link}"\n`;
        });
        const blob = new Blob(["\ufeff" + csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `naver_rank_${new Date().toISOString().slice(0,10)}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // --- Bulk Scan Logic ---
    const btnBulkScan = document.getElementById('btn-bulk-scan');
    
    async function runBulkScan() {
        console.log('runBulkScan triggered - Sequential Mode');
        
        try {
            const superSaveStr = inputSupersave.value;
            const ssk = superSaveStr.split(',').map(s => s.trim()).filter(s => s);
            
            btnBulkScan.disabled = true;
            btnBulkScan.innerHTML = `<span>준비 중...</span>`;

            const kwResp = await fetch('/api/keywords');
            const kwData = await kwResp.json();
            
            if (kwData.error) throw new Error(kwData.error);
            const activeKws = kwData.filter(k => k.is_active === 1 || k.is_active === true);
            
            if (activeKws.length === 0) {
                alert('활성화된 키워드가 없습니다.');
                btnBulkScan.disabled = false;
                btnBulkScan.innerHTML = `<span>🔥 모든 활성 키워드 전체 스캔</span>`;
                return;
            }
            
            if (!confirm(`총 ${activeKws.length}개의 키워드를 순차적으로 스캔하시겠습니까?\n(중간에 페이지를 닫지 마세요)`)) {
                btnBulkScan.disabled = false;
                btnBulkScan.innerHTML = `<span>🔥 모든 활성 키워드 전체 스캔</span>`;
                return;
            }

            // Sequential Execution
            let successCount = 0;
            let failCount = 0;

            for (let i = 0; i < activeKws.length; i++) {
                const kw = activeKws[i].keyword;
                btnBulkScan.innerHTML = `
                    <span class="flex items-center gap-2">
                        <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        스캔 중 (${i + 1}/${activeKws.length}): ${kw}
                    </span>`;
                
                try {
                    const res = await fetch('/api/search_single', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ keyword: kw, target_brand: '오즈키즈', super_save_keywords: ssk })
                    });
                    const data = await res.json();
                    if (data.status === 'success') {
                        successCount++;
                        // If this matches the currently selected keyword in UI, refresh the UI results
                        if (selectKeyword.value === kw) {
                            renderScanResults(data);
                            localStorage.setItem('last_scan_results', JSON.stringify(data));
                        }
                    } else {
                        failCount++;
                    }
                } catch (e) {
                    console.error(`Error scanning ${kw}:`, e);
                    failCount++;
                }
                
                // Small delay to prevent rate limiting
                await new Promise(r => setTimeout(r, 1000));
            }

            alert(`벌크 스캔 완료!\n성공: ${successCount}\n실패: ${failCount}`);
            loadHistory(); 

        } catch (err) {
            console.error('runBulkScan error:', err);
            alert('벌크 스캔 시작 중 오류 발생: ' + err.message);
        } finally {
            btnBulkScan.disabled = false;
            btnBulkScan.innerHTML = `<span>🔥 모든 활성 키워드 전체 스캔</span>`;
        }
    }

    async function triggerScanImplicit(keyword) {
        const superSaveStr = inputSupersave.value;
        const ssk = superSaveStr.split(',').map(s => s.trim()).filter(s => s);
        
        try {
            await fetch('/api/search_single', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword, target_brand: '오즈키즈', super_save_keywords: ssk })
            });
        } catch (err) { console.error(`Scan failed for ${keyword}:`, err); }
    }

    if (btnBulkScan) btnBulkScan.addEventListener('click', runBulkScan);

    // Init
    loadMasterKeywords();
    loadHistory();
    // Render last results if they exist
    const lastResults = JSON.parse(localStorage.getItem('last_scan_results') || 'null');
    if (lastResults) {
        renderScanResults(lastResults);
    }
});
