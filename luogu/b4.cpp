#include<bits/stdc++.h>
using namespace std;
using ll = long long ;
const int N= 1e3+5;

// mp: 地图，'.'表示海，'#'表示陆地
char mp[N][N];
// col: 记录每个陆地格子属于哪个连通块（岛屿）
// scc: 连通块（岛屿）的编号计数器
int scc,col[N][N];
// vis[i]: 记录第 i 个岛屿是否已经被统计为“不会完全沉没”
bool vis[N*N];
// 四个方向：右，左，下，上
int dx[]={0,0,1,-1},dy[]={1,-1,0,0};
int n; // 移动到这里，统一作为全局变量

// 深度优先搜索，用于划分岛屿（求连通块并染色）
void dfs(int x,int y) {
    col[x][y]=scc; // 染色：将当前陆地标记为第 scc 个岛屿
    // 错误修复1：方向数组下标应从 0 开始，原代码写成了 i=1 漏掉了一个方向
    for (int i=0;i<4;++i) { 
        int nx=x+dx[i],ny=y+dy[i];
        
        // 错误修复2：增加边界检查，防止越界访问
        if (nx < 1 || nx > n || ny < 1 || ny > n) continue;
        
        // 错误修复3：mp[nx][ny] == ',' 是笔误，应该是 '.' (海)
        // 如果相邻格子已经被染色，或者是海洋，则不扩展
        if (col[nx][ny]||mp[nx][ny]=='.')continue;
        
        dfs(nx,ny);
    }
}
int main() {
    ios::sync_with_stdio(0),cin.tie(0),cout.tie(0);
    cin>>n;
    
    // 错误修复4：原代码完全没有读入地图数据！补上读入地图的逻辑
    // 假设输入地图中没有空格，可以直接作为字符串读入每一行
    for (int i=1;i<=n;++i) {
        // C++20 不支持 cin >> char*，使用 scanf 防止编译报错
        scanf("%s", mp[i] + 1); // 从下标 1 开始读入
    }

    // 第一步：遍历全图，使用 DFS 找出所有的岛屿并染色
    for (int i=1;i<=n;++i) {
        for (int j=1;j<=n;++j) {
            // 如果已经被染色，或者是海洋，跳过
            if (col[i][j]||mp[i][j]=='.')continue;
            scc++; // 发现新岛屿，编号加一
            dfs(i,j);
        }
    }
    
    // 错误修复5：ans 未初始化，局部变量默认是随机垃圾值，必须赋值为 0
    int ans = 0; // 记录有多少个岛屿不会完全沉没
    
    // 第二步：遍历全图，检查哪些陆地格子不会被淹没
    for (int i=1;i<=n;++i) {
        for (int j=1;j<=n;++j) {
            if (mp[i][j]=='.')continue; // 只检查陆地格子
            
            bool tag=true; // tag=true 表示该陆地四周都没有海洋，自己不会被淹没
            for (int k=0;k<4;++k) {
                int x=i+dx[k],y=j+dy[k];
                // 如果四周有任何一个是海洋，该格子就会被淹没
                if (mp[x][y]=='.')tag=false;
            }
            
            // 如果该陆地格子不会被淹没，说明它所在的岛屿就不会完全沉没
            if (tag) {
                // 如果这个岛屿还没被统计过，答案加一
                if (!vis[col[i][j]])ans++;
                vis[col[i][j]]=true; // 标记该岛屿已存活
            }
        }
    }
    cout<<ans<<'\n';

    return 0;
}