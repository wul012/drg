#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

// ============================================================
// 题目：旅行售货员 (Lanqiao OJ 3322)
// ============================================================
//
// 【题目描述】
// T 组测试。每组给定 N 个城市和 M 条无向道路（u, v, w）。
// 要求找一个方案让所有城市连通，且"最长的那条路"尽可能短。
// 输出该方案中最长边的权值。
//
// 【本质：最小生成树 (MST) 的最大边】
// 要连通 N 个点，至少选 N-1 条边（即一棵生成树）。
// 在所有可能的生成树中，MST 的"最大边权"是最小的。
// 直觉理解：Kruskal 从最小边开始贪心选，尽量不选大边，
// 当选到第 N-1 条边时刚好连通，此时最后选的那条边就是 MST 中的最大边。
//
// 【Kruskal 算法原理】
// 1. 把所有边按权值从小到大排序
// 2. 依次扫描每条边 (u, v, w)：
//    - 如果 u 和 v 已经在同一个连通块 → 选这条边会形成环，跳过
//    - 如果 u 和 v 不在同一个连通块 → 选这条边，合并两个连通块
// 3. 当选了 N-1 条边时，所有点连通，算法结束
//
// 判断"是否在同一连通块"和"合并"用**并查集 (DSU)** 实现，几乎 O(1)。
// 整体复杂度 O(M log M)，瓶颈在排序。
//
// 【并查集 (Disjoint Set Union) 原理】
// 每个元素有一个 parent 指针，初始指向自己（自己是自己的老大）。
// find(x)：沿着 parent 链一路往上找到根节点（集合的代表元素）。
//   路径压缩优化：找到根后，把沿途所有节点直接挂到根下面，下次查找 O(1)。
// unite(x, y)：先找 x 和 y 的根，如果根不同就合并（把一个根挂到另一个下面）。
//   如果根相同，说明已经在同一集合，返回 false。
//
// 例子：初始 parent = [1,2,3,4]（各自为王）
//   unite(1,2)：parent[1]=2 → 集合 {1,2}，根为 2
//   unite(3,4)：parent[3]=4 → 集合 {3,4}，根为 4
//   unite(1,3)：find(1)=2, find(3)=4, parent[2]=4 → 合并成 {1,2,3,4}
//   find(1)：1→2→4，路径压缩后 parent[1]=4, parent[2]=4
// ============================================================

// 并查集
struct DSU {
    vector<int> parent;
    
    // 初始化：每个节点的 parent 指向自己
    DSU(int n) {
        parent.resize(n + 1);
        for (int i = 1; i <= n; ++i) parent[i] = i;
    }
    
    // 查找根节点（带路径压缩）
    // 递归版：沿 parent 链向上找根，回溯时把沿途节点直接挂到根上
    int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);
        }
        return parent[x];
    }
    
    // 合并两个集合，返回是否成功（false = 已在同一集合，选这条边会成环）
    bool unite(int x, int y) {
        int rootX = find(x);
        int rootY = find(y);
        if (rootX == rootY) return false;
        parent[rootX] = rootY;
        return true;
    }
};

// 边结构体：u, v 为端点，w 为权值
struct Edge {
    int u, v;
    long long w;
    
    // 按边权升序排列
    bool operator<(const Edge& other) const {
        return w < other.w;
    }
};

void solve() {
    int n, m;
    cin >> n >> m;
    
    vector<Edge> edges(m);
    for (int i = 0; i < m; ++i) {
        cin >> edges[i].u >> edges[i].v >> edges[i].w;
    }
    
    // ============================================================
    // Kruskal 主流程
    // ============================================================
    
    // Step 1：边按权值升序排列
    sort(edges.begin(), edges.end());
    
    DSU dsu(n);
    long long max_edge_in_mst = 0;
    int edge_count = 0;
    
    // Step 2：从最小边开始贪心选
    for (const auto& edge : edges) {
        // 尝试合并 u 和 v 所在的连通块
        if (dsu.unite(edge.u, edge.v)) {
            edge_count++;
            // 因为边是升序排列的，后选的边一定 >= 先选的边
            // 所以最后选的那条边就是 MST 中的最大边
            max_edge_in_mst = max(max_edge_in_mst, edge.w);
            
            // 选够 N-1 条边 → 所有点已连通 → 提前结束
            if (edge_count == n - 1) break;
        }
        // 如果 unite 返回 false，说明 u 和 v 已经连通了，
        // 再连这条边就会形成环 → 跳过
    }
    
    cout << max_edge_in_mst << "\n";
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    
    int t;
    if (cin >> t) {
        while (t--) {
            solve();
        }
    }
    
    return 0;
}

/*
============================================================
【手推演示】N=4, M=5
边：(1,2,3) (1,3,7) (2,3,1) (2,4,5) (3,4,2)

Step 1：排序后：
  (2,3,1) (3,4,2) (1,2,3) (2,4,5) (1,3,7)

Step 2：贪心选边（需要选 N-1 = 3 条）

边 (2,3,1)：find(2)=2, find(3)=3，不同 → 选！合并{2,3}
  edge_count=1, max_edge=1
  并查集：parent = [_,1,3,3,4]  (2→3)

边 (3,4,2)：find(3)=3, find(4)=4，不同 → 选！合并{2,3,4}
  edge_count=2, max_edge=2
  并查集：parent = [_,1,3,4,4]  (3→4, 2→3→4)

边 (1,2,3)：find(1)=1, find(2)=find(2)→3→4=4，不同 → 选！合并{1,2,3,4}
  edge_count=3 = N-1 → 结束！
  max_edge=3

输出：3

MST 的 3 条边是：(2,3,1) (3,4,2) (1,2,3)，总权 = 6
其中最大边权 = 3，这就是让所有城市连通的最小"最大边"
（如果换成选 (1,3,7)，最大边就变成 7，更差）
============================================================
*/
