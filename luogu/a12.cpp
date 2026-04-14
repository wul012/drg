#include<bits/stdc++.h>
using namespace std;
using ll=long long;

// 定义一个小根堆（优先队列，每次 pop 出来的都是最小值）
// priority_queue 的三个模板参数含义：
// 1. ll: 队列中存储的元素类型是 long long
// 2. vector<ll>: 底层用来实现堆的容器类型，一般使用 vector
// 3. greater<ll>: 比较函数（仿函数）。greater 表示“大于”时下沉，最终堆顶是最小值，形成小根堆。
//                如果不写后两个参数，默认是 less<ll>，形成大根堆（每次 pop 最大值）。
priority_queue<ll,vector<ll>,greater<ll>> pq;

int main() {
    // 优化输入输出流
    ios::sync_with_stdio(0),cin.tie(0),cout.tie(0);

    int n;cin>>n;
    // 读入所有果子的重量，并直接压入小根堆中
    for (int i = 1;i<=n;++i) {
        ll x;cin>>x;
        pq.push(x);
    }
    
    ll ans = 0; // 记录总的体力消耗（代价）
    
    // 经典贪心算法：合并果子（哈夫曼树）
    // 只要堆里还有两堆或以上的果子，就继续合并
    while (pq.size()>1) {
        // 取出当前最小的两堆
        ll x = pq.top();pq.pop();
        ll y = pq.top();pq.pop();
        
        // 合并这两堆需要消耗 x+y 的体力
        ans+=x+y;
        
        // 将合并后的新果子堆重新放回优先队列
        pq.push(x+y);
    }
    
    // 输出最小总消耗
    cout<<ans<<'\n';
    return 0;
}