#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <unordered_set>
#include <unordered_map>
#include <algorithm>
#include <cmath>
#include <cctype>
#include <fstream>

// Clean and lowercase a token
std::string cleanToken(const std::string& token) {
    std::string clean;
    for (char c : token) {
        if (std::isalnum(static_cast<unsigned char>(c)) || c == '+' || c == '#' || c == '.') {
            clean += std::tolower(static_cast<unsigned char>(c));
        }
    }
    return clean;
}

// Fast whitespace and delimiter tokenization
std::vector<std::string> tokenize(const std::string& text) {
    std::vector<std::string> tokens;
    std::string cur;
    for (char c : text) {
        if (std::isalnum(static_cast<unsigned char>(c)) || c == '+' || c == '#' || c == '.') {
            cur += std::tolower(static_cast<unsigned char>(c));
        } else {
            if (!cur.empty()) {
                tokens.push_back(cur);
                cur.clear();
            }
        }
    }
    if (!cur.empty()) {
        tokens.push_back(cur);
    }
    return tokens;
}

// Compute Jaccard Similarity between two token sets
double computeJaccard(const std::vector<std::string>& a, const std::vector<std::string>& b) {
    std::unordered_set<std::string> setA(a.begin(), a.end());
    std::unordered_set<std::string> setB(b.begin(), b.end());

    if (setA.empty() || setB.empty()) return 0.0;

    int intersectionCount = 0;
    for (const auto& item : setA) {
        if (setB.find(item) != setB.end()) {
            intersectionCount++;
        }
    }

    int unionCount = static_cast<int>(setA.size() + setB.size()) - intersectionCount;
    if (unionCount <= 0) return 0.0;
    return static_cast<double>(intersectionCount) / static_cast<double>(unionCount);
}

// Compute Cosine Similarity between term frequency vectors
double computeTFCosine(const std::vector<std::string>& a, const std::vector<std::string>& b) {
    std::unordered_map<std::string, double> tfA;
    std::unordered_map<std::string, double> tfB;

    for (const auto& t : a) tfA[t] += 1.0;
    for (const auto& t : b) tfB[t] += 1.0;

    double dot = 0.0;
    double normA = 0.0;
    double normB = 0.0;

    for (const auto& pair : tfA) {
        normA += pair.second * pair.second;
        auto it = tfB.find(pair.first);
        if (it != tfB.end()) {
            dot += pair.second * it->second;
        }
    }
    for (const auto& pair : tfB) {
        normB += pair.second * pair.second;
    }

    if (normA <= 0.0 || normB <= 0.0) return 0.0;
    return dot / (std::sqrt(normA) * std::sqrt(normB));
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cout << "{\"error\": \"Missing arguments. Usage: fast_matcher --jaccard textA textB | --cosine textA textB | --benchmark\"}\n";
        return 1;
    }

    std::string mode = argv[1];

    if (mode == "--jaccard" && argc >= 4) {
        std::string textA = argv[2];
        std::string textB = argv[3];
        auto tokA = tokenize(textA);
        auto tokB = tokenize(textB);
        double jaccard = computeJaccard(tokA, tokB);
        std::cout << "{\"mode\": \"jaccard\", \"score\": " << jaccard << "}\n";
        return 0;
    } else if (mode == "--cosine" && argc >= 4) {
        std::string textA = argv[2];
        std::string textB = argv[3];
        auto tokA = tokenize(textA);
        auto tokB = tokenize(textB);
        double cosine = computeTFCosine(tokA, tokB);
        std::cout << "{\"mode\": \"cosine\", \"score\": " << cosine << "}\n";
        return 0;
    } else if (mode == "--hybrid" && argc >= 4) {
        std::string textA = argv[2];
        std::string textB = argv[3];
        auto tokA = tokenize(textA);
        auto tokB = tokenize(textB);
        double jaccard = computeJaccard(tokA, tokB);
        double cosine = computeTFCosine(tokA, tokB);
        double hybrid = 0.6 * cosine + 0.4 * jaccard;
        std::cout << "{\"mode\": \"hybrid\", \"cosine\": " << cosine 
                  << ", \"jaccard\": " << jaccard 
                  << ", \"hybrid_score\": " << hybrid << "}\n";
        return 0;
    } else if (mode == "--benchmark") {
        std::string s1 = "Python machine learning deep learning scikit-learn pytorch sql docker aws kubernetes fast-api";
        std::string s2 = "Senior Python ML Engineer required. Strong experience in scikit-learn, pytorch, sql, aws, and docker.";
        auto t1 = tokenize(s1);
        auto t2 = tokenize(s2);
        double c = computeTFCosine(t1, t2);
        double j = computeJaccard(t1, t2);
        std::cout << "{\"status\": \"ok\", \"engine\": \"C++17 FastMatcher\", \"cosine\": " << c << ", \"jaccard\": " << j << "}\n";
        return 0;
    }

    std::cout << "{\"error\": \"Unrecognized mode or insufficient arguments\"}\n";
    return 1;
}
