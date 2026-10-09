# 🚀 Kaggle Training Guide - AURA GNN Model

## Why Use Kaggle?

✅ **FREE GPU Access** - T4 GPU with 16GB VRAM  
✅ **No Local Setup** - Train in the cloud  
✅ **Faster Training** - 5-10 minutes vs 30-60 minutes on CPU  
✅ **Pre-installed Libraries** - Most dependencies already available  

---

## 📋 Step-by-Step Instructions

### **1. Create a Kaggle Account**
- Go to [kaggle.com](https://www.kaggle.com)
- Sign up for free (if you don't have an account)

### **2. Upload Your Data**

**Option A: Direct Upload to Notebook**
1. Create new notebook at [kaggle.com/code](https://www.kaggle.com/code)
2. Click "Add Data" → "Upload"
3. Upload `nodes.csv` and `relationships.csv`

**Option B: Create a Dataset (Recommended)**
1. Go to [kaggle.com/datasets](https://www.kaggle.com/datasets)
2. Click "New Dataset"
3. Upload `nodes.csv` and `relationships.csv`
4. Make it public or private
5. Click "Create"
6. Now you can reuse this dataset in any notebook!

### **3. Upload the Notebook**
1. Download `train_gnn_kaggle.ipynb` from your project folder
2. Go to [kaggle.com/code](https://www.kaggle.com/code)
3. Click "New Notebook" → "Upload Notebook"
4. Select `train_gnn_kaggle.ipynb`

### **4. Enable GPU Acceleration** ⚡
This is CRITICAL for fast training!

1. On the right sidebar, click "Settings"
2. Under "Accelerator", select **GPU T4 x2**
3. Click "Save"

You should see a green checkmark and "GPU" indicator at the top.

### **5. Add Your Dataset to Notebook**
1. Click "Add Data" button (top right)
2. Search for your uploaded dataset
3. Click "Add" to attach it to the notebook

### **6. Run the Notebook**
You have two options:

**Option A: Run All Cells**
- Click "Run All" at the top
- Wait 10-15 minutes
- Model will train automatically

**Option B: Run Cell-by-Cell**
- Click on first cell
- Press `Shift + Enter` to run
- Review output
- Continue to next cell

### **7. Monitor Training**
Watch for:
- ✅ GPU detection message
- ✅ Data loading confirmation
- ✅ Training progress (epoch numbers)
- ✅ Best model checkpoints
- ✅ "Training Complete" message

Expected output:
```
Epoch    Train Loss   Val Loss     Val Acc      Status
--------------------------------------------------------------------------------
1        0.6234       0.5891       0.6234       
2        0.5123       0.4821       0.7145       ✓ Best!
...
35       0.1456       0.2123       0.8956       ✓ Best!

🎉 TRAINING COMPLETE!
Best Validation Accuracy: 0.8956 (Epoch 35)
Total Training Time: 8.34 minutes
```

### **8. Download the Trained Model**

**After training completes:**

1. Look at the **right sidebar** → "Output" section
2. You'll see `classifier.pth` file
3. Click the **download icon** next to it
4. Save to your local project folder

**File size:** Should be 5-20 MB depending on your graph size

### **9. Use the Model Locally**

Place `classifier.pth` in your project folder:
```
project/
├── app.py
├── nodes.csv
├── relationships.csv
├── classifier.pth  ← Downloaded from Kaggle
└── ...
```

Then run:
```bash
streamlit run app.py
```

---

## 🔧 Troubleshooting

### **Issue: "GPU not detected"**
**Solution:**
- Check Settings → Accelerator → GPU T4 x2
- Restart the notebook session
- Re-run the first cell

### **Issue: "Data files not found"**
**Solution:**
- Make sure you uploaded the CSV files
- Check the "Add Data" button shows your dataset
- Re-run the data loading cell
- Check file paths in the cell output

### **Issue: "Out of memory"**
**Solutions:**
1. Restart the notebook (clears memory)
2. Reduce batch size in embedding cell:
   ```python
   batch_size=16  # instead of 32
   ```
3. Use smaller model:
   ```python
   hidden_channels=128  # instead of 256
   ```

### **Issue: "Installation failed"**
**Solution:**
- Kaggle sometimes has library version conflicts
- Try alternative install:
  ```python
  !pip install --no-deps torch-geometric
  ```

### **Issue: "Training is very slow"**
**Check:**
- GPU is enabled (should see "Using device: cuda")
- If showing "cpu", GPU is not active
- Enable GPU in Settings and restart

### **Issue: "Validation accuracy is low (<75%)"**
**Solutions:**
1. Train for more epochs (increase `num_epochs = 100`)
2. Adjust learning rate (`lr=0.0005` instead of `0.001`)
3. Check if your data has enough Paper→Concept edges
4. Try different model architectures

---

## 💡 Pro Tips

### **Tip 1: Save Your Work**
Kaggle autosaves, but you can also:
- Click "Save Version" to create snapshots
- Download the notebook for backup

### **Tip 2: View Logs Later**
- All output is saved in the notebook
- You can review training progress anytime
- Download the notebook with outputs

### **Tip 3: Experiment**
Try different hyperparameters:
```python
# In the model initialization cell
gnn_model = GNN(hidden_channels=512, out_channels=256)  # Bigger model
optimizer = torch.optim.Adam(..., lr=0.0005)  # Lower learning rate
num_epochs = 100  # More training
```

### **Tip 4: Compare Results**
Create multiple versions:
- Version 1: Default settings
- Version 2: Larger model
- Version 3: More epochs
- Compare validation accuracies!

### **Tip 5: Share Your Work**
- Make notebook public
- Share link with collaborators
- Others can fork and experiment

---

## 📊 Expected Performance

With your data (7,623 nodes, 3,838 edges):

| Metric | Expected Value |
|--------|----------------|
| Training Time | 5-10 minutes (GPU) |
| Validation Accuracy | 85-90% |
| Model Size | 5-20 MB |
| GPU Memory Used | 2-4 GB |

---

## 🎯 Success Checklist

- [ ] Kaggle account created
- [ ] GPU enabled (T4 x2)
- [ ] Data files uploaded
- [ ] Notebook uploaded
- [ ] Dataset added to notebook
- [ ] GPU detected in first cell
- [ ] Data loaded successfully
- [ ] Training completed
- [ ] classifier.pth downloaded
- [ ] Model placed in project folder
- [ ] Streamlit app runs successfully

---

## 🆘 Need Help?

1. **Check notebook outputs** - Error messages are usually clear
2. **Re-run cells** - Sometimes a simple re-run fixes issues
3. **Restart kernel** - Clears memory and state
4. **Check Kaggle forums** - Very active community
5. **Review documentation** - Links in the notebook

---

## ⏱️ Timeline

| Step | Time |
|------|------|
| Setup Kaggle + Upload Data | 5 min |
| Upload Notebook | 2 min |
| Enable GPU | 1 min |
| Install Libraries | 2 min |
| Load Data | 1 min |
| Create Embeddings | 3-5 min |
| Build Graph | 1 min |
| Train Model | 5-10 min |
| Download Model | 1 min |
| **TOTAL** | **~20-30 min** |

---

## 🎓 What You'll Learn

By using this Kaggle notebook, you'll learn:
- ✅ How to use Kaggle's free GPU
- ✅ Graph Neural Network training
- ✅ PyTorch Geometric library
- ✅ Heterogeneous graph construction
- ✅ Link prediction tasks
- ✅ Model evaluation and optimization

---

**Ready to train? Upload the notebook to Kaggle and let's go! 🚀**
