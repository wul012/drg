// #include "graph.h"
//
// #include <stdexcept>
//
// // 一个比较大的常量，用于表示“不可达”的距离。
// // 在 Dijkstra 的实现里：
// //   - 初始化所有点的距离为 INF；
// //   - 若算法结束后某个点的距离仍为 INF，则说明从源点无法到达该点。
// const int INF = 1000000000; // 1e9
//
// // ---------------------------- Node / Edge 实现 ----------------------------
//
// Node::Node(int v)
//     : value(v), in(0), out(0), nexts(), edges() {}
//
// Edge::Edge(int w, Node* f, Node* t)
//     : weight(w), from(f), to(t) {}
//
// // --------------------------- createGraph 实现 ----------------------------
//
// Graph createGraph(const std::vector<std::array<int, 3>>& matrix) {
//     Graph graph;
//
//     // 每一行 row = {from, to, weight}
//     for (const auto& row : matrix) {
//         int fromValue = row[0];
//         int toValue   = row[1];
//         int weight    = row[2];
//
//         if (weight < 0) {
//             // 经典 Dijkstra 不能处理负权边
//             throw std::invalid_argument("Dijkstra does not support negative edge weights");
//         }
//
//         // 1. 确保 from 节点存在
//         Node* fromNode = nullptr;
//         auto itFrom = graph.nodes.find(fromValue);
//         if (itFrom == graph.nodes.end()) {
//             fromNode = new Node(fromValue);
//             graph.nodes[fromValue] = fromNode;
//         } else {
//             fromNode = itFrom->second;
//         }
//
//         // 2. 确保 to 节点存在
//         Node* toNode = nullptr;
//         auto itTo = graph.nodes.find(toValue);
//         if (itTo == graph.nodes.end()) {
//             toNode = new Node(toValue);
//             graph.nodes[toValue] = toNode;
//         } else {
//             toNode = itTo->second;
//         }
//
//         // 3. 创建一条边并更新两端节点的信息
//         Edge* newEdge = new Edge(weight, fromNode, toNode);
//
//         fromNode->nexts.push_back(toNode); // 记录后继节点
//         fromNode->edges.push_back(newEdge); // 记录从 from 发出的边
//         fromNode->out++;                   // 出度 +1
//         toNode->in++;                      // 入度 +1
//
//         graph.edges.push_back(newEdge);
//     }
//
//     return graph; // 返回值语义与 Java 中的 createGraph 一致
// }

#include "graph.h"
#include <stdexcept>
const int INF = 1000000000;

Node::Node(int v)
    :value(v),in(0),out(0),nexts(),edges(){}

Edge::Edge(int w,Node* f,Node* t)
    :weight(w),from(f),to(t){}

Graph createGraph(const std::vector<std::array<int,3>>& matrix) {
    Graph graph;

    for (const auto& row:matrix) {
        int fromValue = row[0];
        int toValue = row[1];
        int weight = row[2];
        if (weight < 0) {
            throw std::invalid_argument("Dijkstra does not support negative edge weights");
        }


        Node* fromNode = nullptr;
        auto itFrom = graph.nodes.find(fromValue);
        if (itFrom == graph.nodes.end()) {
            fromNode = new Node(fromValue);
            graph.nodes[fromValue] = fromNode;
        }else{fromNode = itFrom->second;}

        Node* toNode = nullptr;
        auto itTo = graph.nodes.find(toValue);
        if (itTo == graph.nodes.end()) {
            toNode = new Node(toValue);
            graph.nodes[toValue] = toNode;
        }else{toNode = itTo->second;}


        Edge* newEdge = new Edge(weight,fromNode,toNode);

        fromNode->nexts.push_back(toNode);
        fromNode->edges.push_back(newEdge);
        fromNode->out++;
        toNode->in++;
        graph.edges.push_back(newEdge);
    }
    return graph;
}