# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Build and run

This is a single-target C++20 project built with CMake. The only CMake target is an executable named `C` defined in `CMakeLists.txt`.

Typical workflow (Debug build):

- Configure (only needed when CMake configuration changes or the build directory is missing):
  - `cmake -S . -B cmake-build-debug -DCMAKE_BUILD_TYPE=Debug`
- Build the default target:
  - `cmake --build cmake-build-debug`
- Run the resulting executable (Windows):
  - `./cmake-build-debug/C.exe`

If you need a separate Release build, create and use another build directory, for example:

- Configure Release:
  - `cmake -S . -B cmake-build-release -DCMAKE_BUILD_TYPE=Release`
- Build Release:
  - `cmake --build cmake-build-release`

## Testing

There is no dedicated test framework; tests are ordinary C++ programs using `assert`.

- Dijkstra/graph tests live in `test.cpp` and currently provide the `main` entrypoint compiled into `C.exe`.
  - Running `./cmake-build-debug/C.exe` executes three test functions that construct graphs via `createGraph`, run `dijkstra`, and validate distances with `assert`.
  - On success, the program prints `All Dijkstra tests passed` and exits with code 0; any failing `assert` aborts the program.
- There is no mechanism to run a single test function from the command line; to narrow down a failure or run only some tests, edit `main` in `test.cpp` to call only the desired helper(s).

The file `main.cpp` contains a separate driver that stress-tests the `selectionSort` and `quickSort` implementations against `std::sort`, but it is **not** part of the CMake target list by default. To use it as the entrypoint, you would need to update `CMakeLists.txt` (e.g., swap `test.cpp` for `main.cpp` in `add_executable`).

## Linting and static analysis

The repository does not include a configured linter (such as clang-tidy or cpplint) or formatting tooling. Static checking is currently limited to compiler warnings produced when building via CMake.

If you introduce a linter or formatter, prefer integrating it via CMake so it can be invoked consistently (for example, by adding custom targets like `clang-tidy` or `format`).

## Code architecture

### Build system

- `CMakeLists.txt` defines a single executable target `C` and sets `CMAKE_CXX_STANDARD 20`.
- The target is composed of a small set of algorithm modules (sorting, N-Queens, graph shortest path) and a single driver file (`test.cpp` by default) that provides `main`.

### Array / sorting algorithms

Sorting algorithms follow a common pattern:

- Each algorithm is implemented as a pair of `*.h`/`*.cpp` files in the global source directory and lives in its own namespace:
  - `selectionSort::{void sort(std::vector<int>&)}`
  - `quickSort::{void sort(std::vector<int>&)}`
  - `mergeSort::{void sort(std::vector<int>&)}`
- All APIs operate on `std::vector<int>&` in-place and assume no special invariants beyond basic validity (size ≥ 0).
- `main.cpp` (currently unused by the build) demonstrates the intended usage and testing pattern:
  - Random integer vectors are generated.
  - The custom sort implementation is run.
  - Results are compared against `std::sort` using helper functions like `comparator` and `areVectorsEqual`.

When adding new array/algorithm utilities, following this header/implementation split and namespace-based API makes it straightforward to plug them into the existing random-test harness in `main.cpp`.

### N-Queens solver

The N-Queens logic is encapsulated in `nQueens.h`/`nQueens.cpp` under the `nQueens` namespace:

- Public API:
  - `long long countNQueensSimple(int n)` – classic backtracking over rows, using a `std::vector<int>` to record queen positions.
  - `long long countNQueensBitmask(int n)` – optimized variant using 32-bit bitmasks to represent used columns and diagonals; supports `1 <= n <= 32`.
- Implementation details (kept in an anonymous namespace in `nQueens.cpp`):
  - `isValidPosition` validates row/column/diagonal constraints for the simple solver.
  - `processSimple` performs recursive placement of queens row by row.
  - `processBitmask` implements the bitmask-based recursion from typical N-Queens optimization examples.

All helpers are intentionally file-local; anything outside `nQueens.cpp` should depend only on the two public counting functions.

### Graph representation and Dijkstra

The directed weighted graph and Dijkstra shortest path implementation are split into `graph.h`/`graph.cpp` and `dijkstra.h`/`dijkstra.cpp`:

- `graph.h` / `graph.cpp` define the core graph model:
  - `struct Node` with fields `value`, `in`, `out`, `nexts`, and `edges`.
  - `struct Edge` linking `from` and `to` `Node*` with an integral `weight` (non-negative for Dijkstra).
  - `struct Graph` holding `nodes` (an `std::unordered_map<int, Node*>` keyed by node value) and `edges` (a flat `std::vector<Edge*>`).
  - A global constant `INF` (declared in `graph.h` and defined in `graph.cpp`) used as the sentinel for unreachable distances.
  - `Graph createGraph(const std::vector<std::array<int, 3>>& matrix)` constructs a graph from a list of `{from, to, weight}` triples, allocating `Node`/`Edge` objects and wiring degrees and adjacency.
- `dijkstra.h` / `dijkstra.cpp` implement a heap-optimized single-source Dijkstra:
  - Public API: `std::vector<int> dijkstra(const Graph& g, int src)`.
  - The returned vector is indexed by node `value` and initialized to `INF`; elements are updated with shortest distances as nodes are finalized.
  - Internally, `NodeHeap` wraps a binary min-heap over `Node*`, tracking heap indices and tentative distances with `std::unordered_map`s and providing `addOrUpdateOrIgnore` and `pop` operations analogous to a classic Java implementation.

The Dijkstra tests in `test.cpp` exercise this stack end-to-end by:

- Constructing graphs as `std::vector<std::array<int, 3>>` edge lists.
- Calling `createGraph` to obtain a `Graph`.
- Invoking `dijkstra` and asserting on the returned distance vector, including behavior for disconnected nodes (remaining at `INF`).

Any new graph algorithms should reuse the existing `Graph`/`Node`/`Edge` definitions to stay compatible with this model and allow combined usage in tests.

### Trie (prefix tree)

`trie.h` contains a self-contained, header-only `Trie` class:

- Each node tracks `pass` (number of strings passing through), `end` (strings ending at the node), and an `std::unordered_map<char, TrieNode*> nexts` map for children.
- Public operations:
  - `insert(const std::string&)`
  - `erase(const std::string&)` (no-op if the word was not present)
  - `search(const std::string&) const` – count of exact matches
  - `prefixNumber(const std::string&) const` – number of words with the given prefix
- Memory management is handled recursively via `freeSubtree` in the destructor and from `erase` when subtrees become unreachable.

The Trie is not currently wired into any executable; it is ready for direct inclusion in future drivers or tests.

## Conventions

A few project-specific conventions are visible in the current code:

- Standard library symbols are always qualified (`std::vector`, `std::sort`, `std::cout`) rather than using `using namespace std;` (see the detailed rationale in `main.cpp`).
- Algorithm modules expose minimal, focused functions in their own namespaces and rely on simple value types (`int`, `std::vector<int>`) for interfaces.
- Windows-specific console encoding adjustments (via `SetConsoleOutputCP(65001)`) are guarded with `#ifdef _WIN32` in entrypoint files that print Chinese comments or messages.
