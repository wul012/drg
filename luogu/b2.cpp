#include<bits/stdc++.h>
using namespace std;
using ll = long long;

// 经典 N 皇后问题
// N 取 20 足够了，因为 N 皇后通常 N<=15，过大的 N 会导致二维数组开太大（内存超限）
const int N = 20;

// vis[i][j] 记录棋盘上点 (i, j) 被多少个皇后攻击（覆盖）
// 值大于 0 说明该位置不可放置
int vis[N][N];
int n, ans;
// dep: 当前正在放置第几行的皇后
void dfs(int dep) {
    // 递归边界：如果已经成功放完了第 n 行的皇后，来到了第 n+1 行
    // 说明找到了一种合法方案
    if (dep==n+1) {
        ans++;
        return;
    }
    
    // 尝试在当前行 (dep) 的每一列 (i) 放置皇后
    for (int i=1;i<=n;++i) {
        // 如果当前位置被攻击了，跳过
        if (vis[dep][i]) continue;

        // 【放置皇后：施加攻击标记】
        // 1. 标记这一列（同一行不需要标记，因为按行枚举天然避开了同行）
        for (int _i=1;_i<=n;++_i) vis[_i][i]++;
        // 2. 标记左上对角线
        for (int _i=dep,_j=i;_i>=1&&_j>=1;--_i,--_j) vis[_i][_j]++;
        // 3. 标记右上对角线
        for (int _i=dep,_j=i;_i>=1&&_j<=n;--_i,++_j) vis[_i][_j]++;
        // 4. 标记左下对角线
        for (int _i=dep,_j=i;_i<=n&&_j>=1;++_i,--_j) vis[_i][_j]++;
        // 5. 标记右下对角线
        for (int _i=dep,_j=i;_i<=n&&_j<=n;++_i,++_j) vis[_i][_j]++;

        // 递归去放下一行
        dfs(dep+1);

        // 【回溯：撤销攻击标记】
        // 之前怎么加的，现在就怎么减，恢复现场，以便尝试该行的下一列
        for (int _i=1;_i<=n;++_i) vis[_i][i]--; // 严重 Bug 修复：这里原来写成了 ++
        for (int _i=dep,_j=i;_i>=1&&_j>=1;--_i,--_j) vis[_i][_j]--;
        for (int _i=dep,_j=i;_i>=1&&_j<=n;--_i,++_j) vis[_i][_j]--;
        for (int _i=dep,_j=i;_i<=n&&_j>=1;++_i,--_j) vis[_i][_j]--;
        for (int _i=dep,_j=i;_i<=n&&_j<=n;++_i,++_j) vis[_i][_j]--;
    }
}

int main() {
    ios::sync_with_stdio(0),cin.tie(0),cout.tie(0);
    cin>>n;
    dfs(1);
    cout<<ans<<'\n'; // Bug 修复：忘记输出结果
    return 0;
}