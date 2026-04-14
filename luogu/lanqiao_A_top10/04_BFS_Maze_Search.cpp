#include <iostream>
#include <vector>
#include <queue>

using namespace std;

// 题型 4：BFS 广搜与多维状态迷宫 (蓝桥杯必考)
// 【具体真题】：全球变暖 (改编为带条件的 BFS 迷宫) / 拯救公主
// 题目描述：
// 给定一个 N*M 的迷宫。'S' 是起点，'E' 是终点，'#' 是墙壁，'.' 是平地。
// 迷宫中有一把钥匙 'K' 和一扇门 'D'。
// 小明必须先拿到钥匙 'K'，才能穿过门 'D'。
// 每次只能上下左右移动一格，求从起点到终点的最短步数。
// 如果无法到达，输出 Impossible。

// 核心技巧：不仅要记录坐标 (x, y)，还要记录“有没有拿到钥匙”这个状态。
// 把二维 vis 数组升级为三维 vis[x][y][has_key]。

struct State {
    int x, y, step;
    int has_key; // 0 表示没拿到，1 表示拿到了
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    if (!(cin >> n >> m)) return 0;
    
    vector<string> grid(n);
    int sx = 0, sy = 0;
    
    for (int i = 0; i < n; ++i) {
        cin >> grid[i];
        for (int j = 0; j < m; ++j) {
            if (grid[i][j] == 'S') { sx = i; sy = j; }
        }
    }
    
    // vis[x][y][0] 表示没拿钥匙走到 (x,y)
    // vis[x][y][1] 表示拿了钥匙走到 (x,y)
    // 两个状态是平行的，拿了钥匙后可以走回头路！
    vector<vector<vector<bool>>> vis(n, vector<vector<bool>>(m, vector<bool>(2, false)));
    queue<State> q;
    
    int dx[] = {0, 0, 1, -1};
    int dy[] = {1, -1, 0, 0};
    
    q.push({sx, sy, 0, 0});
    vis[sx][sy][0] = true;
    
    while (!q.empty()) {
        State curr = q.front();
        q.pop();
        
        // 找到终点直接输出
        if (grid[curr.x][curr.y] == 'E') {
            cout << curr.step << "\n";
            return 0;
        }
        
        for (int i = 0; i < 4; ++i) {
            int nx = curr.x + dx[i];
            int ny = curr.y + dy[i];
            int next_key = curr.has_key;
            
            // 越界和墙壁判断
            if (nx >= 0 && nx < n && ny >= 0 && ny < m && grid[nx][ny] != '#') {
                char cell = grid[nx][ny];
                
                // 如果碰到了门，且没钥匙，这扇门就是一堵墙，不能走
                if (cell == 'D' && next_key == 0) continue;
                
                // 如果碰到了钥匙，状态变成 1
                if (cell == 'K') next_key = 1;
                
                // 如果这个状态还没被访问过
                if (!vis[nx][ny][next_key]) {
                    vis[nx][ny][next_key] = true;
                    q.push({nx, ny, curr.step + 1, next_key});
                }
            }
        }
    }
    
    cout << "Impossible\n";
    return 0;
}

/*
========== 测试数据 ==========
输入：
5 5
S..##
..#.#
..D.E
..K##
.....

输出：
8

解释：
起点 S 在 (0,0)，门 D 在 (2,2)，终点 E 在 (2,4)，钥匙 K 在 (3,2)。
S 先走到 K (路线：S向下3步，再向右2步到达K，走过路径变成了点，用时5步)。
拿到钥匙后，向左1步，向上1步回到门D的前方，再向右穿过门D，再向右到达E。
总共步数：5(走到K) + 3(从K走到E) = 8 步。
如果没有多维状态 vis，拿完钥匙是不可能走回头路的！
============================
*/
