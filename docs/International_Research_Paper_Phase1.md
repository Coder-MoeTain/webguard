# Scalable Multiclass Detection of SQL Injection, Cross-Site Scripting, and Cross-Site Request Forgery Using Gradient-Boosted Tree Ensembles: Phase I—Data Pipeline, Feature Engineering, and GPU-Accelerated Learning

**Article type:** Original research (Phase I of a two-part series)

**Suggested citation:** Author(s). *Scalable Multiclass Detection of SQL Injection, Cross-Site Scripting, and Cross-Site Request Forgery Using Gradient-Boosted Tree Ensembles: Phase I—Data Pipeline, Feature Engineering, and GPU-Accelerated Learning.* [Conference/Journal], Year.

---

## Abstract

Web application attacks—particularly SQL injection (SQLi), cross-site scripting (XSS), and cross-site request forgery (CSRF)—remain central to industry threat taxonomies [1], [2]. This paper (Phase I) presents a reproducible **end-to-end learning pipeline** for **multiclass** discrimination among benign traffic and these three attack families, as opposed to collapsing all malicious activity into a single label [3], [4]. We describe (i) **large-scale synthetic dataset construction** with configurable class priors and HTTP-style fields; (ii) a **structured feature vocabulary** spanning lexical, structural, header- and token-oriented CSRF signals, and optional response-aware attributes for hybrid detection [5]–[7]; (iii) **preprocessing and stratified splitting** suitable for imbalanced security data [4], [9]; and (iv) **GPU-accelerated training** of gradient-boosted tree models (e.g., histogram-based XGBoost with CUDA) [10], with complementary tree and linear baselines [11]–[13]. Evaluation emphasizes **macro- and per-class F1**, confusion matrices, and multiclass ROC analysis under controlled imbalance [4], [14]. The contribution is methodological and empirical: a coherent, open-science-friendly recipe linking controlled data generation to interpretable tabular features and modern ensemble learning, forming the foundation for operational deployment and robustness studies reported in Phase II.

**Keywords:** web application security; SQL injection; XSS; CSRF; multiclass classification; feature engineering; XGBoost; GPU training; intrusion detection; machine learning

---

## 1. Introduction

Despite widespread adoption of prepared statements, content security policies, and anti-CSRF mechanisms, misconfiguration and legacy code continue to expose applications to injection and client-side attacks [5], [6]. Signature-centric defenses require continual rule maintenance and struggle with polymorphic payloads and evolving attack grammars [17]. Supervised machine learning offers complementary detection from statistical regularities in requests and metadata, provided that **label semantics**, **feature availability**, and **evaluation metrics** align with operational needs and with documented risks of **technical debt** in ML systems [15], [16].

Many published studies report **binary** accuracy (attack vs. benign), which can obscure failure modes specific to XSS versus SQLi, for example [3]. **Multiclass** formulations that separate benign, SQLi, XSS, and CSRF better support triage, playbooks, and incident taxonomy—at the cost of harder learning problems under class imbalance [4], [9].

**Phase I scope.** This paper formalizes the **detection problem**, documents **dataset generation** up to multi-million-sample regimes with reproducible splits, specifies **feature groups** (payload-only, response-only, hybrid), and details **ensemble training** with GPU-oriented configurations. We intentionally defer extensive **robustness analysis**, **operational API design**, and **runtime intrusion analytics** to the companion Phase II paper, which builds on the same experimental backbone.

**Contributions (Phase I).**

1. A **unified multiclass formulation** with explicit mapping from HTTP-like records to feature vectors and labels.  
2. A **scalable synthetic data methodology** with configurable benign/attack ratios and family-specific substructure.  
3. A **documented feature catalog** for SQLi, XSS, CSRF, and shared contextual descriptors (length, entropy, encoding ratios, method flags, etc.).  
4. An **experimental protocol**: stratified train/validation/test splits, reporting of macro-F1, per-class metrics, and confusion matrices.  
5. **Implementation notes** for GPU-accelerated boosted trees and train-time consistency metadata required for later deployment.

---

## 2. Related Work

**Attack families.** SQLi exploits query syntax and database-specific constructs [5]; XSS injects content interpreted as markup or script [6]; CSRF abuses authenticated sessions via cross-site requests, often involving token and origin semantics [7].

**ML for web defense.** Approaches range from character-level models to tokenized logs and hybrid tabular features [17], [18]. Tree ensembles remain strong on heterogeneous tabular features and support feature-importance diagnostics [11], [12]. Histogram-based gradient boosting implementations—including GPU backends—reduce wall-clock time on large tabular datasets [10], [13], [19].

**Gap.** Many works lack a **single reproducible path** from synthetic control of class balance to **multiclass** metrics and **feature-level** transparency [3]. Phase I addresses that gap for a four-class setting.

---

## 3. Problem Formulation

Let each observation comprise HTTP-relevant fields (payload, URL fragments, headers, optional timing and response attributes). A **feature extractor** maps a record to \(\mathbf{x} \in \mathbb{R}^d\). Labels take values in \(\mathcal{Y} = \{\text{benign}, \text{sqli}, \text{xss}, \text{csrf}\}\) for multiclass mode, or \(\{0,1\}\) for binary baselines.

**Objective.** Learn \(f: \mathbb{R}^d \rightarrow \mathcal{Y}\) (or probability outputs over \(\mathcal{Y}\)) minimizing expected misclassification risk. With class probabilities \(\hat{p}_k(\mathbf{x})\), the multiclass cross-entropy over \(N\) samples is

\[
\mathcal{L}_{\mathrm{CE}} = -\frac{1}{N} \sum_{i=1}^{N} \log \hat{p}_{y_i}(\mathbf{x}_i).
\]

**Metrics.** Per-class precision, recall, and F1; **macro-F1** (unweighted mean over classes); **weighted F1**; accuracy; multiclass ROC-AUC (e.g., one-vs-rest macro average) [14], [20]. Under imbalance, macro-F1 and per-class views are emphasized alongside accuracy [4], [8].

---

## 4. Methodology

### 4.1 Dataset generation

Synthetic generation supports **controlled priors** (e.g., majority attack traffic with tunable benign fraction) and **family-specific** templates for SQLi, XSS, and CSRF, plus benign samples drawn from safe patterns, in line with common attack taxonomies [5]–[7]. Records may include simulated **request methods**, **header placeholders**, and **response fields** (status, length, latency) to enable hybrid feature modes. Outputs are stored in columnar formats suitable for large-scale training (e.g., CSV or Parquet) [21].

### 4.2 Feature design

Features are grouped into:

- **SQLi-oriented:** keyword presence (e.g., SELECT, UNION, SLEEP/BENCHMARK), tautology patterns, quote and comment markers, schema references, entropy of payload fragments, keyword density.  
- **XSS-oriented:** script tags, event handlers, `javascript:` URLs, `alert`/DOM API tokens, angle-bracket counts, encoding indicators.  
- **CSRF-oriented:** token presence/format, cross-origin indicators, referer absence, state-changing methods without validation cues, cookie SameSite heuristics.  
- **Common / contextual:** payload and URL lengths, digit counts, special-character and whitespace ratios, percent-encoding ratios, one-hot request methods, optional hybrid **response** features (status code, body length, response time).

**Modes:** *payload-only* (no response), *response-only* (where applicable), *hybrid* (payload plus response-derived scalars)—critical for matching training and inference conditions (expanded in Phase II) [15], [16].

### 4.3 Preprocessing and splitting

Numerical features are scaled or passed through tree models as raw tabular inputs per toolkit conventions. **Stratified** splits (e.g., 70/15/15 train/validation/test) preserve approximate class proportions under class skew [4], [9]. Random seeds are fixed for repeatability.

### 4.4 Models

**Primary:** gradient-boosted decision trees (XGBoost) with **histogram** tree methods and **GPU** device settings where available [10], for throughput on large tabular data. **Baselines:** random forests [11], linear models, or other boosted variants (LightGBM, CatBoost) may be included for ablation [12], [13]. **Artifacts:** serialized models with bundled **preprocessing** and **feature-mode** metadata to enforce consistent inference [15], [16].

### 4.5 Training protocol

Hyperparameters (e.g., number of estimators, max depth, learning rate) are documented per experiment. Training jobs log **progress**, **elapsed time**, and **validation curves** where applicable. Final evaluation on the **held-out test** set uses the same metrics as validation.

---

## 5. Experimental Design (Phase I)

**Research questions.**

- RQ1: Under fixed synthetic priors, how do **multiclass** macro-F1 and per-class F1 compare across **payload-only** vs. **hybrid** features?  
- RQ2: How does **GPU-accelerated** boosting reduce wall-clock time versus CPU baselines at comparable hyperparameters?  
- RQ3: Which **feature families** contribute most to discrimination (post-hoc importance or ablation previews)?

**Baselines.** Binary classifiers (benign vs. attack) and multiclass models trained on identical splits for fair comparison.

**Ethics and scope.** Synthetic data avoids exposing private production traffic. Results characterize **detector behavior under the generator’s distribution**; generalization to real traffic requires separate validation under **covariate and prior shift** [22] (Phase II discusses shift and robustness).

---

## 6. Results and Discussion (Template)

*Empirical numbers should be filled from your runs.* Suggested tables: (a) dataset sizes and class counts; (b) test metrics per model and feature mode; (c) confusion matrix for the best multiclass model; (d) training time GPU vs. CPU.

**Interpretation.** Hybrid features typically improve discrimination when response attributes carry signal but require consistent availability at inference [16]. Macro-F1 may trail accuracy when one class dominates; per-class recall for CSRF/XSS should be inspected explicitly [4], [8].

---

## 7. Limitations (Phase I)

- Synthetic distributions may **not** match production traffic; **dataset bias** and **domain shift** can degrade deployed models [18], [22]; adaptive adversaries may evade fixed lexical features [3].  
- Feature engineering trades interpretability for **manual maintenance** as attack grammar evolves [15].  
- **Class imbalance** requires careful thresholds and possibly resampling or class weights [8], [9] (reported in full experiments).

---

## 8. Conclusion

Phase I establishes a **multiclass**, **feature-transparent**, **GPU-scalable** pipeline for SQLi, XSS, and CSRF detection using tabular ensembles. The companion **Phase II** paper extends this work to **robustness evaluation**, **operational consistency** between training and serving, and **runtime monitoring** interfaces suitable for security operations.

---

## References

[1] OWASP Foundation, “OWASP Top Ten,” OWASP, 2021. [Online]. Available: https://owasp.org/www-project-top-ten/

[2] OWASP Foundation, “OWASP API Security Top 10,” OWASP, 2019. [Online]. Available: https://owasp.org/www-project-api-security/

[3] N. Papernot, P. McDaniel, I. Goodfellow, S. Jha, Z. B. Celik, and A. Swami, “SoK: Security and privacy in machine learning,” in *Proc. IEEE Eur. Symp. Security Privacy (EuroS&P)*, 2018, pp. 399–414.

[4] H. He and E. A. Garcia, “Learning from imbalanced data,” *IEEE Trans. Knowl. Data Eng.*, vol. 21, no. 9, pp. 1263–1284, Sep. 2009.

[5] W. G. J. Halfond, J. Viegas, and A. Orso, “A classification of SQL-injection attacks and countermeasures,” in *Proc. IEEE Int. Symp. Secure Softw. Eng. (ISSSE)*, 2006, pp. 13–15.

[6] D. Stuttard and M. Pinto, *The Web Application Hacker’s Handbook: Finding and Exploiting Security Flaws*, 2nd ed. Indianapolis, IN, USA: Wiley, 2011.

[7] OWASP Foundation, “Cross-Site Request Forgery Prevention Cheat Sheet,” OWASP Cheat Sheet Series. [Online]. Available: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html

[8] T. Fawcett, “An introduction to ROC analysis,” *Pattern Recognit. Lett.*, vol. 27, no. 8, pp. 861–874, 2006.

[9] M. Kubat and S. Matwin, “Addressing the curse of imbalanced training sets: One-sided selection,” in *Proc. Int. Conf. Mach. Learn. (ICML)*, 1997, pp. 179–186.

[10] T. Chen and C. Guestrin, “XGBoost: A scalable tree boosting system,” in *Proc. ACM SIGKDD Int. Conf. Knowl. Discovery Data Mining (KDD)*, 2016, pp. 785–794.

[11] L. Breiman, “Random forests,” *Mach. Learn.*, vol. 45, no. 1, pp. 5–32, Oct. 2001.

[12] G. Ke et al., “LightGBM: A highly efficient gradient boosting decision tree,” in *Advances Neural Inf. Process. Syst. (NeurIPS)*, 2017, pp. 3146–3154.

[13] L. Prokhorenkova et al., “CatBoost: Unbiased boosting with categorical features,” in *Advances Neural Inf. Process. Syst. (NeurIPS)*, 2018, pp. 6638–6648.

[14] M. Sokolova and G. Lapalme, “A systematic analysis of performance measures for classification tasks,” *Inf. Process. Manage.*, vol. 45, no. 4, pp. 427–437, 2009.

[15] D. Sculley et al., “Hidden technical debt in machine learning systems,” in *Advances Neural Inf. Process. Syst. (NeurIPS)*, 2015, pp. 2503–2511.

[16] D. Sculley et al., “Machine learning: The high-interest credit card of technical debt,” in *SE4ML: Softw. Eng. Mach. Learn. Systems (NIPS Workshop)*, 2014.

[17] A. L. Buczak and E. Guven, “A survey of data mining and machine learning methods for cyber security intrusion detection,” *IEEE Commun. Surveys Tuts.*, vol. 18, no. 2, pp. 1153–1176, 2016.

[18] A. Torralba and A. A. Efros, “Unbiased look at dataset bias,” in *Proc. IEEE Conf. Comput. Vision Pattern Recognit. (CVPR)*, 2011, pp. 1521–1528.

[19] XGBoost Developers, “GPU support,” *XGBoost Documentation*, 2024. [Online]. Available: https://xgboost.readthedocs.io/en/stable/gpu/

[20] J. Davis and M. Goadrich, “The relationship between precision-recall and ROC curves,” in *Proc. Int. Conf. Mach. Learn. (ICML)*, 2006, pp. 233–240.

[21] Apache Software Foundation, “Apache Parquet,” documentation. [Online]. Available: https://parquet.apache.org/

[22] J. G. Moreno-Torres, T. Raeder, R. Alaiz-Rodríguez, N. V. Chawla, and F. Herrera, “A unifying view on dataset shift in classification,” *Pattern Recognit.*, vol. 45, no. 1, pp. 521–530, 2012.

---

## Author contributions (template)

Conceptualization, methodology, software, validation, writing—assign per author.

## Funding

[If any]

## Conflicts of interest

None declared.

---

*Word count guideline: 6,000–10,000 words with figures (adjust for venue).*
