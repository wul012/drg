#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

// 题型 3：二分答案 (蓝桥杯“使最大值最小”或“最小值最大”类型题的杀手锏)
// 【具体真题】：跳石头 (洛谷 P2678 / NOIP / 蓝桥杯常客)
// 题目描述：
// 一条河的起点到终点距离为 L。河中间有 N 块石头。
// 现在最多可以移走 M 块石头，要求移走石头后，所有相邻两块石头之间的距离的【最小值最大化】。
// 求这个最大的最小距离。

const int N = 50005;
long long a[N];

// check 函数：判断假设的最短跳跃距离 x 是否可行
// 如果要求所有石头间距都 >= x，我们最少需要移走几块石头？
bool check(long long x, int n, int m, long long L) {
    int remove_count = 0; // 记录需要移走的石头数量
    long long last_pos = 0; // 记录上一块没被移走的石头的位置（最开始在起点 0）
    
    for (int i = 1; i <= n; ++i) {
        // 如果当前石头距离上一块石头的距离 < x，说明间距不达标
        // 必须把当前这块石头移走！
        if (a[i] - last_pos < x) {
            remove_count++;
        } else {
            // 如果距离 >= x，达标了，保留这块石头，更新 last_pos
            last_pos = a[i];
        }
    }
    
    // 最后还要检查最后一块保留的石头到终点的距离
    if (L - last_pos < x) {
        remove_count++;
    }
    
    // 如果需要的移走数量 <= 允许的最大移走数量 M，说明这个 x 是可行的方案
    return remove_count <= m;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long L;
    int n, m; 
    if (!(cin >> L >> n >> m)) return 0;
    
    for (int i = 1; i <= n; ++i) {
        cin >> a[i];
    }
    
    // 题目输入可能没保证有序，最好排个序
    sort(a + 1, a + 1 + n);
    
    // 二分答案的上下界：
    // 最短距离最小可能是 1，最大可能是直接从起点跳到终点 L
    long long left = 1, right = L; 
    long long ans = 0;
    
    // 经典的二分模板
    while (left <= right) {
        long long mid = left + (right - left) / 2; // 猜一个最短跳跃距离 mid
        
        if (check(mid, n, m, L)) {
            // 如果 mid 可行，说明答案可能还能更大（因为我们要找最大的最小距离）
            ans = mid; // 暂存可行解
            left = mid + 1; // 去右半区找更大的
        } else {
            // 如果不可行（需要移走的石头超过了 M 块），说明步子迈太大了
            right = mid - 1; // 去左半区找小一点的
        }
    }
    
    cout << ans << "\n";
    return 0;
}

/*
========== 测试数据 ==========
输入：
25 5 2
2
11
14
17
21

输出：
4

解释：
起点 0，终点 25。石头在 2, 11, 14, 17, 21。
移走位置 2 和 14 的石头后，剩下的石头为 11, 17, 21。
间距分别为：
0 -> 11 (距 11)
11 -> 17 (距 6)
17 -> 21 (距 4)
21 -> 25 (距 4)
最短距离为 4。如果想让最短距离变成 5，移走 2 块石头是不够的。
============================
*/
