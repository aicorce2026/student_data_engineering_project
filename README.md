# مشروع بيانات الطلاب

هذا المشروع سويته كتطبيق عملي على اللي درسناه في مادة Data Engineering.

الفكرة ببساطة إني أخذت أكثر من مصدر بيانات، وكل مصدر سويت له Pipeline لحاله، وبعدها جمعت تشغيلهم كلهم من ملف واحد.

المصادر اللي استخدمتها هي:

- CSV
- SQLite
- API
- MongoDB

وكل واحد منهم له طريقة مختلفة شوي في القراءة والمعالجة.

---

## الفكرة العامة

الفكرة الأساسية للمشروع ماشية بالشكل هذا:

Raw Data  
↓  
قراءة البيانات  
↓  
فحص البيانات  
↓  
تنظيف وتحويل  
↓  
Validation  
↓  
Processed Data  

أنا حاولت أحافظ على البيانات الأصلية زي ما هي، وما أعدلش عليها مباشرة.

البيانات الخام موجودة داخل:

data/raw/

والبيانات بعد المعالجة موجودة داخل:

data/processed/

يعني لو حصل أي غلط أقدر أرجع للبيانات الأصلية وأشغل الـ Pipeline من جديد.

---

# 1. CSV Pipeline

الملف الأصلي موجود هنا:

data/raw/csv/students_raw.csv

في هذا الجزء استخدمت Pandas.

أول حاجة قرأت الملف باستخدام:

pd.read_csv()

بعدها فحصت البيانات عشان أعرف إذا فيه:

- قيم ناقصة
- قيم غلط
- صفوف مكررة
- Student ID مكرر
- مشاكل في أنواع البيانات

بعدها حولت الأعمدة الرقمية باستخدام:

pd.to_numeric()

واستخدمت:

errors="coerce"

عشان لو فيه قيمة ما تنفعش تتحول لرقم تتحول إلى Missing Value بدل ما البرنامج يوقف.

بعدها نظفت البيانات.

مثلاً:

- العمر لازم يكون بين 16 و 80
- GPA لازم يكون بين 0 و 4
- Attendance لازم يكون بين 0 و 100

أي قيمة خارج الحدود هذه اعتبرتها قيمة غلط.

بعدها عالجت القيم الناقصة باستخدام Median.

واستخدمت:

drop_duplicates()

عشان أحذف التكرار.

ونظفت النصوص باستخدام:

str.strip()

وكمان رتبت أسماء المدن باستخدام:

str.title()

---

## الأعمدة الجديدة

بعد التنظيف أضفت أعمدة جديدة تساعد في التحليل.

### attendance_rate

حولت نسبة الحضور من رقم مثل:

92

إلى:

0.92

### performance_score

حولت GPA إلى نسبة مئوية.

مثلاً:

3.5 / 4 * 100

### academic_status

قسمت الطلاب إلى:

High Performer

أو:

Regular

باستخدام GPA والحضور.

---

## نتيجة CSV

الناتج ينحفظ هنا:

data/processed/csv/students_clean.csv

وكمان فيه تقرير بسيط هنا:

reports/csv_quality_report.txt

---

# 2. SQLite Pipeline

في هذا الجزء استخدمت قاعدة بيانات SQLite.

الملف الأصلي موجود هنا:

data/raw/sqlite/students_original.db

قاعدة البيانات فيها أكثر من جدول، من ضمنها:

- students
- courses
- enrollments
- assessments

هنا ركزت أكثر على SQL.

استخدمت:

- SELECT
- JOIN
- GROUP BY
- CTE
- CASE
- RANK

---

## كيف اشتغل SQLite Pipeline

أول حاجة اتصلت بقاعدة البيانات باستخدام:

sqlite3

بعدها استخدمت SQL عشان أربط الجداول مع بعض.

العلاقة تقريباً كذا:

students  
↓  
enrollments  
↓  
assessments  

واستخدمت JOIN عشان أوصل بيانات الطالب بدرجاته.

بعدها استخدمت:

GROUP BY

عشان أحسب النتائج لكل طالب.

واستخدمت:

COUNT(DISTINCT ...)

عشان أعرف كم مقرر عند كل طالب.

---

## CTE

استخدمت CTE عشان أقسم الاستعلام إلى مراحل واضحة بدل ما يكون استعلام واحد طويل ومعقد.

المرحلة الأولى تحسب بيانات الطالب ودرجاته.

والمرحلة الثانية تحدد مستوى الطالب.

---

## CASE

استخدمت CASE عشان أصنف الطلاب إلى:

- Excellent
- Very Good
- Good
- Pass
- Weak

حسب متوسط الدرجة.

---

## RANK

استخدمت:

RANK() OVER()

عشان أعمل ترتيب للطلاب حسب average_score.

في البيانات الموجودة عندي كل الطلاب طلع لهم نفس average_score وهو 87، عشان كذا كلهم أخذوا Rank = 1.

هذا مش خطأ في الكود، هذا بسبب البيانات نفسها.

---

## نتيجة SQLite

الناتج ينحفظ هنا:

data/processed/sqlite/student_analytics.csv

والتقرير هنا:

reports/sqlite_quality_report.txt

---

# 3. API Pipeline

في هذا الجزء جبت البيانات من API.

استخدمت:

https://jsonplaceholder.typicode.com/users

واستخدمت مكتبة:

requests

عشان أرسل GET Request.

---

## طريقة العمل

استخدمت:

requests.get()

وحطيت:

timeout=10

عشان البرنامج ما يظلش معلق لو الموقع ما رد.

وبعدها استخدمت:

raise_for_status()

عشان لو رجع Status Code فيه مشكلة يطلع Error.

بعدها حولت الرد إلى JSON باستخدام:

response.json()

---

## Raw API Data

قبل ما أعدل البيانات حفظتها أولاً كـ JSON هنا:

data/raw/api/users_raw.json

هذا عشان أحافظ على البيانات اللي جات من المصدر قبل المعالجة.

---

## Transform

الـ API يرجع بيانات كثيرة ومتداخلة.

أنا ما أخذتش كل شيء.

أخذت فقط الحقول اللي احتاجها:

- user_id
- name
- username
- email
- city

والـ city كانت داخل:

address

عشان كذا طلعتها من Nested JSON.

بعدها حولت البيانات إلى Pandas DataFrame.

---

## Validation

تأكدت من:

- إن البيانات مش فاضية
- user_id موجود
- user_id ما يتكرر
- name موجود
- الأعمدة المطلوبة موجودة

---

## نتيجة API

الناتج هنا:

data/processed/api/users_clean.csv

والتقرير هنا:

reports/api_quality_report.txt

---

# 4. MongoDB Pipeline

هذا الجزء مختلف شوي عن البقية لأن MongoDB تتعامل مع Documents بدل Tables.

استخدمت بيانات طلاب فيها:

- Personal Information
- Academic Information
- Skills
- Projects

البيانات فيها Nested Documents و Arrays.

---

## Raw MongoDB Data

البيانات الأصلية موجودة في:

students_raw

وعندي كمان نسخة JSON هنا:

data/raw/mongodb/students_mongodb_raw.json

البيانات الخام فيها أخطاء مقصودة عشان أطبق عليها التنظيف.

مثلاً:

- Student ID مكرر
- GPA أكبر من 4
- Age غلط
- Attendance أكبر من 100
- Missing Values
- بعض الأرقام مكتوبة كنص
- أسماء المدن مكتوبة بأشكال مختلفة

---

# CRUD

طبقت CRUD كاملة.

CRUD معناها:

Create  
Read  
Update  
Delete  

لكن بدل ما أجرب Update و Delete على البيانات الأصلية، استخدمت Collection ثانية خاصة بالتجربة:

students_crud_demo

عشان ما أغيرش Raw Data.

---

## Create

استخدمت:

insert_one()

وضفت طالب Demo.

---

## Read

استخدمت:

find_one()

عشان أقرأ الطالب.

---

## Update

استخدمت:

update_one()

وغيرت GPA.

---

## Delete

استخدمت:

delete_one()

وبعدها حذفت طالب الـ Demo.

بهذا طبقت CRUD بدون ما ألمس البيانات الخام الأصلية.

---

# MongoDB Queries

سويت أكثر من Query.

مثلاً جبت الطلاب اللي GPA حقهم أكبر أو يساوي 3.5.

واستخدمت:

$gte

وكمان جبت الطلاب اللي عندهم Python داخل skills.

لأن skills عبارة عن Array.

---

# Aggregation

استخدمت MongoDB Aggregation.

وعملت Group حسب المدينة.

استخدمت:

$group

وبعدها:

$sort

عشان أشوف عدد الطلاب في كل مدينة.

قبل التنظيف ظهرت أسماء المدن بأكثر من شكل مثل:

Sanaa

sanaa

وهذا يوضح ليش تنظيف البيانات مهم.

---

# MongoDB إلى Pandas

بعد ما قرأت البيانات من MongoDB استخدمت:

pd.json_normalize()

عشان أحول الـ Nested Documents إلى DataFrame عادي.

مثلاً:

personal.name

personal.city

academic.gpa

academic.attendance

---

# تنظيف MongoDB

استخدمت نفس فكرة التنظيف اللي استخدمتها في CSV.

حولت الأعمدة الرقمية باستخدام:

pd.to_numeric()

وبعدها تأكدت من النطاقات.

Age:

16 إلى 80

GPA:

0 إلى 4

Attendance:

0 إلى 100

والقيم الغلط تحولت إلى Missing Values.

بعدها عالجتها باستخدام Median.

وحذفت Student ID المكرر.

---

# Feature بسيطة

أضفت عمود:

python_skill

القيمة تكون:

True

لو الطالب عنده Python ضمن skills.

وتكون:

False

لو ما عندهش.

---

# نتيجة MongoDB

النتيجة النهائية موجودة هنا:

data/processed/mongodb/students_clean.csv

والتقرير هنا:

reports/mongodb_quality_report.txt

---

# تشغيل المشروع كامل

عندي ملف رئيسي:

main.py

وظيفته بس يشغل كل الـ Pipelines بالترتيب.

الترتيب هو:

CSV  
↓  
SQLite  
↓  
API  
↓  
MongoDB Seed + CRUD  
↓  
MongoDB Pipeline  

لتشغيل المشروع:

python main.py

إذا كل شيء اشتغل صح تظهر الرسالة:

All pipelines completed successfully.

---

# قبل التشغيل

لازم تكون MongoDB شغالة محلياً.

وبعدها تثبت المكتبات:

pip install -r requirements.txt

المكتبات الأساسية المستخدمة:

- pandas
- numpy
- requests
- pymongo

sqlite3 تجي أساساً مع Python.

---

# ترتيب الملفات

المشروع تقريباً مرتب بالشكل هذا:

student_data_engineering_project/

data/
    raw/
    processed/

pipelines/
    csv_pipeline/
    sqlite_pipeline/
    api_pipeline/
    mongodb_pipeline/

reports/

main.py

requirements.txt

README.md

---

# ليش خليت كل Pipeline لحالها؟

لأن كل مصدر بيانات يختلف عن الثاني.

CSV يحتاج قراءة وتنظيف باستخدام Pandas.

SQLite يحتاج SQL.

API يحتاج Requests و JSON.

MongoDB يحتاج PyMongo ويتعامل مع Documents و Arrays.

عشان كذا فصلتهم عن بعض، وفي الأخير خليت main.py يشغلهم كلهم.

---

# ملاحظة

حاولت أخلي المشروع بسيط وواضح، وما أضيفش أشياء ما احتاجهاش.

الهدف عندي مش إني أكبر المشروع، الهدف إني أطبق الأشياء اللي درسناها وأفهم كل مرحلة كيف تشتغل.