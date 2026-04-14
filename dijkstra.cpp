#include "dijkstra.h"

#include <algorithm>
#include <unordered_map>
#include <utility>

// 为了尽可能贴合题目截图中的 Java 版 Dijkstra2，这里同样实现：
//   - NodeHeap: 内部用最小堆维护候选节点集合；
//   - addOrUpdateOrIgnore(node, distance): “加入 / 更新 / 忽略” 三合一操作；
//   - pop(): 弹出目前距离最小的节点以及对应距离。
//
// 不同点在于：
//   - Java 返回的是 HashMap<Node, Integer>；
//   - 这里为了方便测试，直接返回一个 dist 数组，下标就是节点的 value。

// ---------------------------- 堆中返回的记录 ----------------------------
struct NodeRecord {
    Node* node;    // 节点指针
    int distance;  // 从源点出发到该节点的当前最短距离
};

// ------------------------------ 最小堆实现 ------------------------------
// NodeHeap 与 Java 版本的字段一一对应：
//   - nodes        : Node[] 数组，存放当前在堆中的所有节点；
//   - heapIndexMap : HashMap<Node, Integer>，记录每个节点在堆数组中的下标；
//                    若值为 -1，表示该节点已经被弹出；
//   - distanceMap  : HashMap<Node, Integer>，记录每个节点当前已知的最小距离；
//   - size         : 当前堆中元素个数。
class NodeHeap {
public:
    explicit NodeHeap(int capacity)
        : nodes(capacity), size(0) {}

    bool isEmpty() const { return size == 0; }

    // 判断一个节点是否曾经进入过堆
    bool isEntered(Node* node) const {
        return heapIndexMap.find(node) != heapIndexMap.end();
    }

    // 判断一个节点当前是否还在堆中
    bool inHeap(Node* node) const {
        auto it = heapIndexMap.find(node);
        return it != heapIndexMap.end() && it->second != -1;
    }

    // 与 Java 版本语义完全一致：
    //   - 若 node 在堆中：尝试用更小的 distance 更新它，并向上堆化；
    //   - 若 node 从未进入过堆：插入堆尾并向上堆化；
    //   - 若 node 曾经在堆中但已经被弹出：直接忽略。
    void addOrUpdateOrIgnore(Node* node, int dist) {
        if (inHeap(node)) {
            // 已在堆中：尝试更新为更小的距离
            int& curDist = distanceMap[node];
            if (dist < curDist) {
                curDist = dist;
                insertHeapify(heapIndexMap[node]);
            }
        } else if (!isEntered(node)) {
            // 第一次进入堆
            nodes[size] = node;
            heapIndexMap[node] = size;
            distanceMap[node] = dist;
            insertHeapify(size++);
        } else {
            // 走到这里说明：节点曾经进入过堆且已经被弹出（最短路已确定），忽略即可。
        }
    }

    // 弹出当前堆顶（距离最小的节点）
    NodeRecord pop() {
        Node* topNode = nodes[0];
        NodeRecord record{topNode, distanceMap[topNode]};

        // 把堆尾元素换到堆顶，然后 size-- 并向下堆化。
        swap(0, size - 1);
        Node* removed = nodes[size - 1];

        // 维护映射：removed 已经不在堆中了
        heapIndexMap[removed] = -1;
        distanceMap.erase(removed);
        nodes[size - 1] = nullptr;
        --size;
        heapify(0);

        return record;
    }

private:
    std::vector<Node*> nodes;                        // 小根堆数组
    std::unordered_map<Node*, int> heapIndexMap;     // 节点在堆中的下标
    std::unordered_map<Node*, int> distanceMap;      // 节点当前已知的最小距离
    int size;                                        // 当前堆中元素个数

    // 当前下标 index 处元素向上堆化（保持小根堆性质）
    void insertHeapify(int index) {
        while (index > 0) {
            int parent = (index - 1) / 2;
            if (distanceMap[nodes[index]] < distanceMap[nodes[parent]]) {
                swap(index, parent);
                index = parent;
            } else {
                break;
            }
        }
    }

    // 从 index 开始向下堆化（保持小根堆性质）
    void heapify(int index) {
        while (true) {
            int left = index * 2 + 1;
            int right = index * 2 + 2;
            int smallest = index;

            if (left < size && distanceMap[nodes[left]] < distanceMap[nodes[smallest]]) {
                smallest = left;
            }
            if (right < size && distanceMap[nodes[right]] < distanceMap[nodes[smallest]]) {
                smallest = right;
            }

            if (smallest != index) {
                swap(index, smallest);
                index = smallest;
            } else {
                break;
            }
        }
    }

    // 交换堆中两个位置的节点，同时维护 heapIndexMap
    void swap(int i, int j) {
        if (i == j) return;
        std::swap(nodes[i], nodes[j]);
        heapIndexMap[nodes[i]] = i;
        heapIndexMap[nodes[j]] = j;
    }
};

// ----------------------------- Dijkstra 主体 -----------------------------
// 输入：
//   g   —— 基于 Node / Edge 结构的图；
//   src —— 源点的“值”（即 Node.value）。
// 输出：
//   dist 数组，其中 dist[v] 表示从 src 到 value == v 的节点的最短距离；
//   若某个节点不可达，则对应位置保持为 INF。
std::vector<int> dijkstra(const Graph& g, int src) {
    if (g.nodes.empty()) {
        return {};
    }

    // 找到起点节点指针
    auto itHead = g.nodes.find(src);
    if (itHead == g.nodes.end()) {
        // 图中根本不存在编号为 src 的节点，直接返回全 INF 的空结果。
        return {};
    }
    Node* head = itHead->second;

    // 计算结果数组需要多大：假设节点 value 是非负整数，
    // 结果长度取所有节点 value 的最大值 + 1。
    int maxValue = 0;
    for (const auto& kv : g.nodes) {
        maxValue = std::max(maxValue, kv.first);
    }
    int size = maxValue + 1;

    // 初始化所有点的距离为 INF，表示暂不可达。
    std::vector<int> result(size, INF);

    // NodeHeap 的容量可以设置为图中节点个数。
    NodeHeap heap(static_cast<int>(g.nodes.size()));
    heap.addOrUpdateOrIgnore(head, 0); // 源点距离为 0

    while (!heap.isEmpty()) {
        NodeRecord record = heap.pop();
        Node* cur = record.node;
        int distance = record.distance;

        // 一旦某个节点被弹出，其最短距离就确定下来。
        if (cur->value >= 0 && cur->value < size) {
            result[cur->value] = distance;
        }

        // 用当前节点作为中转，尝试更新所有邻接点的距离。
        for (Edge* edge : cur->edges) {
            Node* to = edge->to;
            int newDist = distance + edge->weight;
            heap.addOrUpdateOrIgnore(to, newDist);
        }
    }

    return result;
}

