#include <iostream>
#include <vector>
#include <queue>
#include <algorithm>

using namespace std;

// ============================================================
// 题目：蓝桥王国 (Lanqiao OJ 1122)
// ============================================================
//
// 【题目描述】
// 给定 N 个建筑（点）和 M 条单向道路（有向边，正权），
// 求从皇宫（1 号点）到其他所有建筑的最短路径。
//
// 【为什么选 Dijkstra 而不是 Floyd？】
// - 只有一个源点（1 号）→ 单源最短路问题。
// - N <= 3×10⁵，M <= 10⁶。Floyd 要 O(N³) ≈ 2.7×10¹⁶，完全不可能。
// - 朴素 Dijkstra O(N²) ≈ 9×10¹⁰，也超时。
// - 堆优化 Dijkstra O(M log N) ≈ 10⁶ × 18 ≈ 1.8×10⁷，轻松通过。
//
// 【Dijkstra 算法原理（贪心 + 松弛）】
// 核心思想：维护一个集合 S，记录"已经确定最短路"的节点。
// 每次从"未确定"的节点中挑出距离起点最近的那个 u，把 u 加入 S，
// 然后用 u 去"松弛"它所有邻居：如果 dist[u] + w(u,v) < dist[v]，就更新 dist[v]。
//
// 为什么这样是对的？因为所有边权 >= 0，当 u 是未确定中距离最小的，
// 任何其他路径绕道都不可能比直达 u 更短，所以 dist[u] 此刻一定是最终值。
// 这就是 Dijkstra 的贪心正确性。
//
// 【堆优化细节】
// 朴素版每轮要 O(N) 扫描找最小，改用小根堆（优先队列）后只需 O(log N)。
// 问题：更新 dist[v] 后，堆里可能已经有 v 的旧记录，无法直接修改。
// 解决：不管旧的，直接 push 一个新的 (v, dist[v]) 进去。
// 弹出时检查 vis[u]，如果 u 已确定就跳过（这就是"懒删除"）。
// 最坏情况堆里有 M 个元素，每次操作 O(log M) = O(log N)。
//
// 【为什么不能处理负权边？】
// 如果边权为负，已确定最短路的点 u 的 dist 可能被后续负权边再次缩短，
// 导致贪心假设"u 的 dist 不会再变"失效。负权需要用 Bellman-Ford / SPFA。
//
// 【INF 与 long long】
// 边权 w <= 10⁹，路径最长可能经过 N 个点，最大距离 ≈ 3×10¹⁴，超过 int。
// INF 设为 10¹⁸，long long 存距离。
// ============================================================

const long long INF = 1e18;

// 边结构体：to = 目标节点，w = 边权
struct Edge {
    int to;
    long long w;
};

// 堆中的节点：id = 节点编号，dist = 从起点到此节点的"候选最短距离"
struct Node {
    int id;
    long long dist;
    
    // priority_queue 默认大根堆，重载 < 让 dist 小的排前面 → 变成小根堆
    // 原理：priority_queue 把 "最大" 的放顶部，我们让 dist 大的返回 true（认为它"小"），
    //       这样 dist 小的反而被当作"大"放到顶部
    bool operator<(const Node& other) const {
        return dist > other.dist; 
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    if (!(cin >> n >> m)) return 0;

    // 邻接表存图。N 可达 3×10⁵，绝对不能开 N×N 的邻接矩阵！
    vector<vector<Edge>> adj(n + 1);

    for (int i = 0; i < m; ++i) {
        int u, v;
        long long w;
        cin >> u >> v >> w;
        adj[u].push_back({v, w}); // 有向边 u → v
    }

    // dist[i] = 起点 1 到节点 i 的当前已知最短距离（初始全部 INF，表示未到达）
    vector<long long> dist(n + 1, INF);
    // vis[i] = true 表示节点 i 的最短路已确定（已从堆中弹出过）
    vector<bool> vis(n + 1, false);

    // ============================================================
    // Dijkstra 主流程
    // ============================================================
    priority_queue<Node> pq;

    // Step 1：起点入堆
    dist[1] = 0;
    pq.push({1, 0});

    // Step 2：不断取堆顶（当前全局最近的未确定点）
    while (!pq.empty()) {
        Node curr = pq.top();
        pq.pop();

        int u = curr.id;

        // 懒删除：如果 u 已经确定过，说明这是堆里残留的旧数据，跳过
        if (vis[u]) continue;

        // 确定 u 的最短路
        vis[u] = true;

        // Step 3：用 u 松弛所有邻居
        for (const Edge& edge : adj[u]) {
            int v = edge.to;
            long long w = edge.w;

            // 松弛条件：经过 u 到 v 的路比目前记录的到 v 的路更短
            if (!vis[v] && dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                // 把新的候选距离 push 进堆（旧的会被懒删除）
                pq.push({v, dist[v]});
            }
        }
    }

    // 输出 1 到每个点的最短距离
    for (int i = 1; i <= n; ++i) {
        cout << dist[i] << (i == n ? "" : " ");
    }
    cout << "\n";

    return 0;
}

/*
============================================================
【手推演示】N=4, M=5
边：1→2 (1), 1→3 (4), 2→3 (2), 2→4 (6), 3→4 (1)

初始：dist = [_, 0, INF, INF, INF]   堆 = {(1,0)}

--- 弹出 (1, 0)，确定节点 1 ---
松弛 1→2: dist[2] = min(INF, 0+1) = 1  → push(2,1)
松弛 1→3: dist[3] = min(INF, 0+4) = 4  → push(3,4)
dist = [_, 0, 1, 4, INF]   堆 = {(2,1), (3,4)}

--- 弹出 (2, 1)，确定节点 2 ---
松弛 2→3: dist[3] = min(4, 1+2) = 3  → push(3,3)  ← 发现更短路！
松弛 2→4: dist[4] = min(INF, 1+6) = 7 → push(4,7)
dist = [_, 0, 1, 3, 7]   堆 = {(3,3), (3,4), (4,7)}

--- 弹出 (3, 3)，确定节点 3 ---
松弛 3→4: dist[4] = min(7, 3+1) = 4  → push(4,4)  ← 又更短了！
dist = [_, 0, 1, 3, 4]   堆 = {(3,4), (4,4), (4,7)}

--- 弹出 (3, 4)，但 vis[3]=true → 跳过（懒删除）---
--- 弹出 (4, 4)，确定节点 4 ---
无邻居需要松弛。
--- 弹出 (4, 7)，但 vis[4]=true → 跳过 ---

最终 dist = [_, 0, 1, 3, 4]
输出：0 1 3 4

最短路径：
  1→2: 直达，代价 1
  1→3: 1→2→3，代价 1+2 = 3（比直达的 4 更短）
  1→4: 1→2→3→4，代价 1+2+1 = 4（比 1→2→4 的 7 更短）
============================================================
*/
