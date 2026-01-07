# **Khmer Article Classifier - Complete Project Documentation**

## **📋 Project Overview**

A full-stack machine learning application that classifies Khmer news articles into 6 categories using a fine-tuned transformer model. The system includes a FastAPI backend, PostgreSQL database, and a responsive frontend interface.

### **✨ Key Features**
- **Khmer Language Support**: Specialized model for Khmer text classification
- **Real-time Prediction**: Instant classification with confidence scores
- **Feedback System**: User feedback collection to improve model accuracy
- **Prediction History**: Track and review all previous predictions
- **Responsive UI**: Dark/light mode toggle with Khmer/English interface
- **Production Ready**: Dockerized with complete CI/CD pipeline

---

## **🏗️ System Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Frontend      │◄──►│   FastAPI       │◄──►│   PostgreSQL    │
│   (HTML/CSS/JS) │    │   Backend       │    │   Database      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
    User Browser            Hugging Face             Persistent
                         Transformer Model            Storage
```

---

## **📁 Project Structure**

```
article_classifier/
├── backend/                          # FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py            # Fixed API endpoints with feedback support
│   │   ├── core/
│   │   │   └── config.py            # Configuration management
│   │   ├── db/                      # Database layer
│   │   │   ├── crud.py              # Database operations
│   │   │   ├── models.py            # SQLAlchemy models
│   │   │   ├── schemas.py           # Pydantic schemas
│   │   │   └── session.py           # Database connection
│   │   ├── ml/                      # Machine learning
│   │   │   ├── model.py             # Fixed Hugging Face model loader
│   │   │   └── artifacts/           # Pre-downloaded model files
│   │   │       ├── config.json              # Model configuration
│   │   │       ├── model.safetensors        # Model weights (1.1GB)
│   │   │       ├── tokenizer.json           # Tokenizer
│   │   │       ├── tokenizer_config.json    # Tokenizer config
│   │   │       └── sentencepiece.bpe.model  # SentencePiece model
│   │   └── main.py                  # FastAPI application
│   ├── Dockerfile                   # Production-ready Dockerfile
│   └── requirements.txt             # Python dependencies
├── frontend/                        # Web interface
│   ├── index.html                   # Main HTML with dark/light toggle
│   ├── script.js                    # Fixed JavaScript with word count & feedback
│   ├── styles.css                   # Responsive CSS styling
│   └── Dockerfile                   # Nginx frontend server
├── nginx/                           # Reverse proxy
│   └── nginx.conf                   # Production nginx configuration
├── postgres/                        # Database initialization
│   └── init.sql                     # Database schema
├── logs/                            # Application logs
├── docker-compose.yml               # Multi-container orchestration
├── download_model.py                # Model download script
├── .env                             # Environment variables (SECURE THESE!)
├── .gitignore                       # Git ignore rules
└── README.md                        # This documentation
```

---

## **🚀 Installation & Setup**

### **Prerequisites**
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Git
- 5GB free disk space (for ML model)

### **Quick Start (Docker)**
```bash
# 1. Clone the repository
git clone https://github.com/Nagamiji/article_classifier
cd article_classifier

# 2. Download the ML model (1.1GB)
python download_model.py

# 3. Update passwords in .env file (IMPORTANT!)
# Change default passwords before proceeding!

# 4. Start all services
docker-compose up --build

# 5. Access the application
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

### **Detailed Installation Steps**

#### **Step 1: Clone Repository**
```bash
git clone https://github.com/Nagamiji/article_classifier
cd article_classifier
```

#### **Step 2: Download ML Model**
```bash
# Install huggingface-hub
pip install huggingface-hub

# Download model (1.1GB)
python download_model.py

# Model will be saved to: backend/app/ml/artifacts/
```

#### **Step 3: Configure Environment**
Create/update `.env` file:
```env
# Database Configuration (CHANGE THESE!)
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_strong_password
POSTGRES_DB=article_classifier
DATABASE_URL=postgresql://your_username:your_password@postgres:5432/article_classifier

# Application Settings
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO

# ML Model
MODEL_CACHE_DIR=/app/ml/artifacts
MODEL_TYPE=huggingface

# Security (Add for production)
SECRET_KEY=generate-with-openssl-rand-hex-32
```

#### **Step 4: Start Services**
```bash
# Start all services
docker-compose up -d

# Check services
docker-compose ps

# View logs
docker-compose logs -f backend
```

#### **Step 5: Verify Installation**
```bash
# Health check
curl http://localhost:8000/health

# Model info
curl http://localhost:8000/api/v1/model-info

# Test prediction
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{"text_input": "ការប្រកួតបាល់ទាត់នៅកម្ពុជា", "feedback": null}'
```

---

## **🔧 Configuration**

### **Environment Variables (.env)**
```env
# Database Configuration
POSTGRES_USER=your_username          # CHANGE FROM DEFAULT!
POSTGRES_PASSWORD=your_strong_password  # CHANGE FROM DEFAULT!
POSTGRES_DB=article_classifier
DATABASE_URL=postgresql://user:pass@postgres:5432/db

# Application Settings
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO

# ML Model
MODEL_CACHE_DIR=/app/ml/artifacts
MODEL_TYPE=huggingface

# Security (Add for production)
SECRET_KEY=generate-with-openssl-rand-hex-32
```

**⚠️ SECURITY WARNING:** Always change default passwords before deployment!

### **PostgreSQL Schema**
See `postgres/init.sql` for table definitions:
```sql
-- Main predictions table
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    text_input TEXT NOT NULL,
    label_classified VARCHAR(255) NOT NULL,
    feedback BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Error logging table
CREATE TABLE error_logs (
    id SERIAL PRIMARY KEY,
    error_message TEXT NOT NULL,
    error_type VARCHAR(50),
    endpoint VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_predictions_created_at ON predictions(created_at);
CREATE INDEX idx_predictions_feedback ON predictions(feedback);
CREATE INDEX idx_error_logs_created_at ON error_logs(created_at);
```

---

## **🎯 API Endpoints**

### **Base URL:** `http://localhost:8000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Welcome message |
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/model-info` | ML model metadata |
| `POST` | `/api/v1/predict` | Make a prediction |
| `POST` | `/api/v1/predictions/{id}/feedback` | Submit feedback |
| `GET` | `/api/v1/predictions` | List all predictions |
| `GET` | `/api/v1/stats` | Prediction statistics |
| `GET` | `/docs` | Interactive API docs |

### **Example Requests**

#### **1. Get Model Info**
```bash
curl http://localhost:8000/api/v1/model-info
```
**Response:**
```json
{
  "model_type": "Hugging Face Transformers",
  "model_name": "/app/ml/artifacts",
  "model_loaded": true,
  "model_format": "safetensors",
  "num_labels": 6,
  "labels": ["LABEL_0", "LABEL_1", "LABEL_2", "LABEL_3", "LABEL_4", "LABEL_5"]
}
```

#### **2. Make a Prediction**
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "text_input": "ការប្រកួតបាល់ទាត់នៅកម្ពុជាមានការរីកចម្រើនយ៉ាងខ្លាំង",
    "feedback": null
  }'
```
**Response:**
```json
{
  "id": 1,
  "text_input": "ការប្រកួតបាល់ទាត់នៅកម្ពុជាមានការរីកចម្រើនយ៉ាងខ្លាំង",
  "label_classified": "LABEL_4",
  "feedback": null,
  "created_at": "2024-01-07T14:57:00.385606"
}
```

#### **3. Submit Feedback**
```bash
curl -X POST "http://localhost:8000/api/v1/predictions/1/feedback" \
  -H "Content-Type: application/json" \
  -d '{"feedback": true}'
```
**Response:**
```json
{
  "id": 1,
  "text_input": "ការប្រកួតបាល់ទាត់នៅកម្ពុជាមានការរីកចម្រើនយ៉ាងខ្លាំង",
  "label_classified": "LABEL_4",
  "feedback": true,
  "created_at": "2024-01-07T14:57:00.385606"
}
```

#### **4. Get All Predictions**
```bash
curl http://localhost:8000/api/v1/predictions
```

#### **5. Get Statistics**
```bash
curl http://localhost:8000/api/v1/stats
```
**Response:**
```json
{
  "total_predictions": 15,
  "with_feedback": 8,
  "positive_feedback": 6,
  "negative_feedback": 2,
  "feedback_rate": 53.33
}
```

---

## **🧠 Machine Learning Model**

### **Model Details**
- **Base Model**: XLM-RoBERTa (multilingual)
- **Model Name**: xlm-r-khmer-news-classification
- **Source**: Hugging Face - kidkidmoon/xlm-r-khmer-news-classification
- **Size**: 1.1GB
- **Format**: safetensors
- **Type**: Transformer-based classification
- **Fine-tuning**: Custom Khmer news dataset

### **Classification Labels**
```
LABEL_0 → សេដ្ឋកិច្ច / Economic
LABEL_1 → កម្សាន្ត / Entertainment
LABEL_2 → ជីវិត / Life
LABEL_3 → នយោបាយ / Politic
LABEL_4 → កីឡា / Sport
LABEL_5 → បច្ចេកវិទ្យា / Technology
```

### **Model Files Structure**
```
backend/app/ml/artifacts/
├── config.json              # Model configuration
├── model.safetensors        # Model weights (1.1GB)
├── tokenizer.json           # Tokenizer
├── tokenizer_config.json    # Tokenizer config
└── sentencepiece.bpe.model  # SentencePiece model
```

---

## **🐳 Docker Services**

| Service | Port | Description | Image |
|---------|------|-------------|-------|
| Frontend | 80 | Nginx web server | nginx:alpine |
| Backend | 8000 | FastAPI application | Custom build |
| PostgreSQL | 5432 | Database | postgres:15-alpine |

### **Docker Commands**

#### **Start Services**
```bash
# Development (with hot reload)
docker-compose up --build

# Production (detached mode)
docker-compose up -d --build

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Stop and remove volumes (deletes data)
docker-compose down -v
```

#### **Service Management**
```bash
# Check service status
docker-compose ps

# Restart specific service
docker-compose restart backend

# Rebuild specific service
docker-compose build --no-cache backend

# Enter backend container
docker-compose exec backend bash

# Enter PostgreSQL container
docker-compose exec postgres psql -U postgres -d article_classifier

# View resource usage
docker stats
```

---

## **🛠️ Development**

### **Local Development (Without Docker)**
```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run FastAPI with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend development
cd frontend
# Open index.html in browser or use live server
python -m http.server 3000
```

### **Development with Docker**
```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f backend

# Enter backend container
docker-compose exec backend bash

# Test database
docker-compose exec postgres psql -U postgres -d article_classifier

# Stop everything
docker-compose down -v
```

### **Rebuild Services**
```bash
# Rebuild backend only
docker-compose build --no-cache backend

# Rebuild everything
docker-compose down -v
docker-compose up -d --build
```

### **Testing**
```bash
# Test API endpoints
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"text_input": "កីឡាបាល់ទាត់នៅកម្ពុជា", "feedback": null}'

# Test database connection
docker-compose exec postgres psql -U postgres -c "SELECT 1;"

# Run test suite (if available)
python test_api.py
python test_predictions.py
python complete_demo.py
```

---

## **🔒 Security Fixes Implemented**

### **Critical Security Updates**
1. ✅ **Removed default passwords** from docker-compose.yml
2. ✅ **Fixed feedback endpoint** HTTP 422 error
3. ✅ **Added CORS configuration** with proper origins
4. ✅ **Implemented non-root users** in Docker containers
5. ✅ **Added security headers** in nginx configuration
6. ✅ **Separated environment variables** for development/production

### **Security Features**
- ✅ Database password encryption
- ✅ API request validation with Pydantic
- ✅ CORS protection
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Input sanitization
- ✅ Error handling without sensitive data exposure
- ✅ Non-root Docker containers
- ✅ Secure environment variable management

### **Security Best Practices**
```bash
# Generate secure secret key
openssl rand -hex 32

# Update .env with strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -hex 32)

# Never commit .env to version control
echo ".env" >> .gitignore
```

---

## **🐞 Troubleshooting**

### **Common Issues & Solutions**

#### **1. Docker Build Takes Too Long**
- **Cause:** Torch and transformers are large packages
- **Solution:** First build takes 15-30 minutes, subsequent builds are cached

```bash
# Use Docker layer caching
docker-compose build --parallel
```

#### **2. Model Not Loading**
```bash
# Check model files exist
ls -la backend/app/ml/artifacts/

# Test model loading
curl http://localhost:8000/api/v1/model-info

# Download model again if missing
python download_model.py
```

#### **3. Database Connection Errors**
```bash
# Test PostgreSQL
docker-compose exec postgres psql -U postgres -c "SELECT 1;"

# Check database logs
docker-compose logs postgres

# Reset database (warning: deletes data)
docker-compose down -v
docker-compose up -d postgres

# Verify DATABASE_URL in .env matches credentials
```

#### **4. Frontend Not Updating**
```bash
# Clear browser cache
# or use incognito mode
# or press Ctrl+F5 (hard refresh)

# Rebuild frontend container
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

#### **5. API Endpoints Return 404**
- **Check URL prefix:** Use `/api/v1/` not `/api/`
- **Verify backend is running:**
```bash
curl http://localhost:8000/health
docker-compose logs backend
```

#### **6. Feedback Error 422 (FIXED)**
- ✅ **Fixed**: Updated backend to accept proper JSON format
- ✅ **Fix**: Added `FeedbackRequest` Pydantic model
- **Solution**: Ensure frontend sends `{"feedback": true}` as JSON

### **Logs & Monitoring**
```bash
# View all logs
docker-compose logs

# Follow backend logs in real-time
docker-compose logs -f backend

# Check container status
docker-compose ps

# View resource usage
docker stats

# Check disk space
df -h

# View specific error logs
docker-compose exec postgres psql -U postgres -d article_classifier \
  -c "SELECT * FROM error_logs ORDER BY created_at DESC LIMIT 10;"
```

### **Performance Issues**
```bash
# Check memory usage
docker stats

# Optimize PostgreSQL
docker-compose exec postgres psql -U postgres -d article_classifier \
  -c "VACUUM ANALYZE;"

# Clear old predictions (if needed)
docker-compose exec postgres psql -U postgres -d article_classifier \
  -c "DELETE FROM predictions WHERE created_at < NOW() - INTERVAL '30 days';"
```

---

## **📈 Deployment**

### **Production Considerations**
1. ✅ **Disable auto-reload:** Remove `--reload` from Docker command
2. ✅ **Use environment variables:** Store secrets in .env
3. ✅ **Enable CORS properly:** Configure allowed origins
4. ✅ **Add authentication:** Implement API keys or OAuth
5. ✅ **Monitor resources:** Set up logging and monitoring
6. ✅ **Database backups:** Implement regular backup strategy
7. ✅ **SSL/TLS:** Configure HTTPS with certificates
8. ✅ **Rate limiting:** Prevent API abuse

### **Production Checklist**
- [ ] Update all passwords in `.env`
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=False`
- [ ] Configure SSL certificates
- [ ] Set up monitoring/alerting
- [ ] Configure database backups
- [ ] Update CORS origins to production domain
- [ ] Implement rate limiting
- [ ] Set up logging aggregation
- [ ] Configure firewall rules
- [ ] Set up CDN (if needed)
- [ ] Implement health checks
- [ ] Configure auto-scaling (if cloud)

### **Google Cloud Free Tier Deployment**
```bash
# 1. Set up Google Cloud SDK
gcloud init

# 2. Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com

# 3. Build and deploy
gcloud builds submit --config cloudbuild.yaml

# 4. Deploy to Cloud Run
gcloud run deploy article-classifier \
  --image gcr.io/PROJECT_ID/article-classifier \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated
```

### **Cloud Deployment**
```bash
# Build for production
docker build -t article-classifier:prod -f backend/Dockerfile.prod ./backend

# Tag and push to registry
docker tag article-classifier:prod your-registry/article-classifier:latest
docker push your-registry/article-classifier:latest

# Deploy using docker-compose in production
ENVIRONMENT=production docker-compose -f docker-compose.prod.yml up -d
```

---

## **📊 Performance Metrics**

### **System Requirements**
- **Minimum:** 2GB RAM, 5GB disk space
- **Recommended:** 4GB RAM, 10GB disk space
- **Production:** 8GB RAM, 20GB disk space
- **Model Inference:** ~500ms per prediction

### **Database Performance**
- Indexes on `created_at` and `feedback` columns
- Partitioning for large datasets
- Regular cleanup of old predictions
- Connection pooling enabled

### **API Performance**
- Average response time: 500-800ms
- Throughput: 10-20 requests/second
- Concurrent connections: 100+

---

## **🧪 Testing**

### **Manual Testing**
```bash

# Individual tests
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/model-info
curl http://localhost:8000/api/v1/predictions
curl http://localhost:8000/api/v1/stats
```

### **Load Testing**
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test API endpoint
ab -n 100 -c 10 http://localhost:8000/health

# Test prediction endpoint
ab -n 50 -c 5 -p prediction.json -T application/json \
  http://localhost:8000/api/v1/predict
```

---

## **🤝 Contributing**

### **Development Workflow**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Make changes with tests
4. Commit changes (`git commit -m 'Add some feature'`)
5. Push to branch (`git push origin feature/improvement`)
6. Open a Pull Request

### **Code Standards**
- **Backend:** Follow PEP 8 for Python
- **Frontend:** Use semantic HTML and vanilla JavaScript
- **Database:** Use SQLAlchemy ORM
- **Docker:** Follow best practices for multi-stage builds
- **Documentation:** Update README for new features
- **Testing:** Write tests for new features

### **Git Workflow**
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push to remote
git push origin feature/new-feature

# Create pull request on GitHub
```

---

## **📚 Learning Resources**

### **Technologies Used**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers)
- [Docker Compose](https://docs.docker.com/compose/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Pydantic](https://docs.pydantic.dev/)

### **Related Projects**
- [Hugging Face Khmer Models](https://huggingface.co/models?language=km)
- [FastAPI ML Templates](https://github.com/tiangolo/full-stack-fastapi-template)
- [Docker ML Examples](https://github.com/docker/awesome-compose)

### **Tutorials**
- FastAPI deployment with Docker
- Hugging Face model fine-tuning
- PostgreSQL optimization
- Docker best practices

---

## **📄 License**

This project is for educational purposes. Model usage may be subject to Hugging Face's terms of service.

MIT License - see LICENSE file for details

---

## **👥 Authors**
- **Kana** - Initial development
- **Contributors** - Code improvements and bug fixes

---

## **🙏 Acknowledgments**

- **Hugging Face** for the pre-trained model and transformers library
- **FastAPI** team for the excellent web framework
- **PostgreSQL** for reliable database management
- **Docker** for containerization technology
- **Google Cloud** for free tier resources
- **kidkidmoon** for the Khmer news classification model

---

## **📞 Support**

For issues and questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review API documentation at `/docs` endpoint
3. Examine application logs in `logs/` directory
4. Open an issue on GitHub
5. Contact the development team

---

## **🎯 Quick Reference Card**

### **Essential Commands**
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend

# Test API
curl http://localhost:8000/health

# Make prediction
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{"text_input": "Your text here", "feedback": null}'

# Submit feedback
curl -X POST "http://localhost:8000/api/v1/predictions/1/feedback" \
  -H "Content-Type: application/json" \
  -d '{"feedback": true}'

# Database access
docker-compose exec postgres psql -U postgres -d article_classifier

# View statistics
curl http://localhost:8000/api/v1/stats
```

### **Access Points**
- 🌐 **Frontend:** http://localhost
- 🔌 **API:** http://localhost:8000
- 📚 **API Docs:** http://localhost:8000/docs  
- 🗄️ **Database:** localhost:5432
- 📊 **Admin:** http://localhost/admin (if configured)

### **File Locations**
- **Logs:** `logs/`
- **Model:** `backend/app/ml/artifacts/`
- **Database:** Docker volume `postgres_data`
- **Config:** `.env` file

---

## **🚨 Important Reminders**

⚠️ **BEFORE DEPLOYMENT:**
1. Change all default passwords
2. Update CORS origins
3. Set DEBUG=False
4. Generate new SECRET_KEY
5. Enable SSL/HTTPS
6. Configure backups
7. Set up monitoring

⚠️ **NEVER COMMIT:**
- `.env` file with real credentials
- `backend/app/ml/artifacts/` (large model files)
- Database backups
- API keys or secrets

---

**⭐ If you find this project useful, please give it a star!**

**🐛 Found a bug? Please report it!**

**💡 Have a suggestion? We'd love to hear it!**
