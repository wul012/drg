#include<bits/stdc++.h>
using namespace std;
using ll = long long ;

// 题目：信息传递 / 找图中的最小/最大环
// 每个人只能向另一个人传递信息，构成一个每个节点出度为 1 的有向图（内向基环树森林）
// 目标：找出图中长度最大的环（根据代码逻辑，这里是求最长环，原题可能是最小环，逻辑类似）
const int N= 1e5+9;

// a[i]: i 号节点指向的下一个节点 (i -> a[i])
// dfn[i]: i 号节点被访问的时间戳 (DFS 序)
// idx: 全局时间戳计数器
// mindfn: 当前这一次 DFS 遍历的起始时间戳
int n,a[N],dfn[N],idx,mindfn;

// dfs: 从节点 x 开始遍历，寻找环并返回环的长度
int dfs(int x) {
    // 1. 记录当前节点 x 的访问时间戳
    dfn[x]=++idx;
    
    // 2. 检查 x 指向的下一个节点 a[x] 是否已经被访问过
    if (dfn[a[x]]) {
        // 如果 a[x] 被访问过，且它的时间戳 >= mindfn
        // 说明 a[x] 是在【当前这一轮 DFS】中被访问的，这意味着我们找到了一个环！
        // 环的长度 = 当前节点时间戳 - 环入口节点时间戳 + 1
        if (dfn[a[x]]>=mindfn) return dfn[x]-dfn[a[x]]+1;
        
        // 如果 a[x] 的时间戳 < mindfn
        // 说明 a[x] 是在【以前的某轮 DFS】中被访问过的，我们走到了以前遍历过的路径上
        // 这种情况下没有产生新的环，直接返回 0
        return 0;
    }
    
    // 3. 如果下一个节点没被访问过，继续沿着指针 dfs 下去
    return dfs(a[x]);
}

int main() {
    // 优化输入输出流
    ios::sync_with_stdio(0),cin.tie(0),cout.tie(0);
    
    cin>>n;
    // 读入每个节点的出边指向
    for (int i =1;i<=n;++i)cin>>a[i];
    
    int ans=0;
    
    // 枚举所有节点作为 DFS 的起点
    for (int i =1;i<=n;++i) {
        // 如果节点 i 还没有被访问过，说明属于一个新的连通块
        if (!dfn[i]) {
            // 记录当前这轮 DFS 的起始时间戳，用于区分“本轮的环”和“以前的旧路径”
            mindfn = idx+1;
            
            // 执行 dfs，并用找到的环的长度更新答案
            ans = max(ans,dfs(i));
        }
    }
    
    cout<<ans<<'\n';
    return 0;
}