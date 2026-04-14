#include <iostream>
#include <vector>
#include <queue>
#include <algorithm>

using namespace std;

// 题型 7：最短路图论题 (Dijkstra 单源最短路 + 堆优化)
// 【具体真题】：蓝桥王国 (Lanqiao OJ 1122)
// 题目描述：
// 蓝桥王国一共有 N 个建筑和 M 条单向道路，每条道路连接两个建筑并有长度 w。
// 皇宫编号为 1。求从皇宫到每个建筑的最短路径长度。
// N <= 3*10^5, M <= 10^6，必须使用堆优化的 Dijkstra。

const long long INF = 1e18; // 防止 long long 溢出

struct Edge {
    int to;
    long long w;
};

struct Node {
    int id;
    long long dist;
    // 优先队列用小根堆，必须重载大于号，让距离近的排在最前面
    bool operator>(const Node& other) const {
        return dist > other.dist;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m; 
    if (!(cin >> n >> m)) return 0;
    
    vector<vector<Edge>> adj(n + 1);
    for (int i = 0; i < m; ++i) {
        int u, v;
        long long w;
        cin >> u >> v >> w;
        adj[u].push_back({v, w}); // 单向图，只从 u 指向 v
    }
    
    // 最短路核心数据结构
    vector<long long> dist(n + 1, INF);
    vector<bool> vis(n + 1, false);
    priority_queue<Node, vector<Node>, greater<Node>> pq; // C++ 自带小根堆声明
    
    dist[1] = 0; // 皇宫为起点
    pq.push({1, 0});
    
    while (!pq.empty()) {
        int u = pq.top().id;
        pq.pop();
        
        if (vis[u]) continue; // 已经被确定过最短路的点直接丢弃（堆优化精髓）
        vis[u] = true;
        
        // 松弛操作
        for (const auto& edge : adj[u]) {
            int v = edge.to;
            long long w = edge.w;
            if (!vis[v] && dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                pq.push({v, dist[v]});
            }
        }
    }
    
    // 输出从起点 1 到所有点 1~N 的最短路
    for (int i = 1; i <= n; ++i) {
        if (dist[i] == INF) cout << "-1 ";
        else cout << dist[i] << " ";
    }
    cout << "\n";
    
    return 0;
}

/*
========== 测试数据 ==========
输入：
3 3
1 2 1
1 3 5
2 3 2

输出：
0 1 3

解释：
1 到 1：距离 0
1 到 2：直接走，距离 1
1 到 3：1->2(1) + 2->3(2) = 3 (比直接走 1->3 的 5 要短)
============================
*/
