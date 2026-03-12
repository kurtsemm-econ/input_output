# Structural Importance of Water in U.S. Production Networks

This repository contains the code and analysis used in the paper examining how **representational choices in make–use input–output systems influence estimates of sectoral importance** within production networks. Using water as an empirical case, the project evaluates how commodity-by-commodity and industry-by-industry representations of the U.S. economy produce different estimates of systemic importance.

The analysis uses Bureau of Labor Statistics make–use tables to construct alternative technical coefficient systems and evaluate how each representation traces production interdependencies. The empirical strategy combines linkage measures, hypothetical extraction experiments, and coefficient perturbation analysis to measure structural interconnectedness and systemic sensitivity.

The results show that when production is represented in commodity space rather than industry space, the estimated systemic importance of water increases substantially. Removing water from the commodity-based system produces significantly larger reductions in total output than in the industry-based system. These findings suggest that the measurement of foundational inputs in production networks depends critically on representational assumptions embedded in input–output models.

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
python water_IO_bls.py
```

The script generates linkage measures, hypothetical extraction results, and influence metrics for each year in the dataset.

## Author

Kurt Semm, Ph.D.
Economics – Political Economy, Environmental Economics, and Water Guy

---
