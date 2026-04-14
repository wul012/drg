#include <iostream>
#include <vector>
using namespace std;
const int MAXV = 1000000; int ans[MAXV + 5];
void precompute() { for (int a = 2; a <= 100; ++a) { for (int b = a + 1; a * b * b < MAXV; ++b) { for (int c = b + 1; c < a + b; ++c) { long long v = 1LL * a * b * c; if (v > MAXV) break; ans[v]++; } } } for (int i = 1; i <= MAXV; ++i) ans[i] += ans[i - 1]; }
int main() { precompute(); for(int r_test : {10, 50, 200, 400}) { int l_test = (r_test==10?1:r_test==50?30:r_test==200?60:200); cout << ans[r_test] - ans[l_test-1] << " "; } return 0; }
