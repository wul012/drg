#include <iostream>
#include <cstring>
using namespace std;

// 题目：地宫取宝 (蓝桥杯 216)
// 核心思路：记忆化搜索 (DFS + 备忘录)
// 因为要在网格中寻找满足特定条件的路径总数，直接 DFS 会超时。
// 根据题意，影响我们当前决策的状态只有四个：
// 1. 当前横坐标 x
// 2. 当前纵坐标 y
// 3. 手中宝贝的最大价值 max_val
// 4. 手中已经拥有的宝贝数量 cnt
// 我们使用 memo[x][y][max_val][cnt] 来记录这种状态下到达终点有多少种合法方案。

const int MOD = 1000000007;
int n, m, k;
int grid[55][55];

// 备忘录数组，所有维度要比题目的最大值稍微开大一点
// x: [1, 50], y: [1, 50], max_val: [0, 13] (宝贝价值原本是0-12，我们整体加1变成1-13，0表示没拿), cnt: [0, 12]
long long memo[55][55][15][15];

// 记忆化 DFS 函数
// 返回值：从状态 (x, y, max_val, cnt) 出发，走到终点且恰好取 k 个宝贝的路径方案数
long long dfs(int x, int y, int max_val, int cnt) {
    // 【记忆化核心】如果这个状态之前算过了，直接返回备忘录里的答案，避免重复计算
    if (memo[x][y][max_val][cnt] != -1) return memo[x][y][max_val][cnt];

    // 【递归边界】如果已经走到了终点 (n, m)
    if (x == n && y == m) {
        long long res = 0;
        // 情况 1：到达终点时，手中的宝贝已经正好是 k 个了。
        // 那么对于终点这个格子，我们选择【不拿】它的宝贝（或者根本不能拿），这就是 1 种合法方案。
        if (cnt == k) res = (res + 1) % MOD;
        
        // 情况 2：到达终点时，手中的宝贝是 k-1 个，且终点格子的宝贝价值比手中最大的还要大。
        // 那么我们可以选择在终点【拿】起最后这件宝贝，凑齐 k 个，这也是 1 种合法方案。
        if (cnt + 1 == k && grid[x][y] > max_val) res = (res + 1) % MOD;
        
        // 记录到备忘录并返回
        return memo[x][y][max_val][cnt] = res;
    }

    long long res = 0;

    // 【选择 1：不拿当前格子的宝贝】
    // 既然不拿，那手中宝贝的最大价值(max_val)和数量(cnt)都不变，直接向下或向右走
    if (x + 1 <= n) res = (res + dfs(x + 1, y, max_val, cnt)) % MOD;
    if (y + 1 <= m) res = (res + dfs(x, y + 1, max_val, cnt)) % MOD;

    // 【选择 2：拿当前格子的宝贝】
    // 能拿的前提是：当前格子的宝贝价值 > 手中最大的宝贝价值，并且拿了之后总数不会超过限制 k
    if (grid[x][y] > max_val && cnt + 1 <= k) {
        // 拿了之后，最大价值更新为 grid[x][y]，宝贝数量变成 cnt + 1
        if (x + 1 <= n) res = (res + dfs(x + 1, y, grid[x][y], cnt + 1)) % MOD;
        if (y + 1 <= m) res = (res + dfs(x, y + 1, grid[x][y], cnt + 1)) % MOD;
    }

    // 将计算结果存入备忘录
    return memo[x][y][max_val][cnt] = res;
}

int main() {
    // 优化输入输出
    ios::sync_with_stdio(0), cin.tie(0), cout.tie(0);

    cin >> n >> m >> k;
    for (int i = 1; i <= n; ++i) {
        for (int j = 1; j <= m; ++j) {
            cin >> grid[i][j];
            // 【重要技巧】：因为题目的宝贝价值范围是 0~12
            // 如果我们初始的最大价值设为 -1，作为数组下标会越界。
            // 为了方便处理，我们把所有的宝贝价值都加 1，变成 1~13。
            // 这样我们一开始什么都没拿的时候，max_val 就可以安全地设为 0。
            grid[i][j]++;
        }
    }

    // 初始化备忘录为 -1，表示所有状态都还没计算过
    memset(memo, -1, sizeof(memo));

    // 从坐标 (1, 1) 开始，当前手中最大价值为 0，手里有 0 个宝贝
    cout << dfs(1, 1, 0, 0) << "\n";

    return 0;
}
