# Structural Importance of Water in U.S. Production Networks

This repository contains code and data processing workflows for analyzing the structural role of water in the U.S. economy using Bureau of Labor Statistics (BLS) input–output tables (1997–2024).

The project compares commodity-by-commodity and industry-by-industry representations derived from the same underlying make–use framework to examine how modeling choices affect estimates of water’s economic importance.

Using Leontief-based methods, including hypothetical extraction and linkage analysis, the results show that water’s systemic impact varies substantially depending on how the production structure is specified.

The repository includes scripts for constructing input–output matrices, running extraction experiments, and generating figures used in ongoing research on water, production systems, and environmental constraints.
## Data

The analysis uses publicly available **Bureau of Labor Statistics input–output tables**, specifically the annual make–use tables for the U.S. economy.

Source:
Bureau of Labor Statistics. *Input–Output Accounts Data*.
https://www.bls.gov/emp/data/input-output-matrix.htm

The analysis covers the period **1997–2024**.

## Methods

The workflow follows standard transformations of rectangular make–use systems.

First, commodity–industry matrices are constructed from the BLS make and use tables. Using the industry-technology assumption, the analysis generates two square technical coefficient systems:

* commodity-by-commodity system
* industry-by-industry system

These systems are used to compute:

* backward and forward linkage measures
* hypothetical extraction experiments
* coefficient perturbation influence measures

These metrics evaluate three structural properties of the production network:

1. **Structural interconnectedness** (linkages)
2. **Structural indispensability** (extraction experiments)
3. **Structural sensitivity** (influence analysis)

## Repository Structure

data/
Raw or processed input–output tables

scripts/
Python and R scripts used to construct coefficient matrices and perform network analysis

outputs/
Generated tables and figures used in the manuscript

manuscript/
Drafts and supporting material for the research paper

## Reproducing the Analysis

1. Download the BLS make–use tables from the BLS website.
2. Place the data files in the `data/` directory.
3. Run the main analysis script:

```
python or python3 water_io_metrics.py
```

The script generates linkage measures, hypothetical extraction results, and influence metrics for each year in the dataset.

## Author

Kurt Semm, Ph.D.
Economics – Political Economy, Environmental Economics, and Water Guy

---
