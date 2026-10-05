# Student Data Engineering Project

مشروع Data Engineering يطبق مجموعة من Data Pipelines مستقلة على عدة مصادر بيانات.

## Data Sources

يحتوي المشروع على أربعة مصادر بيانات مستقلة:

1. CSV
2. SQLite
3. REST API
4. MongoDB

كل مصدر يمتلك Data Pipeline مستقلة خاصة به.

---

## Project Architecture

```text
CSV Source
   ↓
CSV Pipeline
   ↓
Processed Data

SQLite Source
   ↓
SQLite Pipeline
   ↓
Analytical Dataset

REST API
   ↓
API Pipeline
   ↓
Processed Data

MongoDB
   ↓
MongoDB Pipeline
   ↓
Processed Data