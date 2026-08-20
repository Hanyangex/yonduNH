<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>한양고속 실시간 유류주문 현황</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1000px;
            margin: 30px auto;
            padding: 20px;
            background-color: #f4f7f6;
        }
        .header-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        h1 {
            color: #1a365d;
            margin: 0;
        }
        .refresh-btn {
            background-color: #319795;
            color: white;
            border: none;
            padding: 8px 14px;
            border-radius: 5px;
            font-size: 13px;
            cursor: pointer;
            font-weight: bold;
        }
        .refresh-btn:hover {
            background-color: #2c7a7b;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 25px;
        }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }
        .form-group {
            display: flex;
            flex-direction: column;
        }
        label {
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 5px;
            color: #4a5568;
        }
        input, select {
            padding: 10px;
            border: 1px solid #cbd5e0;
            border-radius: 5px;
            font-size: 14px;
        }
        .submit-btn {
            background-color: #2b6cb0;
            color: white;
            border: none;
            padding: 12px;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            font-size: 15px;
        }
        .submit-btn:disabled {
            background-color: #a0aec0;
            cursor: not-allowed;
        }

        /* 탭 스타일 */
        .tab-container {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .tab-btn {
            padding: 10px 18px;
            border: 1px solid #cbd5e0;
            background-color: #ffffff;
            color: #4a5568;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .tab-btn:hover {
            background-color: #edf2f7;
        }
        .tab-btn.active {
            background-color: #2b6cb0;
            color: white;
            border-color: #2b6cb0;
            box-shadow: 0 2px 4px rgba(43, 108, 176, 0.3);
        }

        .refinery-section {
            margin-bottom: 25px;
            border-top: 3px solid #2b6cb0;
        }
        .refinery-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .refinery-title {
            font-size: 18px;
            font-weight: bold;
            color: #2d3748;
            margin: 0;
        }
        .total-badge {
            background-color: #ebf8ff;
            color: #2b6cb0;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            border: 1px solid #bee3f8;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        th, td {
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
            font-size: 14px;
        }
        th {
            background-color: #f7fafc;
            color: #4a5568;
            font-weight: 600;
        }
        tr:hover {
            background-color: #f8fafc;
        }
        .empty-row {
            text-align: center;
            color: #a0aec0;
            padding: 15px;
        }
        .loading-text {
            text-align: center;
            padding: 20px;
            color: #4a5568;
        }

        /* 재고 관리 섹션 스타일 */
        .stock-input {
            width: 100px;
            padding: 6px 8px;
            font-size: 13px;
        }
        .expected-stock {
            font-weight: bold;
            color: #2b6cb0;
        }
        .expected-stock.negative {
            color: #e53e3e;
        }
    </style>
</head>
<body>

    <div class="header-container">
        <h1>한양고속 실시간 유류주문 현황</h1>
        <button class="refresh-btn" onclick="fetchOrdersFromSheet()">🔄 새로고침</button>
    </div>

    <!-- 출하지별 재고/사용량 계산 카드 -->
    <div class="card">
        <h3>📊 출하지별 예상 재고 현황</h3>
        <div style="overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>출하지</th>
                        <th>전월 재고 (L)</th>
                        <th>당월 입고량 (L)</th>
                        <th>당월 사용량 (L)</th>
                        <th>현재 예상재고량 (L)</th>
                    </tr>
                </thead>
                <tbody id="stockTableBody">
                    <!-- JavaScript로 동적 생성 -->
                </tbody>
            </table>
        </div>
    </div>

    <div class="card">
        <h3>신규 유류 주문 등록</h3>
        <form id="orderForm">
            <div class="form-grid">
                <div class="form-group">
                    <label for="shipDate">출하일자</label>
                    <input type="date" id="shipDate" required>
                </div>
                <div class="form-group">
                    <label for="shipLocation">출하지</label>
                    <input type="text" id="shipLocation" placeholder="예: 보령터미널, 평택, 서산" required>
                </div>
                <div class="form-group">
                    <label for="refinery">정유사</label>
                    <select id="refinery" required>
                        <option value="">선택하세요</option>
                        <option value="SK에너지">SK에너지</option>
                        <option value="HD현대오일뱅크">HD현대오일뱅크</option>
                        <option value="한화토탈">한화토탈</option>
                        <option value="한진">한진</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="quantity">수량 (L)</label>
                    <input type="number" id="quantity" placeholder="예: 20000" min="1" required>
                </div>
            </div>
            <button type="submit" id="submitBtn" class="submit-btn">주문 등록하기</button>
        </form>
    </div>

    <div class="tab-container">
        <button class="tab-btn active" onclick="switchTab('SK에너지', this)">SK에너지</button>
        <button class="tab-btn" onclick="switchTab('HD현대오일뱅크', this)">HD현대오일뱅크</button>
        <button class="tab-btn" onclick="switchTab('한화토탈', this)">한화토탈</button>
        <button class="tab-btn" onclick="switchTab('한진', this)">한진</button>
    </div>

    <div id="refineryContainer">
        <div class="card loading-text">구글 시트에서 실시간 데이터를 불러오는 중입니다...</div>
    </div>

    <script>
        const GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx46ljUCW-lSsMtc79-FM9jDQL_Pau-l25tJ6gffnoWz780LOfu0YWoq1c9u6IRVU9psA/exec";

        const refineries = ["SK에너지", "HD현대오일뱅크", "한화토탈", "한진"];
        const defaultLocations = ["보령터미널"];

        let refineryData = {};
        let rawOrders = [];
        let currentTab = "SK에너지";
        let isFetching = false;

        // 구글 시트 연동 재고 데이터 객체
        let stockInputs = {};

        document.getElementById('shipDate').value = new Date().toISOString().substring(0, 10);

        function createEmptyDataStructure() {
            const structure = {};
            refineries.forEach(name => {
                structure[name] = {
                    orders: [],
                    totalQuantity: 0
                };
            });
            return structure;
        }

        refineryData = createEmptyDataStructure();

        function formatDate(dateStr) {
            if (!dateStr) return '';
            const str = String(dateStr);
            if (str.includes('T')) return str.split('T')[0];
            return str;
        }

        function formatTime(timeStr) {
            if (!timeStr) return '';
            const str = String(timeStr);
            if (str.includes('T')) {
                const dateObj = new Date(str);
                if (!isNaN(dateObj.getTime())) {
                    return dateObj.toLocaleTimeString('ko-KR');
                }
            }
            return str;
        }

        function switchTab(tabName, btnElement) {
            currentTab = tabName;
            const tabs = document.querySelectorAll('.tab-btn');
            tabs.forEach(tab => tab.classList.remove('active'));

            if (btnElement) {
                btnElement.classList.add('active');
            }

            renderRefineryTables();
        }

        async function fetchOrdersFromSheet() {
            if (!GOOGLE_SCRIPT_URL || GOOGLE_SCRIPT_URL.includes("여기에")) return;
            if (isFetching) return;

            isFetching = true;
            const container = document.getElementById('refineryContainer');

            try {
                const response = await fetch(GOOGLE_SCRIPT_URL);
                if (!response.ok) {
                    throw new Error(`HTTP 에러 발생 (${response.status})`);
                }

                const data = await response.json();
                
                // 구글 시트에서 수신한 객체 분할 (orders, stocks)
                const orders = data.orders || [];
                stockInputs = data.stocks || {};

                rawOrders = orders;

                const tempData = createEmptyDataStructure();

                orders.forEach(order => {
                    const ref = order.refinery;
                    if (tempData[ref]) {
                        const rawQ = String(order.quantity).replace(/,/g, '');
                        const q = Number(rawQ) || 0;

                        tempData[ref].orders.push({
                            date: formatDate(order.date),
                            location: order.location,
                            quantity: q,
                            time: formatTime(order.time)
                        });
                        tempData[ref].totalQuantity += q;
                    }
                });

                refineryData = tempData;
                renderRefineryTables();
                renderStockTable();

            } catch (error) {
                console.error("데이터 불러오기 실패:", error);
                if (!container.querySelector('.refinery-section')) {
                    container.innerHTML = `
                        <div class="card loading-text" style="color: #e53e3e;">
                            ⚠️ 데이터를 불러오지 못했습니다.<br>
                            <small>Apps Script 배포 상태와 인터넷 연결을 확인해 주세요.</small>
                        </div>
                    `;
                }
            } finally {
                isFetching = false;
            }
        }

        function renderStockTable() {
            const tbody = document.getElementById('stockTableBody');
            
            const fetchedLocations = rawOrders.map(o => o.location ? o.location.trim() : '').filter(Boolean);
            const locations = Array.from(new Set([...defaultLocations, ...fetchedLocations]));
            
            Object.keys(stockInputs).forEach(loc => {
                if (!locations.includes(loc)) locations.push(loc);
            });

            if (locations.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" class="empty-row">출하지 데이터가 없습니다.</td></tr>`;
                return;
            }

            const inboundTotals = {};
            rawOrders.forEach(o => {
                const loc = o.location ? o.location.trim() : '';
                if (loc) {
                    const q = Number(String(o.quantity).replace(/,/g, '')) || 0;
                    inboundTotals[loc] = (inboundTotals[loc] || 0) + q;
                }
            });

            let html = '';
            locations.forEach(loc => {
                const prevStock = stockInputs[loc]?.prevStock || 0;
                const usage = stockInputs[loc]?.usage || 0;
                const inbound = inboundTotals[loc] || 0;
                
                const expectedStock = prevStock + inbound - usage;
                const isNegative = expectedStock < 0;

                html += `
                    <tr>
                        <td><b>${loc}</b></td>
                        <td>
                            <input type="number" class="stock-input" value="${prevStock || ''}" placeholder="0" 
                                onchange="updateStockInput('${loc}', 'prevStock', this.value)">
                        </td>
                        <td><b>${inbound.toLocaleString()} L</b></td>
                        <td>
                            <input type="number" class="stock-input" value="${usage || ''}" placeholder="0" 
                                onchange="updateStockInput('${loc}', 'usage', this.value)">
                        </td>
                        <td class="expected-stock ${isNegative ? 'negative' : ''}">
                            ${expectedStock.toLocaleString()} L
                        </td>
                    </tr>
                `;
            });

            tbody.innerHTML = html;
        }

        // 재고 입력 변경 시 구글 시트 전송 POST 처리
        async function updateStockInput(location, key, value) {
            const numVal = Number(value) || 0;

            if (!stockInputs[location]) {
                stockInputs[location] = { prevStock: 0, usage: 0 };
            }
            stockInputs[location][key] = numVal;

            renderStockTable();

            try {
                await fetch(GOOGLE_SCRIPT_URL, {
                    method: 'POST',
                    mode: 'no-cors',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: "updateStock",
                        location: location,
                        key: key,
                        value: numVal
                    })
                });
            } catch (error) {
                console.error("재고 상태 저장 실패:", error);
            }
        }

        function renderRefineryTables() {
            const container = document.getElementById('refineryContainer');
            container.innerHTML = '';

            const displayRefineries = refineries.filter(r => r === currentTab);

            displayRefineries.forEach((name) => {
                const data = refineryData[name];
                if (!data) return;

                const section = document.createElement('div');
                section.className = 'card refinery-section';

                let tableRowsHtml = '';
                if (data.orders.length === 0) {
                    tableRowsHtml = `
                        <tr>
                            <td colspan="5" class="empty-row">등록된 주문 내역이 없습니다.</td>
                        </tr>
                    `;
                } else {
                    data.orders.slice().reverse().forEach((order, idx) => {
                        const orderNo = data.orders.length - idx;
                        tableRowsHtml += `
                            <tr>
                                <td>${orderNo}</td>
                                <td>${order.date}</td>
                                <td>${order.location}</td>
                                <td><b>${Number(order.quantity).toLocaleString()} L</b></td>
                                <td>${order.time}</td>
                            </tr>
                        `;
                    });
                }

                section.innerHTML = `
                    <div class="refinery-header">
                        <h3 class="refinery-title">🏢 ${name}</h3>
                        <span class="total-badge">총 합계: <span>${data.totalQuantity.toLocaleString()}</span> L</span>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>No.</th>
                                <th>출하일자</th>
                                <th>출하지</th>
                                <th>수량(L)</th>
                                <th>등록시간</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${tableRowsHtml}
                        </tbody>
                    </table>
                `;
                container.appendChild(section);
            });
        }

        document.getElementById('orderForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.innerText = "저장 중...";

            const now = new Date();
            const newOrder = {
                id: Date.now(),
                date: document.getElementById('shipDate').value,
                location: document.getElementById('shipLocation').value,
                refinery: document.getElementById('refinery').value,
                quantity: Number(document.getElementById('quantity').value),
                time: now.toLocaleTimeString('ko-KR')
            };

            try {
                await fetch(GOOGLE_SCRIPT_URL, {
                    method: 'POST',
                    mode: 'no-cors',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newOrder)
                });

                document.getElementById('shipLocation').value = '';
                document.getElementById('quantity').value = '';

                setTimeout(() => {
                    fetchOrdersFromSheet();
                    submitBtn.disabled = false;
                    submitBtn.innerText = "주문 등록하기";
                }, 1500);

            } catch (error) {
                console.error("저장 실패:", error);
                alert("주문 등록에 실패했습니다.");
                submitBtn.disabled = false;
                submitBtn.innerText = "주문 등록하기";
            }
        });

        setInterval(fetchOrdersFromSheet, 10000);
        fetchOrdersFromSheet();
    </script>
</body>
</html>