# AI-Assisted End-to-End Drug Discovery Workflow 🧬💊

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![RDKit](https://img.shields.io/badge/RDKit-EF5B25?style=for-the-badge&logo=rdkit&logoColor=white)](https://www.rdkit.org/)
[![AutoDock Vina](https://img.shields.io/badge/AutoDock_Vina-007ACC?style=for-the-badge&logo=python&logoColor=white)](https://vina.scripps.edu/)

A state-of-the-art, production-ready pipeline for high-throughput virtual screening and molecular docking. This platform integrates Deep Learning (GNNs) with Physics-based simulations to accelerate the discovery of potent inhibitors for targets like EGFR.

---

## 🏗️ System Architecture

The platform follows a **layered, modular architecture** designed for high-throughput molecular simulations with a responsive user experience.

```mermaid
graph TB
    subgraph Frontend["🎨 FRONTEND LAYER<br/>(Next.js 16 + React 19)"]
        UI["Dashboard & Charts<br/>(Recharts)"]
        Viewer["3D Molecular Viewer<br/>(3Dmol.js)"]
    end

    subgraph API["🔌 API LAYER<br/>(FastAPI)"]
        REST["REST API Gateway<br/>localhost:8000"]
        Auth["JWT Authentication"]
    end

    subgraph Services["⚙️ SERVICES LAYER<br/>(Business Logic)"]
        Screening["Screening Service<br/>Graph Building<br/>Ranking"]
        Docking["Docking Service<br/>PDBQT Prep<br/>Pose Extraction"]
    end

    subgraph Compute["🧠 ML & COMPUTATIONAL<br/>LAYER"]
        ML["Ensemble Models<br/>RF + XGB + MPNN + GIN"]
        Vina["AutoDock Vina<br/>Binding Affinity"]
        RDKit["RDKit<br/>Molecule Processing"]
    end

    subgraph Database["💾 DATABASE LAYER<br/>(SQLAlchemy ORM)"]
        DB["PostgreSQL (Neon)<br/>Runs · Compounds<br/>Results · History"]
    end

    %% Connections
    UI --> REST
    Viewer --> REST
    REST --> Auth
    
    Auth --> Screening
    Auth --> Docking
    
    Screening --> ML
    Screening --> RDKit
    Docking --> Vina
    Docking --> RDKit
    
    Screening --> DB
    Docking --> DB

    %% Styling
    classDef frontend fill:#3b82f6,stroke:#1e40af,color:#fff,stroke-width:2px
    classDef api fill:#6366f1,stroke:#4338ca,color:#fff,stroke-width:2px
    classDef services fill:#10b981,stroke:#047857,color:#fff,stroke-width:2px
    classDef compute fill:#f59e0b,stroke:#d97706,color:#fff,stroke-width:2px
    classDef database fill:#8b5cf6,stroke:#6d28d9,color:#fff,stroke-width:2px

    class Frontend,UI,Viewer frontend
    class API,REST,Auth api
    class Services,Screening,Docking services
    class Compute,ML,Vina,RDKit compute
    class Database,DB database
```

---

## 🧩 Module Descriptions

### 4.2.1 User Interface Module
A responsive, high-performance web dashboard built with **Next.js 16**, **React 19**, **TypeScript 5.7**, and **Tailwind CSS**. 
- **Interactive 3D Viewer:** Integrated `3Dmol.js` for real-time exploration of protein-ligand docking poses with custom cartoon/stick rendering.
- **Dynamic Analytics:** Real-time visualization of pIC50 distributions, confidence intervals, and Lipinski compliance using `Recharts` & `Lucide` icons.
- **Session Management:** Secure user state handled via React Context API and JWT persistence.

### 4.2.2 API Gateway
The central nervous system of the platform, powered by **FastAPI**.
- **Unified Interface:** Provides a standardized RESTful API for all frontend requests.
- **Security:** Implements OAuth2 with JWT Bearer tokens and password hashing (Passlib).
- **Concurrency:** Leverages Python's `asyncio` to handle multiple screening and docking jobs without blocking the main event loop.

### 4.2.3 Processing Engine
The core logic responsible for the physical world simulation.
- **Docking Orchestration:** Automates the preparation of receptor (PDB) and ligand (SMILES/SDF) files into PDBQT format.
- **AutoDock Vina Integration:** Executes parallelized docking simulations to calculate precise binding affinities (kcal/mol).
- **Lipinski Filtering:** High-speed chemical property filtering (MW, LogP, HBD, HBA) powered by **RDKit**.

### 4.2.4 AI / ML Model Module
A hybrid intelligence layer that combines the speed of Deep Learning with the accuracy of physics.
- **Graph Neural Networks:** Implements **GIN (Graph Isomorphism Network)** and **MPNN (Message Passing Neural Network)** for structural pIC50 prediction.
- **Classical Ensemble:** Includes **Random Forest** and **XGBoost** models trained on diverse molecular descriptors.
- **Uncertainty Quantification:** Provides confidence scores for every prediction, highlighting potential "black swan" molecules.

### 4.2.5 Database Layer
A robust persistence layer using **PostgreSQL** (hosted on AWS Neon) with **SQLAlchemy ORM**.
- **Cloud-Hosted:** PostgreSQL on Neon with SSL/TLS encryption for secure data transmission.
- **Relational Integrity:** Tracks complex relationships between Users, Screening Runs, Docking Results, and individual Compound Predictions.
- **Bulk Persistence:** Optimized for high-throughput writes, allowing thousands of screening results to be saved per batch.
- **Audit Trail:** Maintains full history of every discovery run, model performance, and user feedback for longitudinal analysis.

---

## 🚀 Key Features

- **End-to-End Workflow:** From raw SMILES strings to 3D docked poses in one unified interface.
- **High-Throughput Batch Screening:** Process thousands of compounds simultaneously with optimized RDKit processing.
- **Interactive 3D Visualization:** Explore binding pockets with professional-grade molecular rendering.
- **Dynamic Analytics Dashboard:** Detailed model performance metrics and chemical property distribution.

---

## 🛠️ Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | Next.js, React, TypeScript, Tailwind CSS | 16.2.4, 19, 5.7.3 |
| **Backend** | FastAPI, Uvicorn, SQLAlchemy, Pydantic | 0.115+, 2.8+ |
| **ML/AI** | PyTorch, PyTorch Geometric, scikit-learn, XGBoost | 2.3+, 2.5+, 1.5+, 2.1+ |
| **Chemistry** | RDKit, Biopython, meeko | 2022.9.5+, 1.84+, 0.6+ |
| **Docking** | AutoDock Vina | Latest |
| **Database** | PostgreSQL (Neon), SQLAlchemy ORM | AWS Neon |
| **UI/Viz** | 3Dmol.js, Recharts, Radix UI, Lucide | CDN, Latest |

---

## 🏁 Getting Started

1. **Clone the Repo:**
   ```bash
   git clone https://github.com/your-repo/drug-discovery-workflow.git
   ```
2. **Setup Backend:**
   ```bash
   pip install -r requirements.txt
   python scripts/run_server.py
   ```
3. **Setup Frontend:**
   ```bash
   cd frontend
   pnpm install
   pnpm run dev
   ```

---

