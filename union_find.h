#pragma once

#include <unordered_map>
#include <vector>
#include <stack>
#include <memory>

namespace ds {

// 并查集（Disjoint Set Union, DSU / Union-Find）- 模板实现
// 作用：动态维护若干个不相交集合，支持两类核心操作：
//   1) 查询两个元素是否属于同一集合（isSameSet）
//   2) 合并两个元素所在的集合（unify / union）
// 典型应用：连通性判断、最小生成树（Kruskal）、去重分组等。
//
// 本实现采用两大优化：
//   - 路径压缩（Path Compression）：在 findHead 查找代表元时，将沿途节点直接挂到代表元上，
//     让后续查询几乎 O(1)。
//   - 按规模合并（Union by Size）：合并时把“较小集合”的代表元挂到“较大集合”的代表元上，
//     保持树高很低。
// 二者结合后，单次操作的摊还时间复杂度为近似 O(1)（更严格地说是 O(alpha(n))，alpha 为阿克曼反函数）。
//
// 说明：这是一个“头文件实现”的模板类，支持任意可以作为 unordered_map 键的值类型 T（如 int、string）。

template <typename T>
class UnionFind {
private:
    // Element: 轻量级包装，以便内部用指针建立父子关系（unordered_map 的键不再直接是 T*）。
    // 这么做的好处：不限制 T 的内存布局，也不需要用户自己维护指针的生存期。
    struct Element {
        T value;
        explicit Element(const T& v) : value(v) {}
    };

    // 三张“表”的含义：
    // 1) elementMap:   value(T) -> Element* 映射，负责把“外部值”映射到“内部节点对象”。
    std::unordered_map<T, Element*> elementMap;
    // 2) fatherMap:    某个 Element* 的父亲是谁（代表树形结构）。代表元的父亲就是它自己。
    std::unordered_map<Element*, Element*> fatherMap;
    // 3) sizeMap:      仅在“代表元(head)”上存储集合大小。非代表元的条目不在此表中。
    std::unordered_map<Element*, int> sizeMap;

    // storage 负责托管 Element 对象的生命周期，避免手动 delete 与悬垂指针问题。
    std::vector<std::unique_ptr<Element>> storage;

    // 寻找“代表元”（也称集合的根节点 / head）。
    // 步骤：
    //   - 先一路向上找到代表元；
    //   - 再把沿途经过的节点直接挂到代表元上（路径压缩），降低后续查询的树高。
    Element* findHead(Element* e) {
        std::stack<Element*> path;      // 记录访问路径，便于回溯时做压缩
        while (e != fatherMap[e]) {     // 代表元的父亲指向自己
            path.push(e);
            e = fatherMap[e];
        }
        // 扁平化路径：把沿途所有节点直接连到代表元 e
        while (!path.empty()) {
            fatherMap[path.top()] = e;
            path.pop();
        }
        return e; // e 即代表元
    }

public:
    UnionFind() = default; // 空结构，后续可通过 add/addAll 动态加入元素

    // 通过一个初始列表批量创建元素，每个元素各自单独成一个集合
    explicit UnionFind(const std::vector<T>& list) { addAll(list); }

    // 新增一个值 v：
    //   - 创建对应的 Element 节点；
    //   - 自己的父亲设为自己；
    //   - 在 sizeMap 里登记该集合大小为 1。
    void add(const T& v) {
        if (elementMap.count(v)) return; // 已存在则忽略
        storage.emplace_back(std::make_unique<Element>(v));
        Element* e = storage.back().get();
        elementMap[v] = e;
        fatherMap[e] = e; // 自己是自己的代表
        sizeMap[e] = 1;   // 单元素集合大小为 1
    }

    // 批量添加若干值
    void addAll(const std::vector<T>& list) {
        for (const auto& v : list) add(v);
    }

    // 判断某个值是否已经在并查集中
    bool contains(const T& v) const { return elementMap.find(v) != elementMap.end(); }

    // 判断两个值是否属于同一集合：比较两者代表元是否相同
    bool isSameSet(const T& a, const T& b) {
        if (!contains(a) || !contains(b)) return false;
        return findHead(elementMap[a]) == findHead(elementMap[b]);
    }

    // 合并两个元素所属的集合：
    //   - 先分别找到两者的代表元；
    //   - 若本就同集合则无需操作；
    //   - 否则按集合大小把小树挂到大树上，并更新代表元的 size。
    void unify(const T& a, const T& b) {
        if (!contains(a) || !contains(b)) return; // 没有的元素不处理
        Element* aF = findHead(elementMap[a]);
        Element* bF = findHead(elementMap[b]);
        if (aF == bF) return; // 已在同一集合
        int sizeA = sizeMap[aF];
        int sizeB = sizeMap[bF];
        Element* big = (sizeA >= sizeB) ? aF : bF;
        Element* small = (big == aF) ? bF : aF;
        fatherMap[small] = big;              // 小挂大
        sizeMap[big] = sizeA + sizeB;        // 代表元的集合大小合并
        sizeMap.erase(small);                // small 不再是代表元，移除其 size 条目
    }

    // 当前有多少个集合（即有多少个代表元）
    int setCount() const { return static_cast<int>(sizeMap.size()); }

    // 查询某个值所在集合的规模。若该值不存在则返回 0。
    int sizeOfSet(const T& a) {
        if (!contains(a)) return 0;
        Element* head = findHead(elementMap[a]);
        auto it = sizeMap.find(head);
        return it == sizeMap.end() ? 0 : it->second;
    }
};

} // namespace ds
