#include<bits\stdc++.h>
using namespace std;

// 题目：扫雷游戏（类似经典扫雷）
// 给定一个 n×m 的矩阵，1 表示地雷，0 表示空地
// 对于每个位置，输出其周围 8 个方向（包括对角线）的地雷数量
// 如果该位置本身是地雷，输出 9

const int N=150;
int mp[N][N];   // 原始地图：mp[i][j]=1 表示地雷，0 表示空地
int ans[N][N];  // 结果矩阵：存储每个位置周围的地雷数量

int main() {
    // 读入矩阵的行数 n 和列数 m
    int n,m;
    cin>>n>>m;
    
    // 读入地图数据
    for (int i=1;i<=n;++i) {
        for (int j=1;j<=m;++j) {
            cin>>mp[i][j];
        }
    }
    
    // 计算每个位置的答案
    for (int i=1;i<=n;++i) {
        for (int j=1;j<=m;++j) {
            // 如果当前位置是地雷，直接标记为 9
            if (mp[i][j]==1) {
                ans[i][j]=9;
                continue;
            }
            
            // 否则，统计周围 8 个方向的地雷数量
            // 遍历以 (i,j) 为中心的 3×3 区域
            for (int _i=max(1,i-1);_i<=min(n,i+1);++_i) {
                for (int _j=max(1,j-1);_j<=min(m,j+1);++_j ) {
                    // 如果周围位置是地雷，计数 +1
                    if (mp[_i][_j]) ans[i][j]++;
                }
            }
        }
    }
    
    // 输出结果矩阵
    for (int i = 1; i <= n; ++i) {
        for (int j = 1; j <= m; ++j) {
            cout << ans[i][j];
            if (j < m) cout << ' ';  // 每行最后一个数字后不加空格
        }
        cout << '\n';  // 每行结束后换行
    }

    return 0;
}