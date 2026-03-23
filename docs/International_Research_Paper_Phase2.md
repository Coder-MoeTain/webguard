# Operational Machine Learning for Multiclass Web Attack Detection: Phase II—Robustness, Train–Serve Consistency, and Intrusion-Analytics Interfaces

**Article type:** Original research (Phase II of a two-part series; builds on Phase I)

**Suggested citation:** Author(s). *Operational Machine Learning for Multiclass Web Attack Detection: Phase II—Robustness, Train–Serve Consistency, and Intrusion-Analytics Interfaces.* [Conference/Journal], Year.

---

## Abstract

Phase I of this series established a **multiclass** supervised pipeline—combining synthetic data generation, lexical and contextual **tabular features**, and **GPU-accelerated gradient-boosted trees**—for distinguishing benign traffic from SQL injection, cross-site scripting, and cross-site request forgery. This paper (Phase II) addresses **deployment-facing** questions that arise when moving from offline experiments to **security operations** [1]–[4]: (i) **train–serve consistency**, ensuring that the **feature mode** (payload-only vs. hybrid) and preprocessing used at inference match persisted training artifacts [3], [5]; (ii) **robustness and sensitivity analysis**, including feature ablation, zero-out perturbations, and out-of-distribution (OOD) stress tests [6]–[8]; (iii) **uncertainty-aware alerting** for analyst workflows, using confidence margins between top predicted classes [9], [10]; (iv) an **integrated service architecture** pattern—authenticated REST APIs [11], [12], rate limiting, durable job status for long-running training, and exportable **HTML/Markdown** experiment reports; and (v) **limitations** under adaptive adversaries and distribution shift [2], [7]. Together, Phase II connects the Phase I learning methodology to **actionable monitoring** and **reproducible experimentation governance** in organizational settings [4], [13].

**Keywords:** operational machine learning; web application security; train–serve skew; robustness; ablation; intrusion detection; REST APIs; uncertainty quantification; experiment reporting

---

## 1. Introduction

High test accuracy on curated datasets rarely guarantees reliable behavior in production. Security ML systems face **distribution shift** (benign traffic drift, novel attack encodings), **missing fields** at inference (e.g., response timing unavailable to an edge sensor), and **semantic mismatch** between training labels and analyst categories [1], [2]. When **feature definitions** or **preprocessing** differ between offline training and online scoring, error rates can rise sharply—a phenomenon often termed **train–serve skew** [3], [5].

**Phase II scope.** We extend the Phase I multiclass framework toward:

1. **Artifact-level consistency:** models ship with **serialized preprocessors** and explicit **feature-mode** metadata; inference paths must select extractors accordingly [3], [5].  
2. **Robustness evaluation:** systematic **ablation** of feature groups, **input perturbations**, and **OOD** probes to expose fragility before deployment [6], [8].  
3. **Human-in-the-loop IDS-style analytics:** ranking alerts using not only argmax labels but **probability margins** \(\Delta = p_{(1)} - p_{(2)}\) and low-confidence flags [9], [10].  
4. **Operational envelope:** authentication (e.g., JWT), **per-identity or per-IP rate limits**, persistent **job records** for reproducibility, and **report export** for audits and publications [11]–[12].  
5. **Governance:** explicit threat-model boundaries—detectors **assist** monitoring; they do not replace secure engineering [12], [14].

**Relation to Phase I.** Phase I defines *what* is learned; Phase II defines *how* it is **served**, **monitored**, and **stress-tested** [4].

---

## 2. Background and Related Work

**Train–serve skew** is documented across ML systems; mitigations include **single-source feature definitions**, **versioned artifacts**, and **shadow evaluation** [3,4]. In security, **adaptive adversaries** may optimize against known features [2], [6], motivating **robustness** sections in security-ML papers even when full adversarial robustness is out of scope.

**IDS dashboards** traditionally aggregate signatures; ML-augmented consoles increasingly show **scores**, **class breakdowns**, and **explanations** [14]. **Uncertainty** heuristics (entropy, margin) support triage when softmax probabilities are miscalibrated [9], [10].

---

## 3. Threat Model and Assumptions (Operational)

**In scope.** An adversary can submit HTTP requests observable by the detector (body, query, selected headers). The system may also see **response metadata** if the deployment path includes it (hybrid mode).

**Out of scope.** Full adversarial retraining against worst-case perturbations; **guaranteed** calibration of probabilities without held-out calibration data; protection against **training-data poisoning** (assumed controlled in research settings).

**Trust boundaries.** The API and storage layer must enforce **authentication** and **rate limits** to prevent abuse of compute-heavy training endpoints [11], [12].

---

## 4. Train–Serve Consistency

### 4.1 Feature modes

Three logical modes align with Phase I: **payload-only**, **response-only** (where applicable), and **hybrid**. A **skew** occurs if training uses hybrid features but deployment only supplies payload fields—models may rely on response scalars that are **imputed incorrectly** (e.g., zeros) at inference [1], [3].

**Mitigation.** Persist **feature_mode** with each trained artifact; inference loads the same extractor configuration. Default **HTTP context** profiles for laboratory tests should be documented to avoid systematic bias when headers are absent [5].

### 4.2 Preprocessing parity

Scaling constants, missing-value policies, and **categorical encodings** must be **frozen** in the saved pipeline [3], [5]. Tree models still require **column order** and **dtype** consistency.

### 4.3 Versioning

**Dataset hashes**, **commit identifiers**, and **hyperparameter snapshots** should accompany each job record for auditability [4], [13].

---

## 5. Robustness and Sensitivity Analysis

### 5.1 Group ablation

Remove or mask **SQLi**, **XSS**, **CSRF**, or **common** feature blocks independently; measure **macro-F1** drop. Large drops indicate over-reliance on a subset—informing monitoring (e.g., if CSRF features are often missing live) [8].

### 5.2 Zero-out and perturbation tests

Zero or noise **individual** high-importance features to measure **local sensitivity** [15], [16].

### 5.3 OOD and shift probes

Evaluate on **held-out** corpora from different generators or real logs (if available). Report **confusion** patterns—e.g., XSS misclassified as benign when encoded differently [1], [7].

---

## 6. Uncertainty-Aware Intrusion Analytics

Let class probabilities be \(p_1,\ldots,p_K\) in descending order. **High-confidence** alerts use \(\hat{y} = \arg\max_k p_k\) when \(p_{(1)} \ge \tau_c\) and margin \(\Delta = p_{(1)} - p_{(2)} \ge \tau_\Delta\). Otherwise, flag **review** to reduce false conviction from miscalibrated softmax outputs [9], [10].

**Operational note.** Thresholds \(\tau_c, \tau_\Delta\) are **organizational**; ROC or precision-recall curves on validation data guide selection [17].

---

## 7. System Architecture Pattern (Research Platform)

A reference architecture for reproducible experiments includes:

- **Client:** web dashboard for **dataset selection**, **training configuration**, **live monitoring** of jobs, **model comparison**, and **report export**.  
- **API layer:** REST endpoints for auth, data ingestion, feature extraction jobs, training jobs, inference, robustness jobs, and **system metrics** (CPU, memory, optional GPU telemetry) for observability.  
- **State:** relational metadata (users, jobs) with optional **file-backed** fallbacks for lightweight deployments.  
- **Workers (optional):** asynchronous execution for long training tasks with **Redis** or similar brokers [18].  
- **Artifacts:** filesystem or object storage for **datasets** and **serialized models**.

Security controls: **JWT** bearer tokens [11], **CORS** restrictions, **per-IP rate limiting**, **path validation** on uploads, **global error handling** without leaking stack traces in production [12].

---

## 8. Experimental Studies (Phase II)

**Suggested experiments.**

- E1: **Skew injection:** train hybrid, test payload-only with naive imputation—quantify degradation.  
- E2: **Ablation matrix:** report macro-F1 vs. removed feature groups.  
- E3: **Margin thresholds:** trade-off between analyst workload and false negatives on a validation slice.  
- E4: **Load testing:** API latency under rate limits for inference endpoints.

---

## 9. Results and Discussion (Template)

*Populate with measurements.* Emphasize **failure cases** (misclassification tables) and **operational** metrics (latency percentiles, job recovery after restart).

---

## 10. Ethics, Privacy, and Responsible Use

Synthetic and anonymized data are preferred for public artifacts. Production logs may contain **PII**; access control and **retention policies** are mandatory [19]. Exported reports should **scrub** secrets [12].

---

## 11. Conclusion

Phase II complements Phase I by foregrounding **operational ML** for multiclass web attack detection: **consistent** feature pipelines, **robustness** discipline, **uncertainty-aware** alerting, and **governed** experiment platforms [4], [13]. Future work includes **calibration** (temperature scaling, Platt scaling) [9], **continual learning** under drift [1], and **federated** evaluation across tenants [20].

---

## References

[1] J. Quiñonero-Candela, M. Sugiyama, A. Schwaighofer, and N. D. Lawrence, *Dataset Shift in Machine Learning*. Cambridge, MA, USA: MIT Press, 2009.

[2] N. Papernot, P. McDaniel, I. Goodfellow, S. Jha, Z. B. Celik, and A. Swami, “SoK: Security and privacy in machine learning,” in *Proc. IEEE Eur. Symp. Security Privacy (EuroS&P)*, 2018, pp. 399–414.

[3] D. Sculley et al., “Hidden technical debt in machine learning systems,” in *Advances Neural Inf. Process. Syst. (NeurIPS)*, 2015, pp. 2503–2511.

[4] N. Polyzotis et al., “Data management challenges in production machine learning,” in *Proc. ACM SIGMOD Int. Conf. Manage. Data*, 2017, pp. 1723–1726.

[5] E. Breck et al., “The ML test score: A rubric for ML production readiness and technical debt reduction,” in *Proc. IEEE Int. Conf. Big Data (Big Data)*, 2017, pp. 1573–1581.

[6] B. Biggio and F. Roli, “Wild patterns: Ten years after the rise of adversarial machine learning,” *Pattern Recognit.*, vol. 84, pp. 317–331, 2018.

[7] J. G. Moreno-Torres, T. Raeder, R. Alaiz-Rodríguez, N. V. Chawla, and F. Herrera, “A unifying view on dataset shift in classification,” *Pattern Recognit.*, vol. 45, no. 1, pp. 521–530, 2012.

[8] K. Koh et al., “WILDS: A benchmark of in-the-wild distribution shifts,” in *Proc. Int. Conf. Mach. Learn. (ICML)*, 2021, pp. 5637–5664.

[9] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, “On calibration of modern neural networks,” in *Proc. Int. Conf. Mach. Learn. (ICML)*, 2017, pp. 1321–1330.

[10] B. Lakshminarayanan, A. Pritzel, and C. Blundell, “Simple and scalable predictive uncertainty estimation using deep ensembles,” in *Advances Neural Inf. Process. Syst. (NeurIPS)*, 2017, pp. 6402–6413.

[11] M. Jones, J. Bradley, and N. Sakimura, “JSON Web Token (JWT),” IETF RFC 7519, May 2015. [Online]. Available: https://www.rfc-editor.org/rfc/rfc7519

[12] OWASP Foundation, “OWASP API Security Top 10,” OWASP, 2019. [Online]. Available: https://owasp.org/www-project-api-security/

[13] M. Mitchell et al., “Model cards for model reporting,” in *Proc. ACM Conf. Fairness Accountability Transparency (FAccT)*, 2019, pp. 220–229.

[14] S. Axelsson, “Intrusion detection systems: A survey and taxonomy,” *Technical Report 99-15*, Dept. Comput. Eng., Chalmers Univ. Technol., Göteborg, Sweden, 2000.

[15] M. T. Ribeiro, S. Singh, and C. Guestrin, “‘Why should I trust you?’ Explaining the predictions of any classifier,” in *Proc. ACM SIGKDD Int. Conf. Knowl. Discovery Data Mining (KDD)*, 2016, pp. 1135–1144.

[16] S. M. Lundberg and S.-I. Lee, “A unified approach to interpreting model predictions,” in *Advances Neural Inf. Process. Syst. (NeurIPS)*, 2017, pp. 4765–4774.

[17] J. Davis and M. Goadrich, “The relationship between precision-recall and ROC curves,” in *Proc. Int. Conf. Mach. Learn. (ICML)*, 2006, pp. 233–240.

[18] Redis Ltd., “Redis documentation,” 2024. [Online]. Available: https://redis.io/docs/

[19] Regulation (EU) 2016/679 of the European Parliament and of the Council (General Data Protection Regulation), *Official Journal of the European Union*, Apr. 27, 2016.

[20] K. Bonawitz et al., “Towards federated learning at scale: System design,” in *Proc. Mach. Learn. Systems (MLSys)*, 2019, pp. 374–388.

---

## Author contributions (template)

Conceptualization, software (services), validation, writing—assign per author.

## Funding

[If any]

## Conflicts of interest

None declared.

---

*Word count guideline: 6,000–10,000 words with figures (adjust for venue).*
