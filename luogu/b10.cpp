#include <bits/stdc++.h>
using namespace std;

// 题目：混境之地5 (lanqiao OJ 3820)
// 核心思路：状态空间搜索（BFS / 记忆化 DFS）
// 蓝桥云课的截图提示使用 dp[x][y][t] 记忆化 DFS，但在 C++ 中 1000x1000 的网格 DFS 极易导致爆栈。
// 因此我们采用逻辑完全等价，但工程上更安全且不会爆栈的 BFS（广度优先搜索）来实现。

const int N = 1005;
int h[N][N];

// vis[x][y][t] 表示是否能从起点到达坐标 (x, y)，且喷气背包的使用状态为 t
// t = 0 表示还没使用过背包，t = 1 表示已经使用过背包
bool vis[N][N][2]; 

int n, m, k;
int sx, sy, ex, ey; // 起点和终点坐标

// 上下左右四个方向
int dx[] = {0, 0, 1, -1};
int dy[] = {1, -1, 0, 0};

// 定义队列中的节点结构
struct Node {
    int x, y, t;
};

void solve() {
    cin >> n >> m >> k;
    cin >> sx >> sy >> ex >> ey;
    
    for (int i = 1; i <= n; ++i) {
        for (int j = 1; j <= m; ++j) {
            cin >> h[i][j];
        }
    }
    
    queue<Node> q;
    // C++11 支持列表初始化
    q.push({sx, sy, 0});
    vis[sx][sy][0] = true;
    
    bool can_escape = false;
    
    while (!q.empty()) {
        // C++11 支持 auto，但不支持结构化绑定
        // 所以我们用 auto 推导 curr 的类型，再提取成员变量
        auto curr = q.front();
        int x = curr.x;
        int y = curr.y;
        int t = curr.t;
        q.pop();
        
        // 如果到达终点，标记成功并提前结束
        if (x == ex && y == ey) {
            can_escape = true;
            break;
        }
        
        // 尝试向四个方向移动
        for (int i = 0; i < 4; ++i) {
            int nx = x + dx[i];
            int ny = y + dy[i];
            
            // 越界检查
            if (nx < 1 || nx > n || ny < 1 || ny > m) continue;
            
            // 移动规则 1：不用背包
            // 必须严格走到比当前高度低的地方
            if (h[nx][ny] < h[x][y]) {
                if (!vis[nx][ny][t]) {
                    vis[nx][ny][t] = true;
                    // C++11 支持列表初始化
                    q.push({nx, ny, t});
                }
            }
            
            // 移动规则 2：使用喷气背包
            // 题意：“喷气背包燃料不足，只可以最后使用一次” -> 这意味着背包只能在整个旅途中用一次
            // 前提是之前还没用过 (t == 0)，并且使用后目标高度必须严格小于当前高度 + k
            if (t == 0 && h[nx][ny] < h[x][y] + k) {
                if (!vis[nx][ny][1]) {
                    vis[nx][ny][1] = true;
                    // C++11 支持列表初始化
                    q.push({nx, ny, 1}); // 状态变为已使用背包 (t=1)
                }
            }
        }
    }
    
    if (can_escape) {
        cout << "Yes\n";
    } else {
        cout << "No\n";
    }
}

int main() {
    // 优化输入输出流
    ios::sync_with_stdio(0), cin.tie(0), cout.tie(0);
    solve();
    return 0;
}
