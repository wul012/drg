#include <iostream>
#include <vector>
#include <string>
#include <cstring>

using namespace std;
using ll = long long;

// ============================================================
// 题目：不要 62（数位 DP）
// ============================================================
//
// 【题目要求】
// 给定区间 [L, R]，统计其中有多少个整数满足：
// 1. 十进制表示中不包含数字 4
// 2. 不包含连续子串 62
//
// 【输入格式】
// 一行两个整数 L R
//
// 【输出格式】
// 输出满足条件的整数个数。
//
// 【样例输入】
// 60 70
//
// 【样例输出】
// 9
//
// 【样例解释】
// 60~70 一共 11 个数：
// 60 61 62 63 64 65 66 67 68 69 70
// 其中 62 含有子串 62，不合法；64 含有数字 4，不合法。
// 所以答案 = 11 - 2 = 9。
//
// 【为什么用数位 DP？】
// 如果直接从 L 枚举到 R 再逐个判断，当区间很大时会很慢。
// 数位 DP 的经典套路是：
//   ans = solve(R) - solve(L-1)
// 其中 solve(x) 表示 [0, x] 内合法数字的个数。
//
// 【状态设计】
// dfs(pos, prevSix, started, limit)
// 含义：
// - 当前处理到第 pos 位
// - prevSix：前一位（真实数字位）是否是 6
// - started：前面是否已经出现过非前导零数字
// - limit：当前位是否受到上界限制
//
// 为什么需要 started？
// 因为前导零不应该被当成真实数字参与“不能有 4、不能有 62”的判断。
// 比如数字 7，在高位补零后是 0007，这些前导零不能影响状态。
//
// 【转移规则】
// 枚举当前位填 d：
// - 如果已经开始构造数字（started=true），或者 d 非 0 使得数字刚开始：
//   1) d 不能是 4
//   2) 如果上一位是 6，则 d 不能是 2
// - 如果仍处于前导零阶段，则不受这些限制
// ============================================================

vector<int> digits;
ll memo[20][2][2];
bool vis[20][2][2];

ll dfs(int pos, int prevSix, int started, bool limit) {
    if (pos == (int)digits.size()) {
        // 走到末尾，说明构造出一个合法数
        // 即使一直没 started，也对应数字 0，本题中也算合法
        return 1;
    }

    if (!limit && vis[pos][prevSix][started]) {
        return memo[pos][prevSix][started];
    }

    int up = limit ? digits[pos] : 9;
    ll res = 0;

    for (int d = 0; d <= up; ++d) {
        bool nextLimit = limit && (d == up);

        if (!started && d == 0) {
            // 仍然在前导零阶段，前一位是否是 6 应重置为 false
            res += dfs(pos + 1, 0, 0, nextLimit);
            continue;
        }

        // 从这里开始，d 是一个真实数字位
        if (d == 4) continue;
        if (prevSix && d == 2) continue;

        res += dfs(pos + 1, d == 6, 1, nextLimit);
    }

    if (!limit) {
        vis[pos][prevSix][started] = true;
        memo[pos][prevSix][started] = res;
    }

    return res;
}

ll solve(ll x) {
    if (x < 0) return 0;
    digits.clear();
    string s = to_string(x);
    for (char c : s) digits.push_back(c - '0');
    memset(vis, 0, sizeof(vis));
    return dfs(0, 0, 0, true);
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    ll L, R;
    if (!(cin >> L >> R)) return 0;

    cout << solve(R) - solve(L - 1) << '\n';
    return 0;
}

/*
============================================================
【手推样例】
区间 [60, 70]

我们实际计算：solve(70) - solve(59)
意思是：
[0,70] 的合法数个数 - [0,59] 的合法数个数 = [60,70] 的合法数个数

直接枚举区间验证：
60 合法
61 合法
62 不合法（出现子串 62）
63 合法
64 不合法（出现数字 4）
65 合法
66 合法
67 合法
68 合法
69 合法
70 合法

所以答案是 9。

数位 DP 真正厉害的地方在于：
当区间扩大到 1 ~ 10^18 时，它也不需要逐个枚举数字，
而是按“数位状态”统一统计。
============================================================
【易错点总结】
1. 区间统计一定写成 solve(R) - solve(L-1)。
2. 前导零不能参与“62”判断，所以需要 started 状态。
3. 记忆化一般只在 limit=false 时使用。
4. 本题中数字 0 是合法的，因此 dfs 到末尾返回 1。
============================================================
*/
