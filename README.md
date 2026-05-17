# ⚙️ NavIQ-MLOps — MLOps Infrastructure for Mutual Fund RAG App

Production-style MLOps setup for [NavIQ](https://github.com/YashRM27/NavIQ), a RAG-based mutual fund analysis tool. This repo containerises the application, orchestrates it with Docker Compose, defines Kubernetes manifests for scalable deployment, and automates the build pipeline with GitHub Actions CI/CD.

---

## 🏗️ Architecture

```
Developer pushes code
        │
        ▼
GitHub Actions (CI/CD)
        │
        ├── Build Docker image
        └── Push to Docker Hub
                │
                ▼
        Docker Compose (local)         Kubernetes (production)
        ┌─────────────────┐           ┌─────────────────────┐
        │  app container  │           │  naviq Deployment   │
        │  (Streamlit +   │           │  (Streamlit + RAG)  │
        │   RAG pipeline) │           └──────────┬──────────┘
        └────────┬────────┘                      │ HTTP
                 │ HTTP                           ▼
                 ▼                    ┌─────────────────────┐
        ┌─────────────────┐           │ ChromaDB StatefulSet│
        │chromadb container│          │ + PersistentVolume  │
        │ (vector store)  │           └─────────────────────┘
        └─────────────────┘
```

---

## ✨ What This Repo Covers

- **Docker** — single container image for the Streamlit + RAG app
- **Docker Compose** — multi-container local setup (app + ChromaDB as separate services)
- **Kubernetes** — production-grade manifests with StatefulSet, PVC, ConfigMap, and Secrets
- **GitHub Actions** — automated CI/CD pipeline that builds and pushes to Docker Hub on every push to `main`

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Containerisation | Docker |
| Local orchestration | Docker Compose |
| Production orchestration | Kubernetes |
| CI/CD | GitHub Actions |
| Image registry | Docker Hub |
| Vector store | ChromaDB (HTTP server mode) |
| App | Streamlit + LLaMA 3.3 via Groq |

---

## 📁 Project Structure

```
NavIQ-MLOps/
├── .github/
│   └── workflows/
│       └── ci.yaml                  # GitHub Actions CI/CD pipeline
├── kubernetes/
│   ├── secret.yaml                  # Groq API key (base64 encoded)
│   ├── configmap.yaml               # Non-sensitive environment config
│   ├── chromadb-pvc.yaml            # Persistent storage for ChromaDB
│   ├── chromadb-statefulset.yaml    # ChromaDB as a StatefulSet
│   ├── chromadb-service.yaml        # Internal ClusterIP service for ChromaDB
│   ├── deployment.yaml              # Streamlit app Deployment
│   └── app-service.yaml             # NodePort service to expose the app
├── data/                            # Data pipeline scripts
├── processing/                      # Metric computation scripts
├── rag/                             # Embedding, retrieval, LLM scripts
├── app.py                           # Streamlit UI
├── Dockerfile                       # App container definition
├── docker-compose.yml               # Multi-container local setup
├── requirements.txt
└── .env.example
```

---

## 🚀 Running Locally with Docker Compose

### Prerequisites
- Docker Desktop installed and running
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Steps

**1. Clone the repo**
```bash
git clone https://github.com/YashRM27/NavIQ-MLOps.git
cd NavIQ-MLOps
```

**2. Set up environment**
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

**3. Start both containers**
```bash
docker compose up --build
```

**4. Embed fund data into ChromaDB (first time only)**
```bash
docker compose exec app python rag/embed_chunks.py
```

**5. Open the app**
```
http://localhost:8502
```

---

## ☸️ Kubernetes Deployment

### Prerequisites
- `kubectl` installed
- A running cluster (Minikube locally or any cloud provider)

### Deploy

**1. Apply all manifests in order**
```bash
kubectl apply -f kubernetes/secret.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/chromadb-pvc.yaml
kubectl apply -f kubernetes/chromadb-statefulset.yaml
kubectl apply -f kubernetes/chromadb-service.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/app-service.yaml
```

**2. Check everything is running**
```bash
kubectl get pods
kubectl get services
```

**3. Access the app (Minikube)**
```bash
minikube service naviq-service
```

---

## 🔄 CI/CD Pipeline

Every push to `main` triggers the GitHub Actions workflow:

```
Push to main
     │
     ▼
Checkout code
     │
     ▼
Login to Docker Hub
     │
     ▼
Build Docker image
     │
     ▼
Push to Docker Hub as:
{DOCKERHUB_USERNAME}/naviq-app:latest
```

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token (Read/Write) |

Add under: **GitHub repo → Settings → Secrets and variables → Actions**

---

## 🔑 Environment Variables

```bash
# .env.example
GROQ_API_KEY=your_groq_api_key_here
CHROMA_HOST=chromadb
CHROMA_PORT=8000
```

---

## 🔀 Key Architecture Decision — ChromaDB as a Separate Service

In the original NavIQ repo, ChromaDB runs embedded inside the app process using `PersistentClient`. Here it runs as a **separate container** using `HttpClient`:

```python
# Original NavIQ
chromadb.PersistentClient(path=CHROMA_DIR)

# NavIQ-MLOps
chromadb.HttpClient(host=os.getenv("CHROMA_HOST"), port=int(os.getenv("CHROMA_PORT")))
```

This means:
- App and database scale independently
- ChromaDB data persists in a Docker volume / Kubernetes PVC
- Follows microservices architecture principles

---

## 📌 Roadmap

- [ ] Deploy on AWS EKS
- [ ] Add health checks and liveness probes to Kubernetes manifests
- [ ] Add CD step to GitHub Actions (auto-deploy to cluster after push)
- [ ] Add model caching layer to speed up cold starts
- [ ] Monitoring with Prometheus + Grafana

---

## 🔗 Related

- **NavIQ** (DS/AI repo) — [github.com/YashRM27/NavIQ](https://github.com/YashRM27/NavIQ)
- **Docker Hub image** — `docker pull yashrm27/naviq-app:latest`

---

## 👤 Author

**Yash** — Data Scientist & MLOps  
[GitHub](https://github.com/YashRM27) · [LinkedIn](https://linkedin.com/in/yashmavare)

---

## 📄 License

MIT License — free to use, modify, and distribute.