#include <iostream>
#include <cstring>
using namespace std;
const int MOD = 1000000007;
int n, m, k;
int grid[55][55];
long long memo[55][55][15][15];
long long dfs(int x, int y, int max_val, int cnt) {
if (memo[x][y][max_val][cnt] != -1) return memo[x][y][max_val][cnt];
if (x == n && y == m) {
long long res = 0;
if (cnt == k) res = (res + 1) % MOD;
if (cnt + 1 == k && grid[x][y] > max_val - 1) res = (res + 1) % MOD;
return memo[x][y][max_val][cnt] = res;
}
long long res = 0;
if (x + 1 <= n) res = (res + dfs(x + 1, y, max_val, cnt)) % MOD;
if (y + 1 <= m) res = (res + dfs(x, y + 1, max_val, cnt)) % MOD;
if (grid[x][y] > max_val - 1 && cnt + 1 <= k) {
if (x + 1 <= n) res = (res + dfs(x + 1, y, grid[x][y] + 1, cnt + 1)) % MOD;
if (y + 1 <= m) res = (res + dfs(x, y + 1, grid[x][y] + 1, cnt + 1)) % MOD;
}
return memo[x][y][max_val][cnt] = res;
}
int main() {
cin >> n >> m >> k;
for(int i=1; i<=n; ++i) for(int j=1; j<=m; ++j) { cin >> grid[i][j]; grid[i][j]++; }
memset(memo, -1, sizeof(memo));
cout << dfs(1, 1, 0, 0) << endl;
return 0;
}
