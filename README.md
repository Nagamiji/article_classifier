# 🗄 Database

The system uses **PostgreSQL** to store all predictions and user feedback. The database is containerized with Docker, so it is automatically created and ready to use when the containers start.

## Table: `predictions`

| Column            | Type                | Description                                              |
|-------------------|---------------------|----------------------------------------------------------|
| id                | SERIAL PRIMARY KEY  | Unique ID for each prediction                            |
| text_input        | TEXT                | The article text submitted by the user                   |
| label_classified  | VARCHAR(255)        | The predicted topic/class from the ML model              |
| feedback          | BOOLEAN             | User feedback: TRUE = Good, FALSE = Bad, NULL = Not given|
| created_at        | TIMESTAMP           | Timestamp when the prediction was created                |

---

## How It Works

### 1. Dockerized PostgreSQL

The database runs in its own Docker container defined in `docker-compose.yml`. On first startup, PostgreSQL automatically executes the `init.sql` file to create the database and table.

### 2. Environment Variables

`.env` contains database credentials:

```env
POSTGRES_DB=XXXXX
POSTGRES_USER=XXXX
POSTGRES_PASSWORD=XXXX
DATABASE_URL=XXXX
```

### 3. Feedback Logic

- `TRUE` → user marked prediction as Good 👍
- `FALSE` → user marked prediction as Bad 👎
- `NULL` → no feedback provided

### 4. Persistent Storage

Data is persisted using a Docker volume to ensure predictions are not lost if the container restarts.

---

## Commands to Run & Verify

### 1. Start the database

```bash
docker-compose up -d
```

### 2. Check logs

```bash
docker logs article_postgres
```

### 3. Verify schema

```bash
docker exec -it article_postgres psql -U article_user -d article_db
\dt
\d predictions;
```

This confirms that the table `predictions` is created and ready for backend integration.

---