# 🎓 AURA - Academic Research Assistant
## Complete User Guide v2.0 (Strict Scoring Edition)

---

## 🚀 Quick Start

```bash
# 1. Start the application
streamlit run app.py

# 2. Upload a PDF paper
# 3. Get instant plagiarism analysis!
```

---

## 📊 Understanding Your Results

### Main Metrics Display

When you upload a paper, you'll see three key metrics:

```
┌──────────────────────────────────────────┐
│ 📊 Overall Plagiarism Score: XX%        │
│    Risk Level: [Icon] [Level]           │
│    [Interpretation message]              │
├──────────────────────────────────────────┤
│ 🔍 Matches Found: N                     │
│ 📈 Highest Match: XX%                   │
└──────────────────────────────────────────┘
```

### What Each Metric Means

#### 📊 Overall Plagiarism Score
**The most important number!** This is like Turnitin's similarity index.

- Calculated from top 5 most similar papers
- Uses strict scoring (70% threshold, 35% baseline)
- **This is what you should focus on**

#### 🔍 Matches Found
How many papers in our database exceeded the 70% similarity threshold.

- More matches = higher concern
- 0 matches = highly original work
- 1-2 matches = review recommended
- 5+ matches = significant concern

#### 📈 Highest Match
The adjusted score of your most similar paper.

- **Now shows adjusted score** (consistent with overall!)
- Usually close to overall score
- If much higher, check that specific paper

---

## 🎯 Score Interpretation

### ✅ 0-15%: Original Work
```
Risk Level: ✅ Original
What it means: Your paper is highly original!
Action: Safe for submission
```

**Typical causes:**
- Novel research topic
- Unique methodology
- Minimal literature review overlap

**Example:** New AI technique with unique approach

---

### 🟢 15-30%: Low Risk
```
Risk Level: 🟢 Low Risk
What it means: Mostly original with normal academic overlap
Action: Generally acceptable, quick review recommended
```

**Typical causes:**
- Extended literature review
- Standard methodology descriptions
- Common field terminology
- Normal citation overlap

**Example:** Research paper with comprehensive background section

---

### 🟡 30-50%: Moderate Risk
```
Risk Level: 🟡 Moderate Risk
What it means: Significant similarity detected
Action: Careful review needed, consider revision
```

**Typical causes:**
- Heavy literature review (30%+ of paper)
- Similar experimental design to existing work
- Insufficient paraphrasing in some sections
- Multiple papers with overlapping content

**Example:** Paper extending existing method with similar description

---

### 🟠 50-70%: High Risk
```
Risk Level: 🟠 High Risk
What it means: Extensive similarities found
Action: Major revision required before submission
```

**Typical causes:**
- Large sections match existing papers
- Paraphrasing too close to source
- Missing or incomplete citations
- Reuse of previous methodology sections

**Example:** Paper with significant unattributed content from sources

---

### 🔴 70-100%: Critical
```
Risk Level: 🔴 Critical
What it means: Severe plagiarism detected
Action: Likely unpublishable, complete rewrite needed
```

**Typical causes:**
- Direct copying from sources
- Self-plagiarism (republishing own work)
- Contract cheating
- Translated plagiarism

**Example:** Paper that is nearly identical to existing publication

---

## 🔬 How Strict Scoring Works

### The Problem We Solved

**Old approach:** Simple text matching
- "machine learning" appears in both papers → Match!
- Result: 60%+ scores for completely different papers ❌

**New approach:** Strict semantic scoring
- Only counts genuinely similar papers (>70%)
- Removes common academic language (35% baseline)
- Result: 15-20% for different papers ✅

### The Algorithm (Simplified)

```
Step 1: Find similar papers (embedding-based)
Step 2: Filter out low similarities (<70%)
Step 3: Subtract academic baseline (35%)
Step 4: Weight top matches (60% highest, 40% avg others)
Step 5: Classify risk level
```

### Example Calculation

**Different Papers:**
```
Raw scores: [62%, 58%, 55%, 51%, 49%]
↓ Apply 70% threshold
No matches above threshold
↓ Check moderate matches (60-70%)
Highest: 62%
↓ Heavy discount (×0.3)
Final: 18.6% (Low Risk) ✅
```

**Plagiarized Paper:**
```
Raw scores: [88%, 75%, 72%, 70%, 68%]
↓ Apply 70% threshold
All 5 match!
↓ Subtract 35% baseline
Adjusted: [82%, 62%, 57%, 54%, 51%]
↓ Weight (60/40)
Final: 71.2% (Critical) ✅
```

---

## 🔍 Individual Paper Matches

### When You See Matches

If your paper has similarities above the threshold, you'll see:

```
🔎 Significant Matches Found:
Showing X papers with adjusted similarity ≥ 30%

#1 🟡 "Paper Title Here" - 35%
   
   Adjusted Score: 35.2%  ← After strict scoring
   Raw Similarity: 72.1%   ← Original embedding similarity
   Assessment: Moderate Similarity
   
   Contribution to Overall Score:
   ⭐ Primary match (60% weight)
   
   ℹ️ High match (≥70%) - adjusted by removing 35% baseline
```

### When You See No Matches

```
✅ No significant matches found above 30% threshold after strict scoring.

💡 This means your paper is highly original! Some moderate 
similarities (60-70%) may exist but were filtered out.
```

---

## 🎛️ Adjusting Sensitivity

### The Threshold Slider

```
Display Threshold (adjusted similarity score)
[Slider: 0.0 ─────●─── 1.0]
Currently: 0.30 (30%)
```

**What it does:**
- Controls which individual papers are shown
- **Works on adjusted scores** (after strict scoring)
- Doesn't affect overall plagiarism score

**Recommended settings:**
- **0.30 (default)**: Good for most cases
- **0.20**: More sensitive, see more matches
- **0.40**: Stricter, only significant matches

---

## 💡 Common Questions

### Q: Why is my overall score different from the highest match?

**A:** The overall score is a weighted average:
- 60% from highest match
- 40% from average of next 4 matches

Example:
```
Highest: 50%
Others: 40%, 35%, 30%, 28%
Overall: (0.6 × 50) + (0.4 × 33.25) = 43.3%
```

### Q: Why do I see "18%" when the raw score is "62%"?

**A:** Strict scoring adjustment:
- Raw 62% is below the 70% threshold
- Classified as "moderate match"
- Heavily discounted: 62% × 0.3 = 18.6%

### Q: What if I'm checking my own published paper?

**A:** You'll see high scores (80-95%) - this is expected!
- This is "self-plagiarism" detection
- Useful for checking if you're reusing too much from your own work
- For new papers, aim for <30% even compared to your own work

### Q: My survey paper shows 40% - is that bad?

**A:** Not necessarily!
- Survey papers naturally summarize existing work
- 30-40% is common for surveys
- Check individual matches to ensure proper citations
- Consider the context of your paper type

### Q: Can I trust the "Low Risk" assessment?

**A:** Yes, but always review manually:
- Strict scoring reduces false positives
- But it can't check for proper citations
- Human review is still essential
- Use this as a first-pass filter

---

## 🎨 Special Paper Types

### Literature Reviews / Surveys
**Expected range:** 25-40%
- Naturally summarize existing work
- Higher baseline is acceptable
- Ensure all sources properly cited

### Meta-Analyses
**Expected range:** 30-45%
- Combine multiple studies
- Statistical methods are standard
- Focus on proper attribution

### Replications
**Expected range:** 35-50%
- Deliberately similar to original
- Methodology should be similar
- Clearly cite original study

### Mathematical Papers
**Expected range:** 20-30%
- Standard notation and formulas
- Proofs may have common structure
- Original theorems should be clear

### Novel Research
**Expected range:** 10-25%
- Most original content
- Standard only in intro/background
- Should have low scores

---

## ⚙️ Technical Details

### Database
- **Papers:** 2,541 arXiv papers
- **Authors:** 5,081 researchers
- **Coverage:** Computer Science, AI, ML
- **Update frequency:** Static (for this version)

### Models
- **Text Embeddings:** all-MiniLM-L6-v2 (384-dim)
- **GNN Model:** GraphSAGE (2 layers, 128-dim output)
- **Training:** Kaggle GPU (5 minutes)
- **Accuracy:** Validated on test set

### Scoring Parameters
```python
SUSPICIOUS_THRESHOLD = 0.70   # High similarity threshold
ACADEMIC_BASELINE = 0.35      # Common language discount
MODERATE_DISCOUNT = 0.30      # Discount for 60-70% matches
WEIGHTING = (0.60, 0.40)      # Highest vs others
```

---

## 🚨 Limitations & Disclaimers

### What This Tool Can Do:
✅ Detect semantic similarity to papers in database
✅ Identify potential plagiarism issues
✅ Provide first-pass filtering
✅ Calculate Turnitin-style scores

### What This Tool Cannot Do:
❌ Replace human review
❌ Check proper citation format
❌ Detect plagiarism from sources outside database
❌ Understand context (e.g., quotes)
❌ Verify paraphrasing quality

### Important Notes:
⚠️ **Not a substitute for manual review**
⚠️ **Limited to database of 2,541 papers**
⚠️ **Cannot detect plagiarism from books, websites, unpublished work**
⚠️ **Focuses on semantic similarity, not word-for-word matching**

---

## 📖 Best Practices

### For Authors:
1. **Upload early** - check during writing process
2. **Aim for <25%** - shows strong originality
3. **Review all matches** - even low-scoring ones
4. **Ensure proper citations** - similarity is OK if cited
5. **Paraphrase effectively** - don't just swap words

### For Reviewers:
1. **Start with overall score** - main indicator
2. **Check individual matches** - understand sources
3. **Consider paper type** - surveys vs novel research
4. **Manual verification** - always read flagged sections
5. **Context matters** - quoted text is OK if marked

### For Instructors:
1. **Set clear expectations** - e.g., "must be <30%"
2. **Explain limitations** - this is a tool, not a verdict
3. **Require manual review** - for scores >40%
4. **Consider exceptions** - paper type, field norms
5. **Use as teaching tool** - help students understand plagiarism

---

## 🔧 Troubleshooting

### "GNN model not loaded"
**Solution:** Run training first
```bash
python train_gnn_model.py
# OR upload to Kaggle and run train_gnn_kaggle.ipynb
```

### "No PDF text extracted"
**Solution:** 
- Check if PDF is text-based (not scanned image)
- Try OCR if needed
- Convert to different PDF format

### "All scores show 0%"
**Solution:**
- Check if nodes.csv and relationships.csv exist
- Verify data loaded correctly
- Look for errors in terminal

### "Scores seem too high/low"
**Tuning options:**
- Adjust `SUSPICIOUS_THRESHOLD` (0.65-0.75)
- Change `ACADEMIC_BASELINE` (0.30-0.40)
- Modify `MODERATE_DISCOUNT` (0.2-0.4)

---

## 📚 Additional Resources

### Documentation Files:
- `QUICK_START.md` - Basic getting started
- `KAGGLE_TRAINING_GUIDE.md` - How to train model
- `STRICT_SCORING_EXPLAINED.md` - Deep dive into algorithm
- `INDIVIDUAL_SCORE_FIX.md` - How individual matches work
- `CONSISTENT_METRICS_FIX.md` - Why metrics are aligned
- `PLAGIARISM_SCORING_EXPLAINED.md` - Turnitin-style scoring

### Training Guides:
- `train_gnn_kaggle.ipynb` - Kaggle notebook (recommended)
- `train_gnn_model.py` - Local training script
- `KAGGLE_QUICK_START.md` - 5-minute setup

---

## 🎯 Success Criteria

**Your paper is ready for submission when:**

1. ✅ Overall score <30%
2. ✅ No individual matches >50%
3. ✅ All sources properly cited
4. ✅ Effective paraphrasing throughout
5. ✅ Original contribution is clear

**If any metric fails, review and revise before submitting!**

---

## 🙏 Acknowledgments

- **Database:** arXiv papers (Computer Science)
- **Models:** SentenceTransformers, PyTorch Geometric
- **Framework:** Streamlit
- **Training:** Kaggle GPUs (free tier)

---

## 📞 Support

For issues or questions:
1. Check documentation files
2. Review error messages in terminal
3. Verify all files present (app.py, nodes.csv, etc.)
4. Check Python version (3.8+)
5. Ensure all dependencies installed

---

**Version:** 2.0 (Strict Scoring Edition)
**Last Updated:** October 2025
**Status:** Production Ready ✅

---

**Happy researching with AURA! 🎓✨**
