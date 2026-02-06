import subprocess
import sys

examples = [
    "examples/example1_basic.py",
    "examples/example2_deep.py", 
    "examples/example3_extract.py",
]

print("=" * 60)
print(" Running ALL Examples")
print("=" * 60)

for i, example in enumerate(examples, 1):
    print(f"\n{'='*60}")
    print(f" Example {i}: {example}")
    print("=" * 60)
    
    result = subprocess.run([sys.executable, example])
    
    if result.returncode != 0:
        print(f" Example {i} failed!")
    else:
        print(f" Example {i} done!")

print("\n" + "=" * 60)
print(" ALL EXAMPLES COMPLETED!")
print(" Check output/ folder for results:")
print("   - basic_crawl.json")
print("   - deep_crawl.json")
print("   - extracted_data.json")
print("=" * 60)
