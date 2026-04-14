#include<bits/stdc++.h>
using namespace std;
typedef long long ll;
const ll INF=1e18;
struct Edge {
    int to;
    ll w;
};
struct Node {
    int id;
    ll dist;
    bool operator<(const Node&other)const {
        return dist>other.dist;
    }
};

int main() {
    ios::sync_with_stdio(0),cin.tie(0),cout.tie(0);
    int n,m;
    if (!(cin>>n>>m))return 0;
    vector<vector<Edge>>adj(n+1);
    for (int i=0;i<m;++i) {
        int u,v;
        ll w;cin>>u>>v>>w;
        adj[u].push_back({v,w});
    }
    vector<ll>dist(n+1,INF);
    vector<bool> vis(n+1,false);
    priority_queue<Node> pq;
    dist[1]=0;
    pq.push({1,0});
    while (!pq.empty()) {
        Node curr=pq.top();
        pq.pop();
        int u=curr.id;
        if (vis[u])continue;
        vis[u]=true;
        for (const Edge&edge:adj[u]) {
            int v=edge.to;
            ll w=edge.w;
            if (!vis[v]&&dist[u]+w<dist[v]) {
                dist[v]=dist[u]+w;
                pq.push({v,dist[v]});
            }
        }
    }

}