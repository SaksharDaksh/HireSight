@echo off
echo Compiling FastMatcher C++ Engine...
g++ -O3 -std=c++17 fast_matcher.cpp -o fast_matcher.exe
if %ERRORLEVEL% EQU 0 (
    echo Compilation Successful: fast_matcher.exe generated.
    fast_matcher.exe --benchmark
) else (
    echo Compilation Failed.
)
