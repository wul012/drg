#include<bits/stdc++.h>
using namespace std;
using ll=long long;

// 题目：求斐波那契数列的前 n 项，并对 1e9+7 取模
const int N=1e5+9;      // 数列最大项数
const ll p = 1e9+7;     // 取模的大素数，防止计算过程中数值溢出

// dp[i]：用于记忆化搜索的数组，存储第 i 项的斐波那契数
// 全局数组默认初始化为 0，刚好用来判断某一项是否已经计算过
ll dp[N];

// fib 函数：计算第 n 项斐波那契数
ll fib(int n) {
    // 记忆化搜索的核心：如果 dp[n] 不为 0，说明之前已经计算过了，直接返回结果，避免重复计算
    // 这是将指数级复杂度 O(2^n) 优化为线性复杂度 O(n) 的关键
    if (dp[n]) return dp[n];
    
    // 递归的边界条件：斐波那契数列的第一项和第二项都是 1
    if (n<=2) return 1;
    
    // 递归计算前两项之和，并在每次加法后都对 p 取模
    // 计算完成后，将结果存入 dp[n] 中（记忆化），然后再返回
    return dp[n]=(fib(n-1)+fib(n-2))%p;
}

int main() {
    // 优化输入输出速度
    ios::sync_with_stdio(0),cin.tie(0),cout.tie(0);
    
    int n;cin>>n;
    
    // 依次输出从第 1 项到第 n 项的斐波那契数
    for (int i = 1;i<=n;++i) cout<<fib(i)<<'\n';
    
    return 0;
}