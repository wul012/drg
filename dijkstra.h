// #pragma once
//
// #include <vector>
// #include "graph.h"
//
// // 使用堆优化的 Dijkstra 算法，在基于 Node / Edge 的 Graph 上求单源最短路。
// //
// // 约定：
// //   - 图中节点的 value 是非负整数；
// //   - 我们假设这些 value 不会太大，并以“节点值”作为结果数组的下标：
// //       dist[v] 表示从 src 出发到 value == v 的节点的最短距离；
// //   - 若某个节点不可达，则对应位置保持为 INF。
// std::vector<int> dijkstra(const Graph& g, int src);

#pragma once
#include "graph.h"
#include <vector>
std::vector<int> dijkstra(const Graph& g,int src);