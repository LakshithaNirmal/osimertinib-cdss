# Osimertinib Resistance CDSS (Clinical Decision Support System)

AI-Powered Transcriptomic Risk Stratification Platform for EGFR-mutant Non-Small Cell Lung Cancer (NSCLC).

## 🚀 Features
- **Machine Learning Classifier**: Pretrained Random Forest model trained on transcriptomic biomarkers.
- **Automated Feature Alignment & Imputation**: Handles missing genes and gene-by-sample or sample-by-gene orientation seamlessly.
- **Interactive Web Interface**: Single-page web dashboard with sample download, drag-and-drop file upload, and real-time clinical risk classification.
- **RESTful API**: Fast and light FastAPI backend.

---

## 🌐 Deploy to Render

### Option 1: Automatic Blueprint (Recommended)
1. Push this repository to GitHub / GitLab.
2. In Render Dashboard, click **New +** -> **Blueprint**.
3. Select this repository. Render will automatically read [`render.yaml`](render.yaml) and configure:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Option 2: Manual Web Service Setup
1. In Render Dashboard, click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Set the following parameters:
   - **Name**: `osimertinib-cdss`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`
4. Under **Environment Variables**, add:
   - `PYTHON_VERSION`: `3.11.9`
5. Click **Create Web Service**.

---

## 💻 Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python main.py
# Or run using run_app.bat on Windows
```

Open your browser at `http://127.0.0.1:8000`.

---

## 📡 API Endpoints

- `GET /`: Serves the CDSS Web Dashboard (`index.html`)
- `GET /api/health`: Health status and signature gene count
- `GET /api/sample-data`: Download the real TCGA patient cohort CSV (`Real_TCGA_Combined_Cohort.csv`)
- `POST /predict`: Upload a patient CSV/TSV expression profile to obtain risk predictions and EMT score
