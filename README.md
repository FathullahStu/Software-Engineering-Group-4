# ♻️ Smart Waste Management System (Group 4)

**A Streamlit-based Web Application for Residents, Waste Collectors, and Administrators.**

## 👥 Team Members
* **Afiq:** System Architecture & Database
* **Amir:** Resident UI (Booking System)
* **Fathullah:** Collector UI (Driver Checklist)
* **Min:** Admin Dashboard (Data Visualization)

---

## 🚀 Project Overview
This project digitizes the waste collection process to improve efficiency and encourage recycling.
* **Residents** can schedule pickups and earn "Eco-Points" for recycling.
* **Collectors** get a digital checklist of houses to visit.
* **Admins** view live data on waste collection and user activity.

---

## 📂 Project Structure
This project uses a flat-file modular structure.

| File | Purpose |
| :--- | :--- |
| `app.py` | **Main Application.** Run this file to start the system. |
| `auth.py` | Handles User Login and Registration logic. |
| `db_manager.py` | Manages the SQLite database (`ecosort.db`). |
| `resident_page.py` | UI for Residents (Bookings & Points). |
| `collector_page.py` | UI for Drivers (Job completion). |
| `admin_page.py` | UI for Admins (Dashboard & Stats). |
| `requirements.txt` | List of required Python libraries. |

*(Note: If you named your login file `login_page.py`, please rename it to `auth.py` to match this documentation, or update this line.)*

---

## 🛠️ How to Run This Project

### 1. Install Dependencies
Open your terminal in the project folder and run:
```bash
pip install -r requirements.txt
