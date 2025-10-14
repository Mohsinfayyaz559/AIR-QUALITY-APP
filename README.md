# 🌍 Air Quality Prediction System  

This project provides a **complete end-to-end Air Quality Prediction System** built using **Streamlit**, **FastAPI**, and hosted on **Hugging Face Spaces**.  
It enables real-time AQI (Air Quality Index) forecasting and automated monthly retraining to keep the model up-to-date with the latest data.  

---

## 🚀 Live Applications  

### 🖥️ **User Interface (Streamlit App)**  
🔗 **[Air Quality App – Live on Hugging Face](https://huggingface.co/spaces/mk12rule/Air_quality_app)**  

This is the main web application where users can:  
- Upload or view air quality data.  
- Visualize pollutant trends interactively.  
- Get AQI predictions in real time.  

### ⚙️ **API Backend (FastAPI Service)**  
🔗 **[Air Quality API – Live Endpoint](https://mk12rule-air-quality-api.hf.space)**  

This API powers the Streamlit UI and supports external integrations.  
Endpoints include:  
- `/predict` → Generate air quality predictions.  
- `/retrain` → Trigger model retraining.  
- `/` → Check if API is working.  

---

## 🤖 Automated Model Retraining  

- The model **automatically retrains every month** using a **GitHub Actions workflow**.  
- Retraining is triggered via a POST request to the API `/retrain` endpoint.    
- This ensures the model continuously learns from new data without manual updates.  

---

## 💾 Persistent Storage  

- Model files and cached datasets are stored in the **Hugging Face repository storage**.  
- This allows the model and dataset to retain state between restarts or deployments.  
- Unlike ephemeral storage (which resets when the space sleeps or restarts), this persistent storage ensures:  
  - models and data-sets are saved and no data is lossed .
  - with time data-set will grow and model will be enhanced    

---

## 🧠 Tech Stack  

| Component | Technology |
|------------|-------------|
| Frontend | Streamlit |
| Backend | FastAPI |
| Model | XGBoost |
| Hosting | Hugging Face Spaces |
| Automation | GitHub Actions |
| Storage | Hugging Face Repo (Persistent storage of both dataset and models) |

---

## ⚙️ How It Works  

1. **Streamlit Frontend** interacts with the **FastAPI backend** via REST calls.  
2. **FastAPI API** handles prediction and retraining requests.  
3. **Model retraining** runs monthly via GitHub Actions → triggers `/retrain`.  
4. Updated models are stored persistently in the Hugging Face repository.  

---

## 📈 Project Highlights  

- 🧩 Modular architecture with separate UI and API Spaces.  
- 🔄 Fully automated retraining workflow.  
- 💾 Persistent cache for efficient model loading.  
- ☁️ Deployed on Hugging Face Spaces – no external servers required.  
- 🔍 Transparent open-source structure for community improvements.  

---

## 📫 Contact  

**Author:** Mohsin  
**Role:** Engineer  
📍 [GitHub Profile](https://github.com/mk12rule)  

---

> _This project demonstrates a scalable, reproducible approach to deploying ML systems with automated lifecycle management, using free open tools like Hugging Face Spaces and GitHub Actions._

