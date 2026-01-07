import os
from huggingface_hub import snapshot_download

# Create directory
model_dir = "backend/app/ml/artifacts"
os.makedirs(model_dir, exist_ok=True)

# Download the model you mentioned
model_id = "kidkidmoon/xlm-r-khmer-news-classification"

print(f"Downloading model: {model_id}")
print(f"Saving to: {model_dir}")

try:
    # Download model files
    snapshot_download(
        repo_id=model_id,
        local_dir=model_dir,
        local_dir_use_symlinks=False,
        resume_download=True
    )
    print("✅ Model downloaded successfully!")
    
    # List downloaded files
    print("\n📁 Downloaded files:")
    for root, dirs, files in os.walk(model_dir):
        for file in files:
            path = os.path.join(root, file)
            size = os.path.getsize(path) / (1024*1024)  # MB
            print(f"  - {file} ({size:.2f} MB)")
            
except Exception as e:
    print(f"❌ Error: {e}")