#include <cassert>
#include <iostream>
#include <string>
#include <vector>

#include "morris.h"
#include "coins_min.h"

#ifdef _WIN32
#include <windows.h>
#endif

// ============================================================================
//                    Morris 遍历测试说明（入门友好）
// ============================================================================
// 目标：验证 Morris 遍历算法的核心接口：
// - `morris::preorderMorris(root)` 返回前序遍历结果
// - `morris::inorderMorris(root)` 返回中序遍历结果
// - `morris::postorderMorris(root)` 返回后序遍历结果
// - `morris::buildTree(arr)` 从数组构建二叉树
//
// 测试用例的树结构：
//
// 测试树1：
//       1
//      / \
//     2   3
//    / \
//   4   5
//
// 测试树2：
//       1
//        \
//         2
//        /
//       3
//
// 测试树3（完全二叉树）：
//         1
//       /   \
//      2     3
//     / \   / \
//    4   5 6   7
// ============================================================================

// ============================================================================
//                    硬币问题测试说明（入门友好）
// ============================================================================
// 目标：验证硬币问题算法的核心接口：
// - `coins_min::minCoinsRecursive(arr, amount)` 暴力递归方法
// - `coins_min::minCoinsDp(arr, amount)` 动态规划方法
//
// 测试用例说明：
// 1. 基本测试：常见硬币组合
// 2. 边界测试：空数组、金额为0、无法凑成
// 3. 对拍测试：递归和DP结果一致性
// ============================================================================

void testCoinsMin() {
    using coins_min::minCoinsRecursive;
    using coins_min::minCoinsDp;

    // ========================================================================
    // 测试1：经典案例 - LeetCode 322 示例
    // ========================================================================
    // arr = [1, 2, 5], amount = 11
    // 最少硬币：5 + 5 + 1 = 11，需要 3 枚
    {
        std::vector<int> coins = {1, 2, 5};
        assert(minCoinsRecursive(coins, 11) == 3);
        assert(minCoinsDp(coins, 11) == 3);
    }

    // ========================================================================
    // 测试2：无法凑成的情况
    // ========================================================================
    // arr = [2], amount = 3
    // 只有面值2的硬币，无法凑成3
    {
        std::vector<int> coins = {2};
        assert(minCoinsRecursive(coins, 3) == -1);
        assert(minCoinsDp(coins, 3) == -1);
    }

    // ========================================================================
    // 测试3：金额为0
    // ========================================================================
    // 不需要任何硬币
    {
        std::vector<int> coins = {1, 2, 5};
        assert(minCoinsRecursive(coins, 0) == 0);
        assert(minCoinsDp(coins, 0) == 0);
    }

    // ========================================================================
    // 测试4：空硬币数组
    // ========================================================================
    {
        std::vector<int> coins = {};
        assert(minCoinsRecursive(coins, 5) == -1);
        assert(minCoinsDp(coins, 5) == -1);
    }

    // ========================================================================
    // 测试5：单个硬币恰好等于金额
    // ========================================================================
    {
        std::vector<int> coins = {5};
        assert(minCoinsRecursive(coins, 5) == 1);
        assert(minCoinsDp(coins, 5) == 1);
    }

    // ========================================================================
    // 测试6：需要选择最优方案
    // ========================================================================
    // arr = [1, 3, 4], amount = 6
    // 贪心会选 4+1+1=6（3枚），但最优是 3+3=6（2枚）
    {
        std::vector<int> coins = {1, 3, 4};
        assert(minCoinsRecursive(coins, 6) == 2);
        assert(minCoinsDp(coins, 6) == 2);
    }

    // ========================================================================
    // 测试7：较大金额
    // ========================================================================
    // arr = [1, 2, 5], amount = 100
    // 最优：20 个 5 元硬币
    {
        std::vector<int> coins = {1, 2, 5};
        // 递归版本对于大金额可能较慢，主要测试 DP 版本
        assert(minCoinsDp(coins, 100) == 20);
    }

    // ========================================================================
    // 测试8：对拍测试 - 递归和DP结果一致性
    // ========================================================================
    {
        std::vector<int> coins = {2, 3, 7};
        for (int amount = 0; amount <= 20; ++amount) {
            int recursive_result = minCoinsRecursive(coins, amount);
            int dp_result = minCoinsDp(coins, amount);
            assert(recursive_result == dp_result);
        }
    }

    // ========================================================================
    // 测试9：多种硬币组合
    // ========================================================================
    {
        std::vector<int> coins = {1, 5, 10, 25};
        // 30 = 25 + 5 = 2枚
        assert(minCoinsDp(coins, 30) == 2);
        // 31 = 25 + 5 + 1 = 3枚
        assert(minCoinsDp(coins, 31) == 3);
    }
}

void testMorris() {
    using morris::TreeNode;
    using morris::buildTree;
    using morris::freeTree;
    using morris::preorderMorris;
    using morris::inorderMorris;
    using morris::postorderMorris;

    // ========================================================================
    // 测试1：标准二叉树
    // ========================================================================
    //       1
    //      / \
    //     2   3
    //    / \
    //   4   5
    {
        TreeNode* root = buildTree({1, 2, 3, 4, 5});

        // 前序遍历：根 -> 左 -> 右
        // 期望：1 -> 2 -> 4 -> 5 -> 3
        std::vector<int> preorder = preorderMorris(root);
        assert(preorder == std::vector<int>({1, 2, 4, 5, 3}));

        // 中序遍历：左 -> 根 -> 右
        // 期望：4 -> 2 -> 5 -> 1 -> 3
        std::vector<int> inorder = inorderMorris(root);
        assert(inorder == std::vector<int>({4, 2, 5, 1, 3}));

        // 后序遍历：左 -> 右 -> 根
        // 期望：4 -> 5 -> 2 -> 3 -> 1
        std::vector<int> postorder = postorderMorris(root);
        assert(postorder == std::vector<int>({4, 5, 2, 3, 1}));

        freeTree(root);
    }

    // ========================================================================
    // 测试2：只有右子树的链状树
    // ========================================================================
    //   1
    //    \
    //     2
    //      \
    //       3
    {
        TreeNode* root = buildTree({1, -1, 2, -1, 3});

        std::vector<int> preorder = preorderMorris(root);
        assert(preorder == std::vector<int>({1, 2, 3}));

        std::vector<int> inorder = inorderMorris(root);
        assert(inorder == std::vector<int>({1, 2, 3}));

        std::vector<int> postorder = postorderMorris(root);
        assert(postorder == std::vector<int>({3, 2, 1}));

        freeTree(root);
    }

    // ========================================================================
    // 测试3：只有左子树的链状树
    // ========================================================================
    //       1
    //      /
    //     2
    //    /
    //   3
    {
        TreeNode* root = buildTree({1, 2, -1, 3});

        std::vector<int> preorder = preorderMorris(root);
        assert(preorder == std::vector<int>({1, 2, 3}));

        std::vector<int> inorder = inorderMorris(root);
        assert(inorder == std::vector<int>({3, 2, 1}));

        std::vector<int> postorder = postorderMorris(root);
        assert(postorder == std::vector<int>({3, 2, 1}));

        freeTree(root);
    }

    // ========================================================================
    // 测试4：完全二叉树
    // ========================================================================
    //         1
    //       /   \
    //      2     3
    //     / \   / \
    //    4   5 6   7
    {
        TreeNode* root = buildTree({1, 2, 3, 4, 5, 6, 7});

        std::vector<int> preorder = preorderMorris(root);
        assert(preorder == std::vector<int>({1, 2, 4, 5, 3, 6, 7}));

        std::vector<int> inorder = inorderMorris(root);
        assert(inorder == std::vector<int>({4, 2, 5, 1, 6, 3, 7}));

        std::vector<int> postorder = postorderMorris(root);
        assert(postorder == std::vector<int>({4, 5, 2, 6, 7, 3, 1}));

        freeTree(root);
    }

    // ========================================================================
    // 测试5：单节点树
    // ========================================================================
    {
        TreeNode* root = buildTree({42});

        std::vector<int> preorder = preorderMorris(root);
        assert(preorder == std::vector<int>({42}));

        std::vector<int> inorder = inorderMorris(root);
        assert(inorder == std::vector<int>({42}));

        std::vector<int> postorder = postorderMorris(root);
        assert(postorder == std::vector<int>({42}));

        freeTree(root);
    }

    // ========================================================================
    // 测试6：空树
    // ========================================================================
    {
        TreeNode* root = buildTree({});

        std::vector<int> preorder = preorderMorris(root);
        assert(preorder.empty());

        std::vector<int> inorder = inorderMorris(root);
        assert(inorder.empty());

        std::vector<int> postorder = postorderMorris(root);
        assert(postorder.empty());

        freeTree(root);  // 对 nullptr 调用 freeTree 是安全的
    }

    // ========================================================================
    // 测试7：之字形树
    // ========================================================================
    //     1
    //      \
    //       2
    //      /
    //     3
    //      \
    //       4
    {
        TreeNode* root = new TreeNode(1);
        root->right = new TreeNode(2);
        root->right->left = new TreeNode(3);
        root->right->left->right = new TreeNode(4);

        std::vector<int> preorder = preorderMorris(root);
        assert(preorder == std::vector<int>({1, 2, 3, 4}));

        std::vector<int> inorder = inorderMorris(root);
        assert(inorder == std::vector<int>({1, 3, 4, 2}));

        std::vector<int> postorder = postorderMorris(root);
        assert(postorder == std::vector<int>({4, 3, 2, 1}));

        freeTree(root);
    }
}

int main() {
#ifdef _WIN32
    // 解决 Windows 控制台输出中文乱码的问题
    SetConsoleOutputCP(65001);
#endif

    // 运行硬币问题测试
    testCoinsMin();
    std::cout << "All CoinsMin tests passed" << std::endl;

    // 运行 Morris 遍历测试
    testMorris();
    std::cout << "All Morris traversal tests passed" << std::endl;
    return 0;
}
