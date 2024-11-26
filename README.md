# Event Management System

[Live Site](https://eventmanagement.site/)

## Overview
The **Event Management System** simplifies the organization and attendance of events, conferences, and gatherings. Designed for both organizers and attendees, it includes features for event creation, ticketing, and scheduling.

### Problem Statement
Event organizers and attendees require a streamlined platform for:
- Managing event details.
- Purchasing tickets.

### Features
- **For Organizers**:
  - Create and manage events with details like location, schedule, and speakers.
- **For Attendees**:
  - Register for events and purchase tickets.
- **Admin Panel**:
  - Manage users, events, and tickets.
- **Authentication**:
  - User SignUp and Login.
- **API Integration**:
  - REST API for event details, attendee registration, and ticket sales.

---

## Technology Stack
- **Backend**: Django, Django REST Framework (DRF)
- **Frontend**: Bootstrap (and custom CSS)
- **Payment Gateway**: Razorpay (for ticket transactions), Used Razorpay Payment Page  
- **Database**: SQLite (development) → PostgreSQL (production)

---

## Setup Instructions

### Prerequisites
Ensure you have the following installed:
- Python (3.8 or higher)
- pip (Python package manager)
- Virtualenv
- SQLite (for local development)
- PostgreSQL (for deployment)

---

### Installation
1. **Clone the Repository**:
    ```bash
    git clone https://github.com/debojit11/event-management-system.git
    cd event-management-system
    ```

2. **Create and Activate a Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set Up the Database**:
    - **For SQLite**:
        ```bash
        python manage.py migrate
        ```
    - **For PostgreSQL**:
        Update your `DATABASES` setting in `settings.py` to use PostgreSQL, then run:
        ```bash
        python manage.py migrate
        ```

5. **Create a Superuser**:
    ```bash
    python manage.py createsuperuser
    ```

6. **Run the Development Server**:
    ```bash
    python manage.py runserver
    ```

---

## Usage

### Accessing the Admin Panel
Visit `http://127.0.0.1:8000/admin` and log in with the superuser credentials you created.

### API Endpoints
- **Event**: ` /api/events/`
- **Attendees**: ` /api/attendees`
- **Tickets**: ` /api/tickets/`

---

## Deployment
The application is deployed on an Azure VM running Ubuntu 22.04 LTS server. The deployment setup includes:
- **Web Server**: Nginx
- **Application Server**: Gunicorn
- **Database**: PostgreSQL

---

## License 
This project is licensed under the MIT License. While you are free to use, copy, and modify the project on your own, direct modifications to this repository are not permitted

MIT License 

```markdown 
MIT License 

Copyright (c) [2024] [Debojit Choudhury]
