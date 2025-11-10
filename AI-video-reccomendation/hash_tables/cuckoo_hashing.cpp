#include <iostream>
#include <vector>
#include <random>
#include <chrono>
#include <unordered_set>
#include <iomanip>
#include <cmath>
#include <fstream>
#include <string>

int a1, b1, a2, b2;
long long p = 1000000007LL;
int m = 25000;
const int EMB_DIM = 512;
std::vector<std::pair<int, std::vector<float> > > table1;
std::vector<std::pair<int, std::vector<float> > > table2;
int total_evictions = 0;
const std::string TABLE_FILE = "cuckoo_table.bin";

// Simple next_prime stub
int next_prime(int n) {
    if (n < 2) return 2;
    if (n % 2 == 0) n++;
    for (; n < INT_MAX; n += 2) {
        bool prime = true;
        for (int i = 3; i * i <= n; i += 2) {
            if (n % i == 0) { prime = false; break; }
        }
        if (prime) return n;
    }
    return n;
}

void initialize_tables() {
    m = next_prime(m);
    table1.assign(m, std::make_pair(-1, std::vector<float>()));
    table2.assign(m, std::make_pair(-1, std::vector<float>()));
    std::cout << "Initialized tables with size " << m << std::endl;
}

void initializeHashFunctions() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dist(1, static_cast<int>(p - 1));

    a1 = dist(gen);
    b1 = dist(gen);
    a2 = dist(gen);
    b2 = dist(gen);
}

void save_table() {
    std::ofstream out(TABLE_FILE, std::ios::binary);
    if (!out) return;

    // Save hash function parameters
    out.write(reinterpret_cast<const char*>(&a1), sizeof(a1));
    out.write(reinterpret_cast<const char*>(&b1), sizeof(b1));
    out.write(reinterpret_cast<const char*>(&a2), sizeof(a2));
    out.write(reinterpret_cast<const char*>(&b2), sizeof(b2));
    out.write(reinterpret_cast<const char*>(&m), sizeof(m));

    // Save table sizes
    size_t size1 = table1.size();
    size_t size2 = table2.size();
    out.write(reinterpret_cast<const char*>(&size1), sizeof(size1));
    out.write(reinterpret_cast<const char*>(&size2), sizeof(size2));

    // Save table1
    for (const auto& pair : table1) {
        out.write(reinterpret_cast<const char*>(&pair.first), sizeof(pair.first));
        out.write(reinterpret_cast<const char*>(pair.second.data()), pair.second.size() * sizeof(float));
    }

    // Save table2
    for (const auto& pair : table2) {
        out.write(reinterpret_cast<const char*>(&pair.first), sizeof(pair.first));
        out.write(reinterpret_cast<const char*>(pair.second.data()), pair.second.size() * sizeof(float));
    }

    out.close();
}

void load_table() {
    std::ifstream in(TABLE_FILE, std::ios::binary);
    if (!in) return;

    // Load hash function parameters
    in.read(reinterpret_cast<char*>(&a1), sizeof(a1));
    in.read(reinterpret_cast<char*>(&b1), sizeof(b1));
    in.read(reinterpret_cast<char*>(&a2), sizeof(a2));
    in.read(reinterpret_cast<char*>(&b2), sizeof(b2));
    in.read(reinterpret_cast<char*>(&m), sizeof(m));

    // Load table sizes
    size_t size1, size2;
    in.read(reinterpret_cast<char*>(&size1), sizeof(size1));
    in.read(reinterpret_cast<char*>(&size2), sizeof(size2));

    // Initialize tables
    table1.assign(size1, std::make_pair(-1, std::vector<float>()));
    table2.assign(size2, std::make_pair(-1, std::vector<float>()));

    // Load table1
    for (auto& pair : table1) {
        in.read(reinterpret_cast<char*>(&pair.first), sizeof(pair.first));
        if (pair.first != -1) {
            pair.second.resize(EMB_DIM);
            in.read(reinterpret_cast<char*>(pair.second.data()), EMB_DIM * sizeof(float));
        }
    }

    // Load table2
    for (auto& pair : table2) {
        in.read(reinterpret_cast<char*>(&pair.first), sizeof(pair.first));
        if (pair.first != -1) {
            pair.second.resize(EMB_DIM);
            in.read(reinterpret_cast<char*>(pair.second.data()), EMB_DIM * sizeof(float));
        }
    }

    in.close();
}

int hash1(int key) {
    return ((static_cast<long long>(a1) * key + b1) % p) % m;
}

int hash2(int key) {
    return ((static_cast<long long>(a2) * key + b2) % p) % m;
}

std::vector<float> lookup(int key);

bool insert(int key, std::vector<float> embedding) {
    // Dupe check: Skip if exists (prevents self-cycle)
    if (!lookup(key).empty()) {
        return true;
    }
    
    int eviction_count = 0;
    const int MAX_EVICTIONS = 500;
    bool try_table1 = true;
    std::unordered_set<int> path;

    while (eviction_count < MAX_EVICTIONS) {
        if (path.count(key)) {
            std::cout << "Cycle detected for key " << key << " after " << eviction_count << " evictions; triggering rehash" << std::endl;
            // Rehash
            int old_m = m;
            m *= 2;
            initialize_tables();
            // Reinsert all old entries
            for (auto& pair : table1) {
                if (pair.first != -1) insert(pair.first, pair.second);
            }
            for (auto& pair : table2) {
                if (pair.first != -1) insert(pair.first, pair.second);
            }
            std::cout << "Rehashed from " << old_m << " to " << m << " slots" << std::endl;
            path.clear();
            eviction_count = 0;  // Retry
            continue;
        }
        path.insert(key);

        if (try_table1) {
            int pos = hash1(key);
            if (table1[pos].first == -1) {
                table1[pos] = std::make_pair(key, embedding);
                return true;
            } else {
                int old_key = table1[pos].first;
                std::vector<float> old_emb = table1[pos].second;
                table1[pos] = std::make_pair(key, embedding);
                key = old_key;
                embedding = old_emb;
                try_table1 = false;
                total_evictions++;
            }
        } else {
            int pos = hash2(key);
            if (table2[pos].first == -1) {
                table2[pos] = std::make_pair(key, embedding);
                return true;
            } else {
                int old_key = table2[pos].first;
                std::vector<float> old_emb = table2[pos].second;
                table2[pos] = std::make_pair(key, embedding);
                key = old_key;
                embedding = old_emb;
                try_table1 = true;
                total_evictions++;
            }
        }
        eviction_count++;
    }
    std::cout << "Max evictions hit for key " << key << "; triggering rehash" << std::endl;
    // Same rehash as above
    int old_m = m;
    m *= 2;
    initialize_tables();
    for (auto& pair : table1) {
        if (pair.first != -1) insert(pair.first, pair.second);
    }
    for (auto& pair : table2) {
        if (pair.first != -1) insert(pair.first, pair.second);
    }
    std::cout << "Rehashed from " << old_m << " to " << m << " slots" << std::endl;
    // Retry
    return insert(key, embedding);
}

std::vector<float> lookup(int key) {
    int pos1 = hash1(key);
    if (table1[pos1].first == key) {
        return table1[pos1].second;
    }
    int pos2 = hash2(key);
    if (table2[pos2].first == key) {
        return table2[pos2].second;
    }
    return std::vector<float>();
}

bool remove_key(int key) {
    int pos1 = hash1(key);
    if (table1[pos1].first == key) {
        table1[pos1] = std::make_pair(-1, std::vector<float>());
        return true;
    }
    int pos2 = hash2(key);
    if (table2[pos2].first == key) {
        table2[pos2] = std::make_pair(-1, std::vector<float>());
        return true;
    }
    return false;
}

std::vector<float> load_embedding(const std::string& filepath) {
    std::ifstream file(filepath, std::ios::binary);
    if (!file) {
        std::cerr << "Failed to open file: " << filepath << std::endl;
        return std::vector<float>(EMB_DIM, 0.0f);
    }
    std::vector<float> emb(EMB_DIM);
    file.read(reinterpret_cast<char*>(emb.data()), EMB_DIM * sizeof(float));
    file.close();
    return emb;
}

int main(int argc, char* argv[]) {
    // Try to load existing table, otherwise initialize new one
    load_table();
    if (table1.empty() || table2.empty()) {
        initialize_tables();
        initializeHashFunctions();
    }

    if (argc > 3) {
        std::string cmd = argv[1];
        if (cmd == "insert") {
            int key = std::stoi(argv[2]);
            auto emb = load_embedding(argv[3]);
            bool success = insert(key, emb);
            std::cout << "CLI Insert key " << key << ": " << (success ? "Success" : "Failed") << std::endl;
            if (success) save_table();
            return 0;
        } else if (cmd == "lookup") {
            int key = std::stoi(argv[2]);
            std::string out_file = argv[3];
            auto retrieved = lookup(key);
            if (!retrieved.empty()) {
                std::ofstream out(out_file, std::ios::binary);
                if (out.is_open()) {
                    out.write(reinterpret_cast<const char*>(retrieved.data()), retrieved.size() * sizeof(float));
                    out.close();
                    std::cout << "CLI Lookup key " << key << ": Written to " << out_file << " (size: " << retrieved.size() << ")" << std::endl;
                } else {
                    std::cerr << "CLI Lookup key " << key << ": Failed to open " << out_file << " for writing" << std::endl;
                }
            } else {
                std::cerr << "CLI Lookup key " << key << ": Not found (empty retrieved)" << std::endl;
            }
            return 0;
        }
    }
    
    // Fallback: Run original tests if no args
    // Test 1: Insert sample embedding
    int key = 1234567890;
    std::vector<float> emb = load_embedding("sample_emb.bin");
    if (insert(key, emb)) {
        std::cout << "Insert success for key " << key << ". Size: " << emb.size() << std::endl;
    } else {
        std::cout << "Insert failed for key " << key << std::endl;
    }

    // Test 2: Lookup
    auto retrieved_emb = lookup(key);
    if (!retrieved_emb.empty()) {
        bool match = true;
        for (size_t i = 0; i < emb.size(); ++i) {
            if (std::abs(emb[i] - retrieved_emb[i]) > 1e-6) {
                match = false;
                break;
            }
        }
        std::cout << "Lookup success. Match: " << (match ? "Yes" : "No") << std::endl;
    } else {
        std::cout << "Lookup failed. Retrieved size: " << retrieved_emb.size() << std::endl;
    }

    // Test 3: Dupe insert
    if (insert(key, emb)) {
        std::cout << "Dupe insert succeeded (skipped)" << std::endl;
    } else {
        std::cout << "Dupe insert failed (unexpected)" << std::endl;
    }

    // Test 4: High-load
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 1.0f);
    int success_count = 0;
    for (int i = 1; i <= 10; ++i) {
        int new_key = 1234567890 + i;
        std::vector<float> new_emb(EMB_DIM);
        for (auto& e : new_emb) e = dist(gen);
        if (insert(new_key, new_emb)) success_count++;
    }
    std::cout << "High-load: " << success_count << "/10 success. Total evictions: " << total_evictions << std::endl;

    return 0;
}