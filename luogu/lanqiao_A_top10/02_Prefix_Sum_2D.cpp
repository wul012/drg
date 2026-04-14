#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

// 题型 2：前缀和与差分 (蓝桥杯基础提速利器)
// 【具体真题】：最大子矩阵 (蓝桥杯 2022 省赛)
// 题目描述：
// 给定一个 N*M 的矩阵，要求找出一个子矩阵，使得该子矩阵中最大值和最小值的差不超过 limit，
// 并且该子矩阵的面积最大（即包含的元素个数最多）。
// 求这个最大面积。这里为了演示最基础的二维前缀和，我们把题目简化为：
// “给定一个 N*M 的矩阵，求所有面积为 K*K 的子矩阵中，元素和最大是多少？”

const int N = 1005;
long long a[N][N], sum[N][N];

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, k;
    if (!(cin >> n >> m >> k)) return 0;
    
    // 读入矩阵并同时构造二维前缀和
    for (int i = 1; i <= n; ++i) {
        for (int j = 1; j <= m; ++j) {
            cin >> a[i][j];
            // 二维前缀和递推公式：当前点 = 上方块 + 左方块 - 左上方重叠块 + 当前值
            sum[i][j] = sum[i - 1][j] + sum[i][j - 1] - sum[i - 1][j - 1] + a[i][j];
        }
    }
    
    long long max_sum = -1e18; // 初始化为极小值
    
    // 枚举所有大小为 K*K 的子矩阵的右下角坐标 (i, j)
    // 因为子矩阵大小是 K*K，所以右下角的坐标至少是 (k, k)
    for (int i = k; i <= n; ++i) {
        for (int j = k; j <= m; ++j) {
            // 计算左上角坐标
            int x1 = i - k + 1;
            int y1 = j - k + 1;
            int x2 = i;
            int y2 = j;
            
            // O(1) 计算子矩阵的和：大块 - 上半块 - 左半块 + 左上方被多减去的块
            long long current_sum = sum[x2][y2] - sum[x1 - 1][y2] - sum[x2][y1 - 1] + sum[x1 - 1][y1 - 1];
            max_sum = max(max_sum, current_sum);
        }
    }
    
    cout << max_sum << "\n";
    
    return 0;
}

/*
========== 测试数据 ==========
输入：
4 5 2
1 2 3 4 5
6 7 8 9 10
11 12 13 14 15
16 17 18 19 20

输出：
68

解释：
最大的 2*2 子矩阵在右下角：
14 15
19 20
和为 14+15+19+20 = 68
============================
*/
