#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

// 题型 9：双指针与尺取法 (蓝桥杯 O(N) 优化利器)
// 【具体真题】：日志统计 (蓝桥杯 2018 省赛)
// 题目描述：
// 小明维护着一个包含 N 条日志的数组，每条日志包含两个整数：ts（发生的时间）和 id（帖子编号）。
// 规定：如果一个帖子在任意连续的 D 个时间单位内（即 [T, T+D-1] 这段时间内）
// 受到了不少于 K 个赞，该帖子就会被系统判定为“热帖”。
// 求出所有被判定为热帖的编号（按从小到大排序输出）。

// 核心思想：既然是在“连续的一段时间内”找满足条件的帖子，这就是典型的【滑动窗口 / 尺取法】。

const int MAX_ID = 100005;

struct Log {
    int ts; // 时间戳
    int id; // 帖子编号
    
    // 按时间戳从小到大排序
    bool operator<(const Log& other) const {
        return ts < other.ts;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, d, k;
    if (!(cin >> n >> d >> k)) return 0;
    
    vector<Log> logs(n);
    for (int i = 0; i < n; ++i) {
        cin >> logs[i].ts >> logs[i].id;
    }
    
    // 1. 必须先按时间排序，这样窗口滑动才有意义
    sort(logs.begin(), logs.end());
    
    // cnt 数组记录当前窗口内，每个 id 获得了多少个赞
    vector<int> cnt(MAX_ID, 0);
    // hot 数组记录某个 id 是否已经成为了热帖（防止重复输出）
    vector<bool> hot(MAX_ID, false);
    
    int left = 0; // 窗口的左边界
    int right = 0; // 窗口的右边界
    
    // 2. 双指针滑动窗口核心逻辑
    while (right < n) {
        // 右指针负责把新日志吃进窗口
        int current_id = logs[right].id;
        cnt[current_id]++;
        
        // 关键：检查窗口是否超长了（时间跨度 >= D）
        // 如果超了，左边界必须不断往右缩，直到窗口时间跨度合法
        while (logs[right].ts - logs[left].ts >= d) {
            // 左边界对应的帖子要被踢出窗口了，它的赞数减 1
            cnt[logs[left].id]--;
            left++; // 左指针向右移
        }
        
        // 检查当前刚吃进来的帖子，在合法窗口内是否达到了热帖标准 K
        if (cnt[current_id] >= k) {
            hot[current_id] = true;
        }
        
        right++; // 右指针继续扩张
    }
    
    // 3. 按从小到大输出所有热帖
    for (int i = 0; i < MAX_ID; ++i) {
        if (hot[i]) cout << i << "\n";
    }
    
    return 0;
}

/*
========== 测试数据 ==========
输入：
7 10 2
0 1
0 10
10 10
10 1
9 1
100 3
100 3

输出：
1
3

解释：
N=7条日志，时间跨度D=10内，点赞数>=K=2成为热帖。
帖子 1 在 ts=0 和 ts=9 各有一个赞，时间跨度 9-0=9 < 10，符合条件，是热帖。
帖子 3 在 ts=100 连续两个赞，是热帖。
帖子 10 只有在 ts=0 和 ts=10 有赞，时间跨度 10-0=10，规定必须在 [T, T+D-1] 内，即严格小于 D，不符合。
所以只有 1 和 3 是热帖。
============================
*/
