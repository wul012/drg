#include<bits/stdc++.h>
using namespace std;
using ll =long long;
const int N = 15;
int a[N],n;
vector<int> v[N];

bool dfs(int cnt,int dep) {
    if (dep==n+1) {
        // b7 做法：递归到底时直接返回 true
        // 因为 b7 采用了“剪枝优化”，在放入数字之前就已经检查了合法性
        // 所以只要能放满 n 个数，就说明这是一个合法的分组方案
        return true;
    }
    
    // 尝试把当前数 a[dep] 放入第 i 组
    for (int i=1;i<=cnt;++i) {
        
        // 【核心优化：可行性剪枝】
        // 在把数字放入组内之前，先遍历这组里已有的所有数字 j
        // 检查当前数字 a[dep] 是否与已有的数字 j 存在整除关系
        // 原代码使用了 a[dep]%j==0，（前提是已经从大到小或者从小到大排序）
        bool ok = true;
        for (const auto &j:v[i]) {
            // 如果存在整除或者倍数关系，就不合法
            // （严格来说，为了防止未排序带来的双向整除，应该写 if(a[dep]%j==0 || j%a[dep]==0)）
            if (a[dep]%j==0 || j%a[dep]==0) {
                ok = false;
                break;
            }
        }
        // 如果跟组内现有的某个数冲突，直接跳过这组，尝试下一组 (剪枝)
        if (!ok) continue;
        
        // 放进去
        v[i].push_back(a[dep]);
        
        // 【修复 b5 中的相同错误】：应该是 dep+1 而不是 dep+i
        if (dfs(cnt,dep+1)) return true;
        
        // 拿出来（回溯）
        v[i].pop_back();
    }
    return false;
}

int main() {
    cin>>n;
    for (int i=1;i<=n;++i)cin>>a[i];
    
    // 【修复排序错误】：排的应该是 a 数组，不是 vector 数组 v
    // 为了配合上面的 a[dep]%j==0 检查，建议降序排序
    sort(a+1,a+1+n, greater<int>());
    
    // 迭代加深搜索 (IDA*)
    for (int i=1;i<=n;++i) {
        if (dfs(i,1)) {
            cout<<i<<'\n';
            break; // 【修复】找到最小答案必须 break
        }
    }
    return 0;
}
