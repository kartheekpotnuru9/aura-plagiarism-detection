# 📊 Turnitin-Style Plagiarism Scoring - How It Works

## 🎯 Overview

Your plagiarism detector now provides an **overall plagiarism percentage** (0-100%) just like Turnitin, Grammarly, and other professional tools!

Instead of showing individual paper similarities, it calculates **how much of your content matches existing work** across the entire database.

---

## 🧮 How the Score is Calculated

### **Step 1: Find All Matching Papers**
```
Threshold: 50% similarity
Papers above this = "suspicious matches"
Papers below this = ignored (normal academic overlap)
```

### **Step 2: Identify Top Matches**
```
Top 5 most similar papers are selected
These contribute to the overall plagiarism score
```

### **Step 3: Calculate Weighted Score**
```python
Formula:
Overall Plagiarism % = (0.7 × Highest Match) + (0.3 × Average of Top 4)

Example:
Top matches: 85%, 72%, 68%, 65%, 60%

Calculation:
= (0.7 × 85%) + (0.3 × average(72%, 68%, 65%, 60%))
= 59.5% + (0.3 × 66.25%)
= 59.5% + 19.875%
= 79.4% overall plagiarism
```

**Why this weighting?**
- **70% from highest match**: The most similar paper is the primary concern
- **30% from others**: Shows if there's widespread similarity across multiple sources
- **Ignores noise**: Papers below 50% similarity don't count

---

## 📊 Score Interpretation

### ✅ **0-20%: Original Work**
- **Verdict**: Acceptable for publication
- **What it means**: Minimal overlap with existing work
- **Common sources**: 
  - Standard citations and references
  - Common technical terms
  - Widely-used methodologies
- **Action**: ✅ Good to go!

### 🟢 **20-40%: Low Risk**
- **Verdict**: Generally acceptable, minor review needed
- **What it means**: Some content overlaps but within normal range
- **Common sources**:
  - Extended literature review
  - Standard experimental procedures
  - Common problem definitions
- **Action**: 📝 Review matches, ensure proper citations

### 🟡 **40-60%: Moderate Risk**
- **Verdict**: Needs review and revision
- **What it means**: Significant portions match existing papers
- **Common sources**:
  - Large sections from literature review
  - Similar methodology descriptions
  - Overlapping results discussions
- **Action**: ⚠️ Revise, paraphrase, add citations

### 🟠 **60-80%: High Risk**
- **Verdict**: Major revision required
- **What it means**: Extensive similarities, potential plagiarism
- **Common sources**:
  - Large copied sections
  - Minimal paraphrasing
  - Missing citations
- **Action**: 🚨 Major rewrite needed!

### 🔴 **80-100%: Critical**
- **Verdict**: Severe plagiarism, likely unpublishable
- **What it means**: Paper is nearly identical to existing work
- **Common sources**:
  - Direct copying of entire sections
  - Self-plagiarism (republishing own work)
  - Contract cheating
- **Action**: 🛑 Complete rewrite or abandon

---

## 🎓 Real-World Examples

### Example 1: Original Research Paper
```
Upload: "Novel Deep Learning Architecture for Medical Imaging"

Analysis:
- Highest match: 42% (similar CNN architecture paper)
- Top 4 average: 28% (general medical imaging papers)

Score Calculation:
= 0.7 × 42% + 0.3 × 28%
= 29.4% + 8.4%
= 37.8%

Result: 🟢 Low Risk
Interpretation: Paper is original with normal overlap in technical descriptions
```

### Example 2: Literature Review Heavy
```
Upload: "Survey of Machine Learning in Healthcare"

Analysis:
- Highest match: 68% (another ML healthcare survey)
- Top 4 average: 55% (related survey papers)

Score Calculation:
= 0.7 × 68% + 0.3 × 55%
= 47.6% + 16.5%
= 64.1%

Result: 🟠 High Risk
Interpretation: Too much overlap with existing surveys, needs rewriting
```

### Example 3: Plagiarized Content
```
Upload: Paper copied from existing work

Analysis:
- Highest match: 95% (original source)
- Top 4 average: 45% (related papers)

Score Calculation:
= 0.7 × 95% + 0.3 × 45%
= 66.5% + 13.5%
= 80.0%

Result: 🔴 Critical
Interpretation: Severe plagiarism detected!
```

---

## 🔬 Technical Details

### What Gets Counted?

**Included:**
- Semantic similarity (meaning, not just words)
- Paraphrased content (our GNN catches this!)
- Similar methodologies and approaches
- Overlapping research concepts

**Excluded:**
- Papers below 50% similarity (normal overlap)
- Standard citations (if properly referenced)
- Common technical terms
- Widely-used formulas

### Why Semantic Similarity?

Traditional plagiarism detectors use **exact text matching**. We use **semantic similarity**, which is better because:

1. ✅ **Catches paraphrasing**: Detects when you rewrite but keep the same meaning
2. ✅ **Understands context**: Uses GNN to understand research relationships
3. ✅ **Smarter scoring**: Considers graph structure (authors, concepts)
4. ❌ **More sensitive**: May flag legitimate similar work (hence the 50% threshold)

---

## 📈 Comparison with Other Tools

| Feature | Turnitin | Grammarly | iThenticate | **Aura (Our Tool)** |
|---------|----------|-----------|-------------|---------------------|
| **Text Matching** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Semantic Similarity** | ⚠️ Limited | ⚠️ Limited | ⚠️ Limited | ✅ **Advanced** |
| **Graph Context** | ❌ No | ❌ No | ❌ No | ✅ **Yes (GNN)** |
| **Overall Score** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ **Yes** |
| **Source Breakdown** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ **Yes** |
| **Database Size** | 70B+ pages | Large | 70B+ pages | **2,541 papers** |
| **Paraphrase Detection** | ⚠️ Moderate | ⚠️ Moderate | ⚠️ Moderate | ✅ **Excellent** |

**Our Advantage**: We use Graph Neural Networks to understand research relationships better than traditional tools!

---

## 🎛️ Adjusting Sensitivity

### Current Settings (in code):

```python
# Suspicious match threshold
SUSPICIOUS_THRESHOLD = 0.50  # 50% similarity

# Weighting
highest_match_weight = 0.7  # 70%
other_matches_weight = 0.3  # 30%

# Top K matches considered
top_k = 5
```

### Making it Stricter (fewer false positives):

```python
SUSPICIOUS_THRESHOLD = 0.60  # Raise to 60%
highest_match_weight = 0.8  # Focus more on top match
```

### Making it More Sensitive (catch more potential issues):

```python
SUSPICIOUS_THRESHOLD = 0.40  # Lower to 40%
top_k = 10  # Consider more matches
```

---

## 💡 Best Practices for Users

### Before Submission:

1. **Run the check early** - Not right before deadline
2. **Review all high matches** - Understand why they're similar
3. **Check your citations** - Ensure all sources are cited
4. **Paraphrase properly** - Don't just change a few words

### Interpreting Results:

1. **Check the top match** - Is it your own previous work? (Self-plagiarism)
2. **Look at the source** - Survey papers naturally have higher overlap
3. **Consider the field** - Some fields have more standardized language
4. **Review the breakdown** - Are matches across many papers or just one?

### Common False Positives:

- **Literature reviews** - Naturally summarize existing work
- **Standard methodologies** - Common experimental procedures
- **Technical definitions** - Widely-accepted terminology
- **Mathematical formulas** - Universal notation

**Tip**: Use the detailed match view to understand *why* each paper matches!

---

## 🚀 Future Enhancements

### Planned Features:

1. **Sentence-level matching** - Show exactly which sentences match
2. **Source highlighting** - Visual highlighting of matched sections
3. **Citation suggestions** - Auto-suggest missing citations
4. **Exclusion filters** - Exclude quotes, references, methodologies
5. **Temporal analysis** - Check against only papers published before yours
6. **Self-plagiarism detection** - Flag matches with your own previous work

---

## 📞 Summary

**Key Takeaways:**

1. ✅ **Overall score** = Weighted average of top 5 matches
2. ✅ **70% weight** on highest match (most important)
3. ✅ **30% weight** on average of next 4 matches
4. ✅ **50% threshold** = Only count significant matches
5. ✅ **Semantic matching** = Catches paraphrasing better than text-only

**Your plagiarism detector now works like a professional tool, but with the added power of Graph Neural Networks! 🎉**

---

**Need help?** Check the app's interpretation guide or review the top matching papers to understand your score.
