#pragma once

#include <string>
#include <unordered_map>

/*
 * Trie 前缀树（子节点使用 unordered_map 存储，支持任意 char）
 * - insert(word): 将单词计数 +1；可重复插入同一单词
 * - erase(word): 将单词计数 -1；当某分支计数归零时整支释放
 * - search(word): 返回某单词被插入过的次数
 * - prefixNumber(pre): 以 pre 为前缀的单词数量
 * 复杂度：令 L 为字符串长度，上述四操作均为 O(L)（哈希均摊）。
 * 内存：析构时递归释放全部节点；erase 过程中按需回收。
 */
class Trie {
private:
    struct TrieNode {
        int pass;                                   // 经过当前节点的字符串个数
        int end;                                    // 以当前节点为结尾的字符串个数
        std::unordered_map<char, TrieNode*> nexts;  // 邻接：字符 -> 子节点
        TrieNode() : pass(0), end(0) {}
    };

    TrieNode* root;

    // 递归释放子树（erase 或析构时使用）
    static void freeSubtree(TrieNode* node) {
        if (!node) return;
        for (auto& kv : node->nexts) {
            freeSubtree(kv.second);
        }
        delete node;
    }

public:
    Trie() : root(new TrieNode()) {}

    ~Trie() { freeSubtree(root); root = nullptr; }

    // 插入单词一次；支持任意字符
    void insert(const std::string& word) {
        TrieNode* node = root;
        node->pass++;
        for (char ch : word) {
            TrieNode*& child = node->nexts[ch];
            if (!child) child = new TrieNode();
            node = child;
            node->pass++;
        }
        node->end++;
    }

    // 删除一次已存在的单词；若不存在则无操作
    void erase(const std::string& word) {
        if (search(word) == 0) return;
        TrieNode* node = root;
        node->pass--;
        for (char ch : word) {
            auto it = node->nexts.find(ch);
            if (it == node->nexts.end()) return; // 理论上不会发生
            TrieNode* child = it->second;
            if (--child->pass == 0) {
                freeSubtree(child);
                node->nexts.erase(it);
                return;
            }
            node = child;
        }
        node->end--;
    }

    // 返回 word 被插入过的次数
    int search(const std::string& word) const {
        const TrieNode* node = root;
        for (char ch : word) {
            auto it = node->nexts.find(ch);
            if (it == node->nexts.end()) return 0;
            node = it->second;
        }
        return node->end;
    }

    // 统计以 pre 为前缀的单词数量
    int prefixNumber(const std::string& pre) const {
        const TrieNode* node = root;
        for (char ch : pre) {
            auto it = node->nexts.find(ch);
            if (it == node->nexts.end()) return 0;
            node = it->second;
        }
        return node->pass;
    }
};

