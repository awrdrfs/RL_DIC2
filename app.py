from flask import Flask, render_template, jsonify, request
import numpy as np

app = Flask(__name__)

# 初始化網格參數
GRID_SIZE = 5
GAMMA = 0.9
THRESHOLD = 1e-4

# 狀態類別：0: 一般, 1: 起點, 2: 終點, 3: 障礙物
# 預設：(0,0) 為起點, (4,4) 為終點, (1,1), (2,2), (3,3) 為障礙物
grid_status = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
grid_status[0, 0] = 1
grid_status[4, 4] = 2
grid_status[1, 1] = 3
grid_status[2, 2] = 3
grid_status[3, 3] = 3

# 價值函數 V(s)
V = np.zeros((GRID_SIZE, GRID_SIZE))

# 行動定義: 0: 上, 1: 右, 2: 下, 3: 左
ACTIONS = [(-1, 0), (0, 1), (1, 0), (0, -1)]
ACTION_NAMES = ['UP', 'RIGHT', 'DOWN', 'LEFT']
ACTION_SYMBOLS = ['↑', '→', '↓', '←']

def get_reward(r, c):
    """獲取進入該格子的獎勵"""
    if grid_status[r, c] == 2:  # 終點
        return 10.0
    elif grid_status[r, c] == 3:  # 障礙物
        return -5.0
    else:
        return -0.1  # 每走一步的代價

def is_valid(r, c):
    """檢查是否在網格內且非障礙物"""
    return 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE

def value_iteration_step():
    """執行一輪價值迭代"""
    global V
    new_V = np.copy(V)
    policy = np.full((GRID_SIZE, GRID_SIZE), -1, dtype=int)
    
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            # 終點與障礙物不更新價值
            if grid_status[r, c] == 2 or grid_status[r, c] == 3:
                new_V[r, c] = get_reward(r, c)
                continue
            
            action_values = []
            for action_idx, (dr, dc) in enumerate(ACTIONS):
                nr, nc = r + dr, c + dc
                if is_valid(nr, nc):
                    # 考慮邊界，如果撞牆則留在原地（取決於模型定義，這裡採納簡單版本：撞牆罰分且留在原地）
                    val = get_reward(nr, nc) + GAMMA * V[nr, nc]
                else:
                    # 撞出界外，停留在原處
                    val = -1.0 + GAMMA * V[r, c]
                action_values.append(val)
            
            new_V[r, c] = max(action_values)
            policy[r, c] = np.argmax(action_values)
            
    V = new_V
    return V.tolist(), policy.tolist()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data')
def get_data():
    policy = []
    for r in range(GRID_SIZE):
        row_policy = []
        for c in range(GRID_SIZE):
            if grid_status[r, c] == 2 or grid_status[r, c] == 3:
                row_policy.append('')
                continue
            
            # 計算目前最佳政策
            action_values = []
            for action_idx, (dr, dc) in enumerate(ACTIONS):
                nr, nc = r + dr, c + dc
                if is_valid(nr, nc):
                    val = get_reward(nr, nc) + GAMMA * V[nr, nc]
                else:
                    val = -1.0 + GAMMA * V[r, c]
                action_values.append(val)
            best_action = np.argmax(action_values)
            row_policy.append(ACTION_SYMBOLS[best_action])
        policy.append(row_policy)
        
    # 處理顯示數值，隱藏終點與障礙物的數值顯示
    display_values = []
    for r in range(GRID_SIZE):
        row = []
        for c in range(GRID_SIZE):
            if grid_status[r, c] == 2 or grid_status[r, c] == 3:
                row.append('')
            else:
                row.append(round(V[r, c], 2))
        display_values.append(row)

    return jsonify({
        'grid': grid_status.tolist(),
        'values': display_values,
        'policy': policy
    })

@app.route('/iterate', methods=['POST'])
def iterate():
    v_list, p_list = value_iteration_step()
    
    # 轉換政策為符號
    policy_symbols = []
    for r in range(GRID_SIZE):
        row = []
        for c in range(GRID_SIZE):
            if grid_status[r, c] == 2 or grid_status[r, c] == 3:
                row.append('')
            else:
                row.append(ACTION_SYMBOLS[p_list[r][c]])
        policy_symbols.append(row)
        
    # 處理顯示數值，隱藏終點與障礙物的數值顯示
    display_values = []
    for r in range(GRID_SIZE):
        row = []
        for c in range(GRID_SIZE):
            if grid_status[r, c] == 2 or grid_status[r, c] == 3:
                row.append('')
            else:
                row.append(round(v_list[r][c], 2))
        display_values.append(row)

    return jsonify({
        'values': display_values,
        'policy': policy_symbols
    })

@app.route('/toggle', methods=['POST'])
def toggle():
    global grid_status, V
    data = request.json
    r, c = data['r'], data['c']
    type_to_set = data['type'] # 'start', 'end', 'block', 'none'
    
    # 清除舊的起點或終點（如果是設為起點或終點）
    if type_to_set == 'start':
        grid_status[grid_status == 1] = 0
        grid_status[r, c] = 1
    elif type_to_set == 'end':
        grid_status[grid_status == 2] = 0
        grid_status[r, c] = 2
    elif type_to_set == 'block':
        grid_status[r, c] = 3
    else:
        grid_status[r, c] = 0
    
    # 改動後重設價值
    V = np.zeros((GRID_SIZE, GRID_SIZE))
    return jsonify({'status': 'success'})

@app.route('/reset', methods=['POST'])
def reset():
    global V
    V = np.zeros((GRID_SIZE, GRID_SIZE))
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

