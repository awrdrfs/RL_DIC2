let currentMode = 'block';
let iterCount = 0;

document.addEventListener('DOMContentLoaded', () => {
    initGrid();
    setupEventListeners();
});

function setupEventListeners() {
    // 模式切換
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMode = btn.dataset.type;
        });
    });

    // 迭代按鈕
    document.getElementById('iterate-btn').addEventListener('click', runIteration);
    
    // 重置按鈕
    document.getElementById('reset-btn').addEventListener('click', async () => {
        await fetch('/reset', { method: 'POST' });
        iterCount = 0;
        updateUI();
    });

    // 自動按鈕
    document.getElementById('auto-btn').addEventListener('click', autoConverge);
}

async function initGrid() {
    const response = await fetch('/get_data');
    const data = await response.json();
    renderGrid(data);
}

function renderGrid(data, pathCells = []) {
    const gridEl = document.getElementById('grid');
    gridEl.innerHTML = '';
    
    for (let r = 0; r < 5; r++) {
        for (let c = 0; c < 5; c++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            const type = data.grid[r][c];
            if (type === 1) cell.classList.add('start');
            if (type === 2) cell.classList.add('end');
            if (type === 3) cell.classList.add('block');
            
            // 檢查是否在最佳路徑上
            if (pathCells.some(p => p.r === r && p.c === c)) {
                cell.classList.add('path');
            }

            cell.dataset.r = r;
            cell.dataset.c = c;
            
            // 點擊事件
            cell.onclick = () => toggleCell(r, c);
            
            // 數值
            const valueEl = document.createElement('div');
            valueEl.className = 'cell-value';
            valueEl.innerText = data.values[r][c];
            cell.appendChild(valueEl);
            
            // 政策 (箭頭)
            const policyEl = document.createElement('div');
            policyEl.className = 'cell-policy';
            const symbol = data.policy[r][c];
            policyEl.innerText = symbol;
            if (symbol === '↑') policyEl.classList.add('up');
            if (symbol === '↓') policyEl.classList.add('down');
            if (symbol === '←') policyEl.classList.add('left');
            if (symbol === '→') policyEl.classList.add('right');
            cell.appendChild(policyEl);
            
            gridEl.appendChild(cell);
        }
    }
    document.getElementById('iter-count').innerText = iterCount;
}

function calculatePath(data) {
    let path = [];
    let currR, currC;
    
    // 1. 尋找起點
    for (let r = 0; r < 5; r++) {
        for (let c = 0; c < 5; c++) {
            if (data.grid[r][c] === 1) {
                currR = r; currC = c;
                break;
            }
        }
    }
    
    if (currR === undefined) return [];
    
    // 2. 追蹤政策直到終點
    let visited = new Set();
    while (true) {
        path.push({ r: currR, c: currC });
        visited.add(`${currR},${currC}`);
        
        if (data.grid[currR][currC] === 2) break; // 達終點
        
        const symbol = data.policy[currR][currC];
        let nextR = currR, nextC = currC;
        
        if (symbol === '↑') nextR--;
        else if (symbol === '→') nextC++;
        else if (symbol === '↓') nextR++;
        else if (symbol === '←') nextC--;
        else break; // 無有效行動
        
        // 檢查邊界或無限循環
        if (nextR < 0 || nextR >= 5 || nextC < 0 || nextC >= 5 || visited.has(`${nextR},${nextC}`)) {
            break;
        }
        
        currR = nextR;
        currC = nextC;
    }
    return path;
}

async function toggleCell(r, c) {
    await fetch('/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ r, c, type: currentMode })
    });
    iterCount = 0; // 改動地圖後重設計數
    updateUI();
}

async function runIteration() {
    const response = await fetch('/iterate', { method: 'POST' });
    const data = await response.json();
    iterCount++;
    // 需要重新抓取完整資料來更新 UI (包含 grid 狀態以防萬一)
    updateUI();
}

async function updateUI() {
    const response = await fetch('/get_data');
    const data = await response.json();
    renderGrid(data);
}

async function autoConverge() {
    const btn = document.getElementById('auto-btn');
    btn.disabled = true;
    btn.innerText = '計算中...';
    
    for (let i = 0; i < 50; i++) { // 預設執行 50 次或直到收斂 (這裡簡單執行)
        await runIteration();
        await new Promise(r => setTimeout(r, 50)); // 加速動畫
    }
    
    // 計算完成後，找出並顯示最佳路徑
    const response = await fetch('/get_data');
    const data = await response.json();
    const path = calculatePath(data);
    renderGrid(data, path);
    
    btn.disabled = false;
    btn.innerText = '自動執行至收斂';
}
