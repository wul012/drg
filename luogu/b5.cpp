#include<bits/stdc++.h>
using namespace std;
using ll =long long;
// 题目：将 n 个数分成最少的组，使得每组内任意两个数都不存在整除关系
const int N = 15;
int a[N],n;
// v[i] 存储第 i 组里的所有数字
vector<int> v[N];

// cnt: 当前允许使用的最大组数
// dep: 当前正在尝试把第 dep 个数字（a[dep]）放入某一组
bool dfs(int cnt,int dep) {
    // 递归边界：如果已经成功把 n 个数都放入了组中，说明当前 cnt 个组是可行的
    if (dep==n+1) {
        // b5 做法：在递归到底的时候，才集中检查所有组是否合法
        // 这是低效的“生成-测试”法，会在中途生成大量必然非法的方案，导致 TLE
        for (int i=1;i<=cnt;++i) {
            for (int j=0;j<v[i].size();++j) {
                for (int k=j+1;k<v[i].size();++k) {
                    // 如果组内存在整除关系，这组就是不合法的
                    if (v[i][k]%v[i][j]==0) return false;
                }
            }
        }
        return true;
    }
    
    // 尝试把当前数 a[dep] 放入第 i 组 (1 <= i <= cnt)
    for (int i=1;i<=cnt;++i) {
        v[i].push_back(a[dep]);
        
        // 【严重错误】原代码：dfs(cnt, dep+i)
        // 逻辑错误：进入下一层应该是处理下一个数，也就是 dep+1
        // 写成 dep+i 会导致直接跳过中间很多数，且越界
        if (dfs(cnt,dep+1)) return true;
        
        // 回溯：把 a[dep] 拿出来，尝试放到别的组
        v[i].pop_back();
    }
    return false;
}

int main() {
    cin>>n;
    for (int i=1;i<=n;++i)cin>>a[i];
    
    // 【错误】：原代码 sort(v+1,v+1+n);
    // 这里排的是 vector 数组，而不是输入的数字 a 数组
    // 正确应该是：sort(a+1, a+1+n); 排序能优化搜索顺序（从大到小或者从小到大）
    sort(a+1,a+1+n);
    
    // 迭代加深搜索 (IDA*)
    // 从小到大枚举允许的最大组数 i，如果能成功，i 就是最少需要的组数
    for (int i=1;i<=n;++i) {
        if (dfs(i,1)) {
            cout<<i<<'\n';
            break; // 【错误修复】找到最小答案后必须 break 退出循环！否则会继续输出
        }
    }
    return 0;
}
