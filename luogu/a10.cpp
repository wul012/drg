#include<bits/stdc++.h>
using namespace std;
const int N = 1e5+3;
// a: 原数组, d: 差分数组
int a[N],d[N];

void solve(int n,int m) {
    // 1. 读入原数组
    for (int i=1;i<=n;++i)cin>>a[i];
    
    // 2. 构造差分数组：d[i] = a[i] - a[i-1]
    // 差分数组的性质：前缀和可以还原原数组
    for (int i =1;i<=n;++i)d[i]=a[i]-a[i-1];
    
    // 3. 处理 m 次区间修改操作
    while (m--) {
        int l,r,v;cin>>l>>r>>v;
        // 区间 [l, r] 加上 v，等价于差分数组的两点修改
        d[l]+=v;
        d[r+1]-=v;
    }
    
    // 4. 根据差分数组还原修改后的原数组：a[i] = a[i-1] + d[i]
    for (int i=1;i<=n;++i)a[i]=a[i-1]+d[i];
    
    // 5. 输出结果
    // " \n"[i==n] 技巧：
    // i!=n 时，i==n 为 0，输出 " \n"[0] 也就是空格 ' '
    // i==n 时，i==n 为 1，输出 " \n"[1] 也就是换行 '\n'
    for (int i=1;i<=n;++i)cout<<a[i]<<" \n"[i==n];
}

int main() {
    // 关闭同步流，加速大量输入输出
    ios::sync_with_stdio(0),cin.tie(0),cout.tie(0);
    
    int n,m;
    // 多组测试数据，直到文件结束
    while (cin>>n>>m)solve(n,m);
    return 0;
}