#include <iostream>
#include <vector>
#include <queue>
#include <string>

using namespace std;

// ============================================================
// 题目：迷宫取钥匙（BFS + 状态压缩）
// ============================================================
//
// 【题目要求】
// 给定 n×m 迷宫：
// S 起点，T 终点，. 空地，# 墙。
// a~f 表示钥匙，A~F 表示门。只有拿到对应小写钥匙后，才能通过对应大写门。
// 每次上下左右走一格，求从 S 到 T 的最少步数。到不了输出 -1。
//
// 【输入格式】
// 第一行：n m
// 接下来 n 行：每行一个长度为 m 的字符串
//
// 【输出格式】
// 输出最少步数。
//
// 【样例输入】
// 1 5
// S.aAT
//
// 【样例输出】
// 4
//
// 【为什么普通 BFS 不够？】
// 因为“人在同一个格子”，但“手里钥匙集合不同”，未来可走的路也不同。
// 所以状态不能只记 (x,y)，还必须记当前持有的钥匙状态 mask。
//
// 【状态设计】
// dist[x][y][mask] = 到达 (x,y) 且当前钥匙集合为 mask 的最短步数
// 其中 mask 是一个二进制数：
// - 第 0 位是否拿到 a
// - 第 1 位是否拿到 b
// ...
// - 第 5 位是否拿到 f
//
// 总状态数约为 n*m*64，完全可以接受。
// ============================================================

struct Node {
    int x, y, mask;
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    if (!(cin >> n >> m)) return 0;

    vector<string> g(n);
    for (int i = 0; i < n; ++i) cin >> g[i];

    int sx = -1, sy = -1;
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < m; ++j) {
            if (g[i][j] == 'S') {
                sx = i;
                sy = j;
            }
        }
    }

    vector<vector<vector<int>>> dist(n, vector<vector<int>>(m, vector<int>(64, -1)));
    queue<Node> q;
    dist[sx][sy][0] = 0;
    q.push({sx, sy, 0});

    int dx[4] = {-1, 1, 0, 0};
    int dy[4] = {0, 0, -1, 1};

    while (!q.empty()) {
        Node cur = q.front();
        q.pop();

        int x = cur.x, y = cur.y, mask = cur.mask;
        if (g[x][y] == 'T') {
            cout << dist[x][y][mask] << '\n';
            return 0;
        }

        for (int dir = 0; dir < 4; ++dir) {
            int nx = x + dx[dir];
            int ny = y + dy[dir];
            int nmask = mask;

            if (nx < 0 || nx >= n || ny < 0 || ny >= m) continue;
            if (g[nx][ny] == '#') continue;

            char c = g[nx][ny];
            if (c >= 'a' && c <= 'f') {
                nmask |= (1 << (c - 'a'));
            }
            if (c >= 'A' && c <= 'F') {
                if ((mask & (1 << (c - 'A'))) == 0) continue;
            }

            if (dist[nx][ny][nmask] == -1) {
                dist[nx][ny][nmask] = dist[x][y][mask] + 1;
                q.push({nx, ny, nmask});
            }
        }
    }

    cout << -1 << '\n';
    return 0;
}

/*
============================================================
【手推样例】
迷宫：S . a A T
下标：0 1 2 3 4

初始：在 S，mask=000000，步数 0
第 1 步：走到 '.'，mask 仍是 000000
第 2 步：走到 'a'，拿到钥匙 a，mask 变成 000001
第 3 步：走到 'A'，因为 mask 里有 a，所以允许通过
第 4 步：走到 'T'，结束
答案 = 4

注意：
如果没有先走到 'a'，那么走到 'A' 时会被门挡住。
============================================================
【易错点总结】
1. visited 不能只开二维，必须带上 mask。
2. 判断门能不能过时，要看“当前旧 mask”，不是更新后的 nmask。
3. BFS 适用前提是每一步代价都相同，都是 1。
4. 钥匙数少时最适合用状态压缩。
============================================================
*/
