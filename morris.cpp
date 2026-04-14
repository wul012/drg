#include "morris.h"
#include <algorithm>
#include <queue>

namespace morris {

    // ========================================================================
    // Morris 遍历基础版本 —— 详细注释
    // ========================================================================
    //
    // 【算法流程图示】
    //
    //   假设有如下二叉树：
    //
    //           1
    //          / \
    //         2   3
    //        / \
    //       4   5
    //
    //   Morris 遍历过程：
    //
    //   Step 1: cur = 1，有左子树
    //           找到左子树最右节点 = 5
    //           5->right = null，所以 5->right = 1，cur = 2
    //
    //   Step 2: cur = 2，有左子树
    //           找到左子树最右节点 = 4
    //           4->right = null，所以 4->right = 2，cur = 4
    //
    //   Step 3: cur = 4，无左子树
    //           直接 cur = cur->right = 2（之前建立的链接）
    //
    //   Step 4: cur = 2，有左子树
    //           找到左子树最右节点 = 4
    //           4->right = 2（第二次到达），恢复 4->right = null，cur = 5
    //
    //   Step 5: cur = 5，无左子树
    //           直接 cur = cur->right = 1（之前建立的链接）
    //
    //   Step 6: cur = 1，有左子树
    //           找到左子树最右节点 = 5
    //           5->right = 1（第二次到达），恢复 5->right = null，cur = 3
    //
    //   Step 7: cur = 3，无左子树
    //           直接 cur = cur->right = null
    //
    //   Step 8: cur = null，遍历结束
    //
    //   访问顺序：1 -> 2 -> 4 -> 2 -> 5 -> 1 -> 3
    //   （有左子树的节点 1 和 2 各被访问 2 次）
    //
    // ========================================================================
    void morris(TreeNode* head, std::function<void(TreeNode*, bool)> visit) {
        // 边界情况：空树
        if (head == nullptr) {
            return;
        }

        TreeNode* cur = head;       // 当前遍历的节点
        TreeNode* mostRight = nullptr;  // 左子树的最右节点

        while (cur != nullptr) {
            mostRight = cur->left;  // mostRight 先指向 cur 的左孩子

            if (mostRight != nullptr) {
                // ============================================================
                // 情况：cur 有左子树
                // ============================================================
                // 找到左子树的最右节点
                // 注意循环条件：mostRight->right != cur 是为了避免死循环
                // （因为我们可能已经把 mostRight->right 指向了 cur）
                // ============================================================
                while (mostRight->right != nullptr && mostRight->right != cur) {
                    mostRight = mostRight->right;
                }

                // 现在 mostRight 指向左子树的最右节点
                if (mostRight->right == nullptr) {
                    // ========================================================
                    // 第一次到达 cur
                    // ========================================================
                    // mostRight->right 是 null，说明是第一次来到 cur
                    // 建立返回路径：让 mostRight->right 指向 cur
                    // 然后 cur 向左移动
                    // ========================================================
                    visit(cur, true);  // 第一次访问
                    mostRight->right = cur;
                    cur = cur->left;
                    continue;  // 重要：直接进入下一轮循环
                } else {
                    // ========================================================
                    // 第二次到达 cur（mostRight->right == cur）
                    // ========================================================
                    // 说明左子树已经遍历完了，现在要恢复树结构
                    // 然后 cur 向右移动
                    // ========================================================
                    visit(cur, false);  // 第二次访问
                    mostRight->right = nullptr;  // 恢复树结构
                }
            } else {
                // ============================================================
                // 情况：cur 没有左子树
                // ============================================================
                // 这种节点只会被访问一次
                // ============================================================
                visit(cur, true);  // 只访问一次，算作第一次
            }

            // cur 向右移动
            cur = cur->right;
        }
    }

    // ========================================================================
    // 前序遍历（Morris 实现）
    // ========================================================================
    // 【前序遍历顺序】根 -> 左 -> 右
    //
    // 【策略】
    //   - 对于有左子树的节点：第一次到达时处理
    //   - 对于无左子树的节点：直接处理
    //   
    //   也就是说：只在第一次访问时处理节点
    //
    // 【示例】
    //           1
    //          / \
    //         2   3
    //        / \
    //       4   5
    //
    //   Morris 访问顺序：1(1st) -> 2(1st) -> 4 -> 2(2nd) -> 5 -> 1(2nd) -> 3
    //   前序输出：       1         2         4              5              3
    //   结果：[1, 2, 4, 5, 3] ✓
    // ========================================================================
    std::vector<int> preorderMorris(TreeNode* head) {
        std::vector<int> result;

        if (head == nullptr) {
            return result;
        }

        TreeNode* cur = head;
        TreeNode* mostRight = nullptr;

        while (cur != nullptr) {
            mostRight = cur->left;

            if (mostRight != nullptr) {
                // 有左子树，找最右节点
                while (mostRight->right != nullptr && mostRight->right != cur) {
                    mostRight = mostRight->right;
                }

                if (mostRight->right == nullptr) {
                    // ★ 第一次到达：处理当前节点 ★
                    result.push_back(cur->val);
                    mostRight->right = cur;
                    cur = cur->left;
                    continue;
                } else {
                    // 第二次到达：不处理，只恢复
                    mostRight->right = nullptr;
                }
            } else {
                // ★ 无左子树：处理当前节点 ★
                result.push_back(cur->val);
            }

            cur = cur->right;
        }

        return result;
    }

    // ========================================================================
    // 中序遍历（Morris 实现）
    // ========================================================================
    // 【中序遍历顺序】左 -> 根 -> 右
    //
    // 【策略】
    //   - 对于有左子树的节点：第二次到达时处理（左子树已遍历完）
    //   - 对于无左子树的节点：直接处理
    //
    //   也就是说：在向右移动之前处理节点
    //
    // 【示例】
    //           1
    //          / \
    //         2   3
    //        / \
    //       4   5
    //
    //   Morris 访问顺序：1(1st) -> 2(1st) -> 4 -> 2(2nd) -> 5 -> 1(2nd) -> 3
    //   中序输出：                            4     2        5     1       3
    //   结果：[4, 2, 5, 1, 3] ✓
    // ========================================================================
    std::vector<int> inorderMorris(TreeNode* head) {
        std::vector<int> result;

        if (head == nullptr) {
            return result;
        }

        TreeNode* cur = head;
        TreeNode* mostRight = nullptr;

        while (cur != nullptr) {
            mostRight = cur->left;

            if (mostRight != nullptr) {
                // 有左子树，找最右节点
                while (mostRight->right != nullptr && mostRight->right != cur) {
                    mostRight = mostRight->right;
                }

                if (mostRight->right == nullptr) {
                    // 第一次到达：不处理，只建立链接
                    mostRight->right = cur;
                    cur = cur->left;
                    continue;
                } else {
                    // 第二次到达：恢复树结构
                    mostRight->right = nullptr;
                }
            }

            // ★ 关键：在向右移动之前处理节点 ★
            // 这里处理两种情况：
            // 1. 无左子树的节点
            // 2. 有左子树但第二次到达的节点（左子树已遍历完）
            result.push_back(cur->val);
            cur = cur->right;
        }

        return result;
    }

    // ========================================================================
    // 辅助函数：逆序处理右边界
    // ========================================================================
    // 后序遍历需要用到这个函数
    // 将从 from 开始沿着 right 指针形成的链表逆序，处理后再恢复
    //
    // 例如：a -> b -> c -> null
    // 逆序后：c -> b -> a -> null
    // 处理顺序：c, b, a
    // 恢复后：a -> b -> c -> null
    // ========================================================================
    static void printRightEdge(TreeNode* from, std::vector<int>& result) {
        // 第一步：反转右边界链表
        TreeNode* prev = nullptr;
        TreeNode* curr = from;
        TreeNode* next = nullptr;

        while (curr != nullptr) {
            next = curr->right;
            curr->right = prev;
            prev = curr;
            curr = next;
        }

        // 第二步：逆序收集节点值（此时 prev 指向原来的最右节点）
        TreeNode* tail = prev;
        while (tail != nullptr) {
            result.push_back(tail->val);
            tail = tail->right;
        }

        // 第三步：恢复右边界链表
        prev = nullptr;
        curr = prev;
        // 需要再次反转，从当前的 prev（原来的最右节点）开始
        curr = from;
        // 重新定位到反转后的链表头
        curr = nullptr;
        TreeNode* reversedHead = nullptr;
        
        // 重新找到反转后的头（即原来的最右节点）
        curr = from;
        prev = nullptr;
        // 第一次反转已经改变了结构，需要找到新的头
        // 实际上我们需要再做一次反转来恢复
        
        // 简化实现：再次从反转后的头开始反转
        curr = nullptr;
        next = nullptr;
        
        // 重新实现：找到反转后的链表头（存在 prev 变量中的最后值）
        // 更简洁的实现方式
    }

    // 更清晰的实现：先收集到临时数组，再逆序添加
    static void addRightEdgeReversed(TreeNode* from, std::vector<int>& result) {
        std::vector<int> temp;
        TreeNode* curr = from;
        while (curr != nullptr) {
            temp.push_back(curr->val);
            curr = curr->right;
        }
        // 逆序添加
        for (int i = static_cast<int>(temp.size()) - 1; i >= 0; --i) {
            result.push_back(temp[i]);
        }
    }

    // 真正的 O(1) 空间实现：反转 -> 收集 -> 恢复
    static void collectRightEdgeReversed(TreeNode* from, std::vector<int>& result) {
        // 反转右边界
        TreeNode* prev = nullptr;
        TreeNode* curr = from;
        while (curr != nullptr) {
            TreeNode* next = curr->right;
            curr->right = prev;
            prev = curr;
            curr = next;
        }
        // prev 现在是反转后的头（原来的尾）

        // 收集值
        curr = prev;
        while (curr != nullptr) {
            result.push_back(curr->val);
            curr = curr->right;
        }

        // 再次反转以恢复原结构
        curr = prev;
        prev = nullptr;
        while (curr != nullptr) {
            TreeNode* next = curr->right;
            curr->right = prev;
            prev = curr;
            curr = next;
        }
        // 现在链表恢复了原来的顺序
    }

    // ========================================================================
    // 后序遍历（Morris 实现）
    // ========================================================================
    // 【后序遍历顺序】左 -> 右 -> 根
    //
    // 【策略】这是最复杂的情况
    //   后序遍历的关键观察：
    //   当我们第二次到达某个节点 X 时，X 的左子树已经遍历完了。
    //   此时，逆序打印 X 左子树的右边界，就能得到该子树的后序遍历结果。
    //
    //   最后，还需要逆序打印整棵树的右边界。
    //
    // 【示例】
    //           1
    //          / \
    //         2   3
    //        / \
    //       4   5
    //
    //   第二次到达 2 时：逆序打印 2 左子树的右边界 = 逆序打印 [4] = [4]
    //   第二次到达 1 时：逆序打印 1 左子树的右边界 = 逆序打印 [2, 5] = [5, 2]
    //   最后：逆序打印整棵树的右边界 = 逆序打印 [1, 3] = [3, 1]
    //   
    //   结果：[4, 5, 2, 3, 1] ✓
    // ========================================================================
    std::vector<int> postorderMorris(TreeNode* head) {
        std::vector<int> result;

        if (head == nullptr) {
            return result;
        }

        TreeNode* cur = head;
        TreeNode* mostRight = nullptr;

        while (cur != nullptr) {
            mostRight = cur->left;

            if (mostRight != nullptr) {
                // 有左子树，找最右节点
                while (mostRight->right != nullptr && mostRight->right != cur) {
                    mostRight = mostRight->right;
                }

                if (mostRight->right == nullptr) {
                    // 第一次到达
                    mostRight->right = cur;
                    cur = cur->left;
                    continue;
                } else {
                    // ★ 第二次到达：逆序处理左子树的右边界 ★
                    mostRight->right = nullptr;
                    collectRightEdgeReversed(cur->left, result);
                }
            }

            cur = cur->right;
        }

        // ★ 最后：逆序处理整棵树的右边界 ★
        collectRightEdgeReversed(head, result);

        return result;
    }

    // ========================================================================
    // 从数组构建二叉树（层序遍历格式）
    // ========================================================================
    // -1 表示空节点
    // 例如：[1, 2, 3, -1, 4] 构建的树：
    //       1
    //      / \
    //     2   3
    //      \
    //       4
    // ========================================================================
    TreeNode* buildTree(const std::vector<int>& arr) {
        if (arr.empty() || arr[0] == -1) {
            return nullptr;
        }

        TreeNode* root = new TreeNode(arr[0]);
        std::queue<TreeNode*> q;
        q.push(root);

        size_t i = 1;
        while (!q.empty() && i < arr.size()) {
            TreeNode* node = q.front();
            q.pop();

            // 处理左子节点
            if (i < arr.size()) {
                if (arr[i] != -1) {
                    node->left = new TreeNode(arr[i]);
                    q.push(node->left);
                }
                ++i;
            }

            // 处理右子节点
            if (i < arr.size()) {
                if (arr[i] != -1) {
                    node->right = new TreeNode(arr[i]);
                    q.push(node->right);
                }
                ++i;
            }
        }

        return root;
    }

    // ========================================================================
    // 释放二叉树内存
    // ========================================================================
    void freeTree(TreeNode* root) {
        if (root == nullptr) {
            return;
        }
        freeTree(root->left);
        freeTree(root->right);
        delete root;
    }

}
