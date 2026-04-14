#include<bits/stdc++.h>
using namespace std;
const int N=1e5+9;
int a[N];
int main() {
    // 优化输入输出速度
    ios::sync_with_stdio(0),cin.tie(0),cout.tie(0);

    int n;cin>>n;
    // 数组从下标 1 开始读入，存储在 a[1] 到 a[n]
    for (int i=1;i<=n;++i)cin>>a[i];
    
    // sort 函数对区间进行排序
    // a+1 是起点，a+n+1 是终点
    sort(a+1,a+n+1);
    
    int ans=a[2]-a[1];
    
    // 寻找排序后相邻元素的最小差值
    // 注意：这里必须是 i < n，因为用到了 a[i+1]
    // 原代码是 i <= n，当 i=n 时会访问 a[n+1](值为0)，导致计算出错误的负数差值
    for (int i=1;i<n;++i)ans=min(ans,a[i+1]-a[i]);
    
    cout<<ans<<'\n';
    return 0;
}
