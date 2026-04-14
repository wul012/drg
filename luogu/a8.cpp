#include<bits/stdc++.h>
using namespace std;
using ll=long long ;
const ll p= 1e9+7;      // 模数
const int N=1e5+9;      // 最大数组长度
// a[i][j]: 第 i 次幂，第 j 个位置的值
// a[1][j] = 原始值, a[2][j] = 原始值^2, ..., a[5][j] = 原始值^5
ll a[6][N],prefix[6][N];  // prefix[i][j]: a[i] 的前缀和
int main() {
    ios::sync_with_stdio(0),cin.tie(0),cout.tie(0);
    int n,m;cin>>n>>m;  // n=数组长度, m=查询次数
    
    // 读入原始数组 a[1][1..n]
    for (int i=1;i<=n;++i)cin>>a[1][i];
    // 预处理：计算每个位置的 2~5 次幂
    // a[k][j] = a[1][j]^k (mod p)
    for (int i=2;i<=5;++i)
        for (int j=1;j<=n;++j)
            a[i][j]=a[i-1][j]*a[1][j]%p;  // a[i][j] = a[i-1][j] * a[1][j]
    // 计算每个幂次的前缀和
    // prefix[k][j] = sum(a[k][1..j])
    for (int i=1;i<=5;++i)
        for (int j=1;j<=n;++j)
            prefix[i][j]=(prefix[i][j-1]+a[i][j])%p;
    // 处理 m 个查询
    while (m--) {
        int l,r,k;cin>>l>>r>>k;  // 查询区间 [l,r] 的 k 次幂和
        
        // 区间和 = prefix[k][r] - prefix[k][l-1]
        // +p 是为了防止出现负数（虽然理论上不会）
        cout<<(prefix[k][r]-prefix[k][l-1]+p)%p<<'\n';
    }
    return 0;
}