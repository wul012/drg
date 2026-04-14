#include <iostream>
#include <vector>

using namespace std;

// 题目：区间修改，区间求和 (Lanqiao OJ 1133)
// 题意：长度为 N 的数组，支持两种操作：
// 1 l r k: 将区间 [l, r] 的每个数加上 k
// 2 l r: 求区间 [l, r] 的和
// 经典线段树（带 lazy tag，也就是懒标记）。
// N, Q <= 10^5，如果不加 lazy tag 每次更新到叶子节点，必定超时。

// 数据范围很大，数组元素之和可能爆 int，因此所有的 sum, k 都要开 long long
using ll = long long;
const int N = 1e5 + 5;

// a 数组存储最开始的初始值
ll a[N];

// 线段树节点：存的是区间和
ll tree[N * 4];
// lazy tag：存的是“本区间所有元素共同加上的值，还没下传给儿子”
ll lazy_tag[N * 4];

// 建树操作
// node：当前节点编号，l：左端点，r：右端点
void build(int node, int l, int r) {
    if (l == r) {
        tree[node] = a[l];
        return;
    }
    int mid = l + (r - l) / 2;
    // 递归建立左子树和右子树
    build(node * 2, l, mid);
    build(node * 2 + 1, mid + 1, r);
    // 合并子树信息：当前区间的和 = 左半区间的和 + 右半区间的和
    tree[node] = tree[node * 2] + tree[node * 2 + 1];
}

// 核心操作：懒标记下传 (Push Down)
// 只有当我们要访问（更新或查询）儿子节点，但儿子节点的值还没加上之前的欠债时，
// 我们才把“欠条”(lazy_tag)分发给儿子，并更新儿子的区间和。
void push_down(int node, int l, int r) {
    if (lazy_tag[node] != 0) {
        int mid = l + (r - l) / 2;
        int left_child = node * 2;
        int right_child = node * 2 + 1;
        
        // 1. 把欠条传递给左儿子
        lazy_tag[left_child] += lazy_tag[node];
        // 左儿子的区间和，要加上：(左半边的元素个数) * 欠条值
        tree[left_child] += (mid - l + 1) * lazy_tag[node];
        
        // 2. 把欠条传递给右儿子
        lazy_tag[right_child] += lazy_tag[node];
        // 右儿子的区间和，要加上：(右半边的元素个数) * 欠条值
        tree[right_child] += (r - mid) * lazy_tag[node];
        
        // 3. 当前节点的欠债已经结清，清空
        lazy_tag[node] = 0;
    }
}

// 区间修改操作：将 [ql, qr] 范围内的每个数加上 v
void update(int node, int l, int r, int ql, int qr, ll v) {
    // 1. 如果当前节点代表的区间 [l, r] 完全被包在了我们要修改的 [ql, qr] 里面
    // 那么我们不要继续往下递归了！把值加上，记个欠条就撤（这就是懒标记的威力，O(logN)的关键）
    if (ql <= l && r <= qr) {
        tree[node] += (r - l + 1) * v; // 当前区间的和加上新增的这一坨
        lazy_tag[node] += v;           // 记账，以后再说
        return;
    }
    
    // 2. 如果只有一部分重叠，说明必须把原有的账本下发（push_down），
    // 并且去子树里寻找重叠的部分
    push_down(node, l, r);
    int mid = l + (r - l) / 2;
    
    // 左半边有交集，去左边改
    if (ql <= mid) update(node * 2, l, mid, ql, qr, v);
    // 右半边有交集，去右边改
    if (qr > mid)  update(node * 2 + 1, mid + 1, r, ql, qr, v);
    
    // 3. 子树改完了，更新当前节点的和
    tree[node] = tree[node * 2] + tree[node * 2 + 1];
}

// 区间查询操作：求 [ql, qr] 范围内的和
ll query(int node, int l, int r, int ql, int qr) {
    // 1. 如果当前区间完全被包在了查询区间里，这不就是我们要的吗？直接拿走！
    if (ql <= l && r <= qr) {
        return tree[node];
    }
    
    // 2. 如果只有一部分交集，那我们要兵分两路去下面找。
    // 去找之前，必须确保下面的数据是最新的，不能带着旧账，所以必须 push_down！
    push_down(node, l, r);
    int mid = l + (r - l) / 2;
    
    ll res = 0;
    // 如果查询区间和左半边有重叠，把左半边的和拿过来
    if (ql <= mid) res += query(node * 2, l, mid, ql, qr);
    // 如果查询区间和右半边有重叠，把右半边的和拿过来
    if (qr > mid)  res += query(node * 2 + 1, mid + 1, r, ql, qr);
    
    return res;
}

int main() {
    // 优化输入输出流
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    if (!(cin >> n >> q)) return 0;
    
    for (int i = 1; i <= n; ++i) {
        cin >> a[i];
    }
    
    // 首次建树
    build(1, 1, n);
    
    while (q--) {
        int type;
        cin >> type;
        if (type == 1) {
            int l, r;
            ll k;
            cin >> l >> r >> k;
            update(1, 1, n, l, r, k);
        } else if (type == 2) {
            int l, r;
            cin >> l >> r;
            cout << query(1, 1, n, l, r) << "\n";
        }
    }

    return 0;
}
