#include<bits/stdc++.h>
using namespace std;

// mp: 用 map 记录每个数字出现的次数
// key = 数字本身, value = 该数字出现的次数
map<int,int> mp;

int main() {
    // 关闭 stdio 同步、解绑 cin/cout，加速输入输出
    ios::sync_with_stdio(0),cin.tie(0),cout.tie(0);

    // 读入矩阵的行数 n 和列数 m
    int n,m;cin>>n>>m;

    // 共有 n*m 个元素，逐个读入并统计频次
    for (int i=1;i<=n*m;++i) {
        int x;cin>>x;   // 读入当前元素
        mp[x]++;        // 该元素的计数 +1
    }

    // 遍历 map 中所有 (数字, 出现次数) 的键值对
    
    // 【方法1】C++17 结构化绑定写法（洛谷/CF 可用，蓝桥杯有风险）
    // for (const auto &[x,y]:mp) {
    //     // x = 数字本身 (key), y = 该数字出现的次数 (value)
    //     if (2*y>n*m)cout<<x<<'\n';
    // }
    
    // 【方法2】传统写法，兼容 C++11（蓝桥杯推荐）
    for (const auto &p : mp) {
        // p.first = 数字本身 (key)
        // p.second = 该数字出现的次数 (value)
        
        // 判断是否为主元素: 出现次数超过总数的一半
        // 2*p.second > n*m 等价于 p.second > n*m/2
        // 用乘法避免整数除法的精度问题
        if (2*p.second > n*m) {
            cout << p.first << '\n';
        }
    }
    return 0;
}