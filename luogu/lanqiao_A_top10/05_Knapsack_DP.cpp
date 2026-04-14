#include <iostream>
#include <vector>
#include <numeric>
#include <algorithm>

using namespace std;

// 题型 5：背包类 DP (01背包变种)
// 【具体真题】：分金币 / 调手表 (蓝桥杯常考的“把数组分成两半，差值最小”的模型)
// 题目描述：
// 有 N 堆金币，第 i 堆有 a[i] 个金币。
// 现在要把这 N 堆金币分给两个人，要求两个人分得的金币总数之差尽可能小。
// 问最小的差值是多少？（每堆金币不能拆开）

// 核心思路：
// 把所有金币加起来得到 sum。最理想的情况是每个人分到 sum / 2。
// 所以这其实是一个【01背包问题】：
// 背包容量为 sum / 2，物品是这 N 堆金币，每个物品的体积和价值都是 a[i]。
// 求在这个背包里最多能装多少价值？装得越满，差值越小。

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    if (!(cin >> n)) return 0;
    
    vector<int> a(n);
    int sum = 0;
    for (int i = 0; i < n; ++i) {
        cin >> a[i];
        sum += a[i];
    }
    
    int target = sum / 2;
    // dp[j] 表示容量为 j 的背包，最多能装多少金币
    vector<int> dp(target + 1, 0);
    
    for (int i = 0; i < n; ++i) {
        int w = a[i];
        // 01 背包必须逆序遍历，确保每堆金币只拿 1 次
        for (int j = target; j >= w; --j) {
            dp[j] = max(dp[j], dp[j - w] + w);
        }
    }
    
    // 一个人拿了 dp[target]，另一个人拿了 sum - dp[target]
    // 差值就是两者的绝对值之差
    int diff = abs((sum - dp[target]) - dp[target]);
    
    cout << diff << "\n";
    
    return 0;
}

/*
========== 测试数据 ==========
输入：
5
1 2 3 4 5

输出：
1

解释：
总和为 15，目标是凑 7。
一个人拿 1, 2, 4 (和为 7)
另一个人拿 3, 5 (和为 8)
差值为 1。
============================
*/
