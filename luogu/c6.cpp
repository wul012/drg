#include<bits/stdc++.h>
using namespace std;
using ll =long long;
const ll INF=1e18;


int main() {
    ios::sync_with_stdio(0),cin.tie(0),cout.tie(0);
    int n,m,q;
    if (!(cin>>n>>m>>q))return 0;
    vector<vector<ll>> dp(n+1,vector<ll>(n+1,INF));
    for (int i=1;i<=n;++i) {
        dp[i][i]=0;
    }
    for (int i=0;i<=m;++i) {
        int u,v;
        ll w;
        cin>>u>>v>>w;
        dp[u][v]=min(dp[u][v], w);
        dp[v][u]=min(dp[v][u],w);
    }
    for (int k=1;k<=n;++k){
        for (int i=1;i<=n;++i) {
            for (int j=1;j<=n;++j) {
                if (dp[i][k]!=INF&&dp[k][j]!=INF) {
                    dp[i][j]=min(dp[i][j],dp[i][k]+dp[k][j]);
                }
            }
        }
}
    while (q--) {
        int st,ed;
        cin>>st>>ed;
        if (dp[st][ed]==INF) {
            cout<<-1<<"\n";
        }else {
            cout<<dp[st][ed]<<"\n";
        }
    }


    return 0;
}
