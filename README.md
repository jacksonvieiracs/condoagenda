<p align="center">
  <img src="https://img.shields.io/badge/status-in%20progress-yellow?style=for-the-badge" alt="Status: In Progress" />
  <img src="https://img.shields.io/badge/python-3.13+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13+" />
  <img src="https://img.shields.io/badge/django-5.2-green?style=for-the-badge&logo=django&logoColor=white" alt="Django 5.2" />
  <img src="https://img.shields.io/badge/fastapi-0.118+-teal?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
</p>

<h1 align="center">🏢 CondoAgenda</h1>

<p align="center">
  <strong>Intelligent WhatsApp Bot for Condominium Scheduling</strong>
</p>

<p align="center">
  Automate common area reservations in your condominium through an intuitive WhatsApp chatbot. <br/>
  No apps to download, no complicated interfaces — just send a message.
</p>

---

## 📹 Demo <sup><span style="color: orange; font-weight: bold;">(Coming Soon!)</span></sup>

<p align="center">
  <em><strong>Demo video will be available shortly!</strong></em>
</p>

<p align="center">
  <a href="https://www.youtube.com/watch?v=<video_id_here>" style="pointer-events: none; opacity: 0.5; cursor: default;" onclick="return false;">
    <img src="https://img.youtube.com/vi/<video_id_here>/maxresdefault.jpg" alt="CondoAgenda Demo Coming Soon" width="600" style="filter: grayscale(100%);"/>
  </a>
</p>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📅 **Smart Scheduling** | Book common areas with real-time availability checking |
| 📱 **WhatsApp Native** | No apps required — works directly in WhatsApp |
| 🔔 **Automatic Reminders** | Get notified before your reservation starts and ends |
| 🔍 **View Reservations** | Check your upcoming bookings anytime |
| 🏠 **Multi-Floor Support** | Manage different areas across building floors |
| ⚡  **Confirmation** | Immediate booking confirmation via message |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CondoAgenda                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐      ┌──────────────┐      ┌─────────────┐  │
│   │   WhatsApp   │◄────►│ Evolution    │◄────►│ CondoAgenda │  │
│   │   Users      │      │ API          │      │ Bot         │  │
│   └──────────────┘      └──────────────┘      └──────┬──────┘  │
│                                                       │         │
│                                                       ▼         │
│                                              ┌──────────────┐   │
│                                              │ CondoAgenda  │   │
│                                              │ API          │   │
│                                              └──────┬───────┘   │
│                                                     │           │
│                                                     ▼           │
│                                              ┌──────────────┐   │
│                                              │  PostgreSQL  │   │
│                                              │  Database    │   │
│                                              └──────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend API
- **Framework:** Django 5.2 + Django REST Framework
- **Database:** PostgreSQL
- **HTTP Client:** HTTPX (async requests)

### WhatsApp Bot
- **Framework:** FastAPI
- **WhatsApp Integration:** Evolution API
- **Workflow Engine:** Custom conversational workflow orchestrator

### Development
- **Python:** 3.13+
- **Package Manager:** uv
- **Linting:** Ruff
- **Testing:** pytest + pytest-cov

---

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- PostgreSQL
- [Evolution API](https://github.com/EvolutionAPI/evolution-api) instance
- uv

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/jacksonvieiracs/condoagenda.git
cd condoagenda
```

2. **Setup the API**

```bash
cd src/condoagenda-api
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

3. **Setup the Bot**

```bash
cd src/condoagenda-bot
uv sync
uv run fastapi dev agendabot/api/main.py
```

4. **Configure Evolution API**

Point your Evolution API webhook to the bot's endpoint.

---

## 💬 Bot Conversation Flow

```
User: Hi
Bot:  Hello! I'm the virtual assistant. I can help you with:
      • Make reservations
      • View your reservations
      
      What would you like to do?

User: Make a reservation
Bot:  Enter your apartment number (e.g., 101, 118)

User: 205
Bot:  Choose a date:
      1. Today (12/02)
      2. Tomorrow (12/03)
      3. Thursday (12/04)
      ...

User: 1
Bot:  Choose a time slot:
      1. 07:00 - 09:00
      2. 09:00 - 11:00
      ...

User: 2
Bot:  📋 Reservation Summary:
      Apartment: 205
      ✅ 12/02 (Monday)
      ✅ 09:00 - 11:00
      
      Confirm this reservation?

User: Confirm
Bot:  ✅ Reservation confirmed successfully!
```

---

## 📊 Data Models

| Model | Description |
|-------|-------------|
| `Apartamento` | Apartment units with number and responsible person |
| `Reserva` | Booking records with date, time, floor, and reminder status |
| `Configuracao` | System settings (operating hours, slot duration, reminder timing) |

---

## Roadmap

- [x] Basic scheduling workflow
- [x] View existing reservations
- [ ] Automatic reminders system
- [ ] Cancel reservations via WhatsApp
