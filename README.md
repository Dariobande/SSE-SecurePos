# SSE - SecurePOS

[![Language](https://img.shields.io/badge/Language-Python%203.11%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%20%2F%20Flask--RESTful-green.svg)](https://flask.palletsprojects.com/)
[![ML Library](https://img.shields.io/badge/Machine%20Learning-scikit--learn-orange.svg)](https://scikit-learn.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Service--Oriented%20%2F%20BPMN-purple.svg)](https://en.wikipedia.org/wiki/Service-oriented_architecture)
[![Validation](https://img.shields.io/badge/Schema-JSON%20Schema%20Draft--7-yellow.svg)](https://json-schema.org/)

[Project Documentation](SecurePOS.pdf) | [Architecture Schemas](shared/json/) | [Requirements](requirements.txt)

This repository contains the design, BPMN 2.0 workflow modeling, service-oriented architecture (SOA), and implementation of **SecurePOS**, a distributed modular platform for fraud detection and risk classification in Point of Sale (POS) environments.

The project was developed for the **Software Systems Engineering** (SSE) course (Master of Science in Computer Engineering, **Università di Pisa**), Academic Year 2025–2026.

---

## Project Overview

Point of Sale (POS) environments generate high-velocity, heterogeneous streams of telemetry across multiple operational facets: financial transactions, network connection traces, and physical terminal localization. Detecting adversarial exploitation, fraudulent transactions, and compromised terminals requires an automated, robust, and resilient end-to-end data processing and machine learning lifecycle.

**SecurePOS** coordinates a distributed microservices pipeline that continuously ingests multi-source sensor batches, enforces fault-tolerant cleaning and feature engineering, validates dataset balance and coverage, trains neural network classifiers using grid search, performs real-time threat inference, and continuously audits classifier accuracy against ground truth.

Key capabilities of the system include:
- **Service-Oriented Microservices Architecture**: Decoupled, autonomous subsystems communicating over standardized HTTP/REST endpoints with contract enforcement guaranteed via JSON Schema.
- **Multi-Modal Data Ingestion**: Asynchronous aggregation of transaction records (timestamps, amounts), network telemetry (source and destination IP pairs), and geospatial coordinates (longitude, latitude) into unified session contexts.
- **Fault-Tolerant Data Preparation**: Robust cleaning pipeline incorporating missing-sample imputation (mode imputation with fallback handling), physical outlier clamping, and statistical feature derivation (Median Absolute Deviation [MAD], spatial coordinate medians, and integer-encoded IP addresses).
- **Dataset Segregation & Quality Assurance**: Pre-training validation layer auditing label distributions against class-imbalance tolerances, assessing feature space coverage, and deterministically segregating datasets into training, validation, and test partitions.
- **Automated Grid-Search Classifier Development**: Multi-layer Perceptron (`MLPClassifier`) hyperparameter exploration over layer depths and neuron topologies, coupled with automated validation reporting and human-in-the-loop sign-off.
- **Multi-Tier Threat Inference**: Real-time multi-class risk classification categorizing active POS sessions into `NORMAL`, `MODERATE`, or `HIGH` risk levels.
- **Closed-Loop Performance Evaluation**: Drift and degradation detection comparing inference outcomes against ground truth, enforcing maximum total error and consecutive failure budgets to trigger automated retraining workflows.
- **Synthetic Multi-Modal Simulator**: Multi-threaded generator simulating transaction dynamics, network socket traces, and spatial drift under normal and malicious exploitation scenarios for elasticity and latency benchmarking.

---

## Technical Specifications

| System Component | Technology / Mechanism | Specification / Details |
| :--- | :---: | :--- |
| **Runtime Environment** | Python 3.11+ | Modular package structure with isolated service controllers |
| **Inter-Service Communication** | RESTful HTTP / Flask | Lightweight HTTP POST protocol with dedicated worker threads (`SystemsIO`) |
| **Contract Validation** | JSON Schema Draft-7 | Strict schema enforcement on all incoming REST payloads (`jsonschema`) |
| **Machine Learning Engine** | scikit-learn (`MLPClassifier`) | Multi-layer Perceptron with grid search over layer depths and neuron counts |
| **Model Serialization** | Joblib | Binary model serialization and network transfer across services |
| **Data Processing & Splits** | Pandas & NumPy | In-memory manipulation, feature calculation, and train/val/test segregation |
| **Threat Taxonomy** | 3-Tier Categorical Enum | `NORMAL`, `MODERATE`, and `HIGH` attack risk levels |
| **Feature Extraction** | Statistical Aggregation | MAD of timestamps & amounts, median longitude & latitude, median source & destination IPs |
| **Data Imputation & Cleaning** | Mode Imputation & Clamping | Missing-sample replacement via mode statistics, transaction amount capping |
| **Quality & Balance Checks** | Tolerance Band Validation | Configurable balancing tolerance (±20%) and feature distribution coverage checks |
| **Model Evaluation Metrics** | Error Budget Tracking | Total classification error threshold and maximum consecutive error streak counter |

---

## System Architecture & Workflow Pipeline

The platform is partitioned into six decoupled microservices, an environment simulator, and a shared foundation library:

```
+-----------------------------------------------------------------------------------+
|                                  SIMULATOR                                        |
|         (Transaction Records, Network Flows, GPS Data, Ground Truth Labels)       |
+-----------------------------------------------------------------------------------+
                                   |  POST /record
                                   v
+-----------------------------------------------------------------------------------+
|                              INGESTION SYSTEM                                     |
|    - Buffers multi-modal records into unified RawSession instances                |
|    - Dispatches Ground Truth to Evaluation System (/actual-label)                 |
+-----------------------------------------------------------------------------------+
                                   |  POST /process
                                   v
+-----------------------------------------------------------------------------------+
|                             PREPARATION SYSTEM                                    |
|    - Cleans data & imputes missing values (DataCorrector)                         |
|    - Extracts statistical feature vectors (FeatureExtractor)                      |
+-----------------------------------------------------------------------------------+
              | (Development Phase)                       | (Production / Eval Phase)
              | POST /prepared-session                    | POST /prepared-session
              v                                           v
+-----------------------------+             +---------------------------------------+
|     SEGREGATION SYSTEM      |             |         CLASSIFICATION SYSTEM         |
|  - Quality & coverage check |             |  - Loads trained MLPClassifier        |
|  - Data balancing checks    |             |  - Predicts AttackRiskLevel           |
|  - Train/Val/Test splitting |             |  - Emits prediction (/predicted-label)|
+-----------------------------+             +---------------------------------------+
              | POST /calibration-sets                        |
              v                                               |
+-----------------------------+                               |
|     DEVELOPMENT SYSTEM      |                               |
|  - Hyperparameter grid      |                               |
|  - Trains & validates MLPs  |                               |
|  - Deploys best model       |                               |
+-----------------------------+                               |
              | POST /classifier                              |
              +---------------------------------->            |
                                                 |            |
                                                 v            v
                                   +------------------------------------------------+
                                   |               EVALUATION SYSTEM                |
                                   |  - Buffers (actual, predicted) label pairs     |
                                   |  - Computes error counts & streak thresholds   |
                                   |  - Generates evaluation reports for sign-off   |
                                   +------------------------------------------------+
```

### 1. Ingestion System (`ingestion_system/`)
- Listens on `/record` to receive streaming records emitted by client-side POS systems.
- Groups incoming transactions, network telemetry, and localization samples matching the same UUID into a single `RawSession`.
- Tracks system operational phases via `PhaseMessageCounter`, separating Development, Evaluation, and Production lifecycles.
- Forwards completed raw sessions to the Preparation System (`/process`) and routes ground-truth labels directly to the Evaluation System (`/actual-label`).

### 2. Preparation System (`preparation_system/`)
- Receives raw sessions via `/process`.
- Employs `DataCorrector` to impute missing values (using mode imputation with fallbacks) and clamp out-of-bound transaction amounts.
- Utilizes `FeatureExtractor` to transform raw time series and categorical arrays into fixed-dimension statistical vectors.
- Routes prepared sessions downstream to the Segregation System during development, or to the Classification System during production and evaluation.

### 3. Segregation System (`segregation_system/`)
- Stores incoming feature vectors in `PreparedSessionsDB`.
- Verifies dataset distribution against user-defined tolerances via `DataBalancingModel` and `DataBalancingView`.
- Assesses statistical coverage of feature spaces via `DataCoverageModel` and `DataCoverageView`.
- Partitions approved sessions into training, validation, and test datasets using `DataSplitter` and dispatches CSV calibration bundles to the Development System (`/calibration-sets`).

### 4. Development System (`development_system/`)
- Implements `DevelopmentSystemController`, orchestrating `TrainingController`, `ValidationController`, and `TestController`.
- Conducts grid-search exploration over neural network topologies (varying hidden layer depth and neurons per layer in `NeuralNetwork`).
- Evaluates models against overfitting and generalization thresholds, presenting validation reports for review.
- Serializes the winning `MLPClassifier` using `joblib` and deploys it to the Classification System via `/classifier`.

### 5. Classification System (`classification_system/`)
- Receives serialized models dynamically over `/classifier` without requiring service restarts.
- Listens for live feature vectors on `/prepared-session` and executes multi-class inference.
- Emits predicted risk classifications to the Evaluation System (`/predicted-label`) and dispatches completion timestamps to the Simulator (`/timestamp`).

### 6. Evaluation System (`evaluation_system/`)
- Listens on `/actual-label` (ground truth) and `/predicted-label` (classifier inference).
- Buffers aligned pairs within `LabelsBufferDB` until the evaluation threshold (`minNumberLabels`) is satisfied.
- Evaluates model health via `ClassifierEvaluationModel`, tracking total classification errors and maximum consecutive error streaks against strict error budgets (`maxErrors`, `maxConsecutiveErrors`).
- Produces structured reports (`evaluation_report.json`) through `ClassifierEvaluationView` to determine whether the model is approved or flagged for recalibration.

### 7. Simulator & Shared Foundation (`simulator/`, `shared/`)
- **Simulator**: Emulates POS client nodes, synthesizing parameterized normal, moderate, and high-risk traffic profiles, as well as executing system elasticity benchmarks.
- **Shared Module**: Provides centralized network addressing (`Address`), standardized endpoint management and thread-safe HTTP I/O (`SystemsIO`), configuration loading with schema validation (`load_and_validate_json_file`), and common domain enumerations (`AttackRiskLevel`, `Feature`).

---

## Data Models & Feature Space

Each session is identified by a unique `uuid` and transformed from raw multi-modal telemetry into a 6-dimensional feature vector:

| Feature Name | Type | Description |
| :--- | :---: | :--- |
| `mad_timestamps` | `float` | Median Absolute Deviation of transaction timestamps |
| `mad_amounts` | `float` | Median Absolute Deviation of transaction financial amounts |
| `median_longitude` | `float` | Median longitude coordinate of the terminal location |
| `median_latitude` | `float` | Median latitude coordinate of the terminal location |
| `median_source_ip` | `int` | Median integer-encoded IPv4 source address |
| `median_destination_ip` | `int` | Median integer-encoded IPv4 destination address |

### Target Classification Labels

The classification output corresponds to the `AttackRiskLevel` domain:
- **`NORMAL`**: Baseline transaction behavior within standard operating ranges.
- **`MODERATE`**: Suspicious telemetry patterns requiring elevated monitoring or secondary verification.
- **`HIGH`**: High-confidence anomaly or fraudulent activity requiring transaction blocking and security alerts.

---

## Operational Phases & Lifecycle

The platform operates across three coordinated phases configured via [`shared_config.json`](shared/json/shared_config.json):

1. **Development Phase (`developmentPhase: true`)**:
   - The Simulator generates labeled sessions to build calibration corpora.
   - The Segregation System validates data quality, audits balancing, and generates train/val/test splits.
   - The Development System runs hyperparameter grid search, selects the optimal classifier, and deploys it to the Classification System.

2. **Evaluation Phase (`evaluationPhaseWindow`)**:
   - The deployed model performs live inference while ground-truth labels are simultaneously collected.
   - The Evaluation System computes error counts and streak lengths over a designated sample window to ensure model performance adheres to production requirements.

3. **Production Phase (`productionPhaseWindow`)**:
   - The classifier operates online at scale, serving low-latency inference on incoming POS sessions with continuous monitoring.

---

## Non-Functional Properties & Resilience

As detailed in the [Project Documentation](SecurePOS.pdf), the system is evaluated across critical non-functional dimensions:
- **Responsiveness & Elasticity**: Benchmarked under varying transaction loads to quantify processing latency from ingestion through classification.
- **Fault Resiliency**: Gracefully handles missing telemetry samples, out-of-order record arrival, and out-of-range sensor readings through automated imputation and clipping.
- **Strict Contract Interoperability**: Every subsystem boundary validates incoming JSON structures against formal JSON schemas, discarding malformed payloads before processing.
- **Human-in-the-Loop Governance**: Strategic decision gates allow data analysts and engineers to inspect balance reports, review validation curves, and sign off on evaluation batches.

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **pip** package manager

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Dariobande/SSE-SecurePos.git
   cd SSE-SecurePos
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

Network endpoints and system parameters can be customized in the configuration files:
- **Global Network & Phase Settings**: [`shared/json/shared_config.json`](shared/json/shared_config.json)
- **Ingestion Settings**: [`ingestion_system/json/ingestion_system_configuration.json`](ingestion_system/json/ingestion_system_configuration.json)
- **Preparation Settings**: [`preparation_system/json/config.json`](preparation_system/json/config.json)
- **Segregation Settings**: [`segregation_system/configuration.json`](segregation_system/configuration.json)
- **Development Settings**: [`development_system/input/development_system_configuration.json`](development_system/input/development_system_configuration.json)
- **Evaluation Settings**: [`evaluation_system/json/config.json`](evaluation_system/json/config.json)

### Running the Services

To run the entire pipeline locally, launch each subsystem controller in separate terminal windows (or as background services):

```bash
# 1. Start the Evaluation System (Port 8006)
python -m evaluation_system.evaluation_system_controller

# 2. Start the Classification System (Port 8005)
python -m classification_system.classification_system_controller

# 3. Start the Development System (Port 8004)
python -m development_system.development_system_controller

# 4. Start the Segregation System (Port 8003)
python -m segregation_system.segregation_system_controller

# 5. Start the Preparation System (Port 8002)
python -m preparation_system.preparation_system_controller

# 6. Start the Ingestion System (Port 8001)
python -m ingestion_system.ingestion_system_controller
```

Once the core services are active, initiate the workload generator:

```bash
# 7. Run the Simulator (Port 8000)
python -m simulator.simulator
```
