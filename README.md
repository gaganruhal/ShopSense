# 🛍️ ShopSense 2.0 — E-commerce Sales Analytics Dashboard

**ShopSense 2.0** is an interactive e-commerce data analytics dashboard built using Python, Pandas, SQL, SQLite and Streamlit.

It helps users upload e-commerce datasets, clean data, perform SQL analysis, identify business insights and generate downloadable reports through a single dashboard.

The project focuses on making data analysis easier, more interactive and useful for understanding business performance.

## 🚀 Key Features

### 📂 1. CSV Upload & Data Preview

* Upload your own CSV datasets.
* Preview uploaded data.
* Explore dataset columns and records.
* Work with your active dataset.

### 🧹 2. Data Cleaning Workspace

* Identify missing values.
* Detect duplicate records.
* Explore data quality issues.
* Perform data cleaning operations.

### 💻 3. SQL Workspace

* Run SQL queries on the active dataset.
* Explore and analyze data using SQL.
* View query results directly in the dashboard.

### 📊 4. Data Quality Report

* Analyze missing values and duplicate records.
* View column-wise data quality information.
* Understand the overall condition of your dataset.

### 💡 5. Smart Business Insights

* Sales channel performance analysis.
* Customer analysis and customer snapshots.
* Top 10 customers by revenue.
* Rule-based business observations.
* Downloadable customer and sales channel reports.

### 📥 6. Export Center

* Download the currently filtered dataset.
* Export category and monthly summaries.
* Export product, customer and sales channel reports.
* Download column quality profiles.
* Download all reports together in a ZIP file.

### 🎨 7. User Interface

* Interactive Streamlit dashboard.
* Light and Dark appearance modes.
* Responsive layout for smaller screens.
* Navigation across different analytics workspaces.

## 🛠️ Tech Stack

| Technology | Purpose                        |
| ---------- | ------------------------------ |
| Python     | Core programming               |
| Pandas     | Data manipulation and analysis |
| SQL        | Data querying                  |
| SQLite     | Database management            |
| Streamlit  | Interactive dashboard          |
| Matplotlib | Data visualization             |

## 📁 Project Structure

```text
ShopSense/
│
├── app.py
├── main.py
├── setup_database.py
├── sql_analysis.py
├── sql_analytics.py
│
├── requirements.txt
├── shopsense_sample_ecommerce.csv
│
├── category_profit.csv
├── category_sales.csv
├── data.csv
│
├── PHASE5_NOTES.txt
├── PHASE6_NOTES.txt
└── PHASE7_NOTES.txt
```

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/gaganruhal/ShopSense.git
cd ShopSense
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

For Windows:

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the dashboard

```bash
streamlit run app.py
```

The dashboard will open in your default web browser.

## 📈 Sample Dataset

The project includes a sample e-commerce dataset for exploring sales, products, customers, orders and business performance.

You can also upload your own CSV dataset and use the available analysis and reporting features.

## 🎯 Project Objectives

* Apply Python programming to real-world style data analysis.
* Understand data cleaning and preprocessing.
* Practice SQL queries and database operations.
* Build interactive data visualizations.
* Generate meaningful business insights from datasets.
* Develop an end-to-end data analytics project.

## 🔮 Future Improvements

* Advanced customer segmentation.
* More interactive visualizations.
* Additional business performance metrics.
* Sales forecasting and predictive analytics.
* Support for more data sources.

## 👨‍💻 Author

**Gagan Ruhal**

B.Tech — Artificial Intelligence & Machine Learning

* GitHub: https://github.com/gaganruhal
* Project Repository: https://github.com/gaganruhal/ShopSense

## 🌐 Live Demo

**Try ShopSense here:**

https://shopsense-dashboard.streamlit.app/

---

⭐ If you find this project interesting, consider giving the repository a star!
