from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
import pandas as pd
import numpy as np
import joblib
import json
import io
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Osimertinib Resistance CDSS API",
    description="Transcriptomic Risk Classifier for EGFR-mutant NSCLC",
    version="1.0.0"
)

# Enable CORS so your frontend can call this API from any domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load artifacts into memory on startup
try:
    MODEL = joblib.load(BASE_DIR / "rf_osimertinib_model.joblib")
    SCALER = joblib.load(BASE_DIR / "scaler.joblib")
    with open(BASE_DIR / "feature_genes.json", "r") as f:
        FEATURE_GENES = json.load(f)
except Exception as e:
    print(f"Error loading models or genes: {e}")
    FEATURE_GENES = []

@app.get("/")
def serve_frontend():
    """Serve the modern CDSS frontend."""
    index_path = BASE_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "index.html not found"}

@app.get("/api/health")
def health_check():
    return {"status": "active", "required_features": len(FEATURE_GENES)}

@app.get("/api/sample-data")
def download_sample_data():
    """Endpoint for users to download the sample patient profile CSV."""
    sample_path = BASE_DIR / "Sample_Patient_Profile.csv"
    if sample_path.exists():
        return FileResponse(sample_path, media_type="text/csv", filename="Sample_Patient_Profile.csv")
    return Response(content="Sample data not found on server.", status_code=404)

@app.post("/predict")
async def predict_risk(file: UploadFile = File(...)):
    if not file.filename.endswith(('.csv', '.tsv')):
        raise HTTPException(status_code=400, detail="File must be a CSV or TSV")

    try:
        contents = await file.read()
        separator = '\t' if file.filename.endswith('.tsv') else ','
        df = pd.read_csv(io.BytesIO(contents), sep=separator, index_col=0)
        
        # Clean Ensembl IDs by removing version decimals if present, and whitespace
        clean_index = df.index.astype(str).str.strip().str.split('.').str[0]
        clean_cols = df.columns.astype(str).str.strip().str.split('.').str[0]

        # Check whether genes are along index or columns by checking overlap
        genes_in_index = sum(1 for g in FEATURE_GENES if g in clean_index.values)
        genes_in_cols = sum(1 for g in FEATURE_GENES if g in clean_cols.values)

        if genes_in_index > genes_in_cols:
            df.index = clean_index
            df = df.T
            df.columns = df.columns.astype(str).str.strip().str.split('.').str[0]
        else:
            df.columns = clean_cols
            
        # Deduplicate columns if any duplicate genes exist, keep first
        df = df.loc[:, ~df.columns.duplicated(keep='first')]

        # Extract available signature genes and pad missing features with 0.0
        matched_genes = [g for g in FEATURE_GENES if g in df.columns]
        missing_genes = [g for g in FEATURE_GENES if g not in df.columns]

        aligned_data = pd.DataFrame(index=df.index)
        for g in FEATURE_GENES:
            if g in df.columns:
                aligned_data[g] = pd.to_numeric(df[g], errors='coerce').fillna(0.0)
            else:
                aligned_data[g] = 0.0

        # Scale features using the fitted scaler
        scaled_features = SCALER.transform(aligned_data)

        # Generate model inference
        probabilities = MODEL.predict_proba(scaled_features)[:, 1]
        predictions = MODEL.predict(scaled_features)

        results = []
        for sample_id, prob, pred in zip(df.index, probabilities, predictions):
            results.append({
                "sample_id": str(sample_id),
                "resistance_risk_score": round(float(prob), 4),
                "risk_category": "High Risk (EMT-associated Early Progression)" if pred == 1 else "Low Risk / Durable Response",
                "features_detected": len(matched_genes),
                "features_imputed": len(missing_genes)
            })

        return {
            "total_samples_analyzed": len(results),
            "signature_coverage_pct": round((len(matched_genes) / max(1, len(FEATURE_GENES))) * 100, 2),
            "predictions": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True if port == 8000 else False)