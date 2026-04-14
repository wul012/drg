// #pragma once
//
// #include <array>
// #include <unordered_map>
// #include <vector>
//
// // ============================================================================
// // 图的结构设计（仿照 Java 版本的 Graph / Node / Edge）
// // ============================================================================
// // 目标：尽量还原你截图里的 Java 实现：
// //   - Graph 持有所有节点 nodes 和所有边 edges；
// //   - Node 记录自己的入度 in、出度 out、后继节点 nexts 以及从自己出发的边 edges；
// //   - Edge 记录一条有向边的 weight、from、to。
// //
// // 在 C++ 中，我们同样用指针连接 Node 和 Edge，对应关系非常直观，
// // 有利于直接对照课程中的 Java 代码理解 Dijkstra 算法。
// //
// // 另外，仍然保留一个较大的常量 INF，用作“不可达”的距离标记，
// // 在基于堆的 Dijkstra 算法返回的结果数组中会用到它。
// extern const int INF;
//
// struct Edge; // 前向声明
//
// // ------------------------------- 节点结构体 -------------------------------
// struct Node {
//     int value;                 // 节点上写的值（类似 Java 中 Node.value）
//     int in;                    // 入度：有多少条边指向该节点
//     int out;                   // 出度：有多少条边从该节点发出
//     std::vector<Node*> nexts;  // 直接相连的后继节点集合（邻接点）
//     std::vector<Edge*> edges;  // 以当前节点为 from 的所有边
//
//     explicit Node(int v);
// };
//
// // ------------------------------- 边结构体 --------------------------------
// struct Edge {
//     int weight;   // 边权，要求为非负整数（经典 Dijkstra 不支持负权）
//     Node* from;   // 起点
//     Node* to;     // 终点
//
//     Edge(int w, Node* f, Node* t);
// };
//
// // ------------------------------- 图结构体 --------------------------------
// struct Graph {
//     // Java: public HashMap<Integer, Node> nodes;
//     // key 是节点的值（编号），value 是对应的 Node*。
//     std::unordered_map<int, Node*> nodes;
//
//     // Java: public HashSet<Edge> edges;
//     // 这里直接用 vector 保存所有边指针即可，遍历方便。
//     std::vector<Edge*> edges;
//
//     Graph() = default;
// };
//
// // -------------------------- 邻接“矩阵”到图的转换 --------------------------
// // Java 中的 createGraph(Integer[][] matrix) 使用一个 N×3 的矩阵描述图：
// //   matrix[i][0] - from 节点的值
// //   matrix[i][1] - to   节点的值
// //   matrix[i][2] - 边的权值 weight
// //
// // 下面是对应的 C++ 版本：
// //   - 参数 matrix 是若干行长度为 3 的数组 {from, to, weight}；
// //   - 返回值是根据这些边构造出的 Graph；
// //   - 只会为真正出现在边里的点创建 Node 对象；
// //   - 会更新每个 Node 的 in/out/nexts/edges 等信息。
// Graph createGraph(const std::vector<std::array<int, 3>>& matrix);


#pragma once
#include <array>
#include <unordered_map>
#include <vector>

extern const int INF;

struct Edge;

struct Node {
    int value;
    int in;
    int out;
    std::vector<Node*> nexts;
    std::vector<Edge*> edges;
    explicit Node(int v);
};

struct Edge {
    int weight;
    Node* from;
    Node* to;
    Edge(int w,Node* f,Node* t);
};

struct Graph {
    std::unordered_map<int,Node*> nodes;
    std::vector<Edge*> edges;
    Graph() = default;
};

Graph createGraph(const std::vector<std::array<int,3>>& matrix);