# Business Rules - CondoAgenda API

## Overview
This document describes the business rules implemented in the reservation system.

## Implemented Business Rules

### 1. Weekly Booking Window
- Users can only book slots within the current week (Monday to Sunday)
- Bookings outside this window are rejected with an error message

### 2. Weekly Reset
- Every Monday, reservations from the previous week are deleted
- Run the management command: `python manage.py reset_weekly_reservas`
- Recommended: Set up a cron job to run this automatically every Monday

### 3. Maximum Reservations per Apartment
- Each apartment has a maximum number of reservations per day (configurable in `Configuracao`)
- Default: 2 reservations per apartment per day
- This prevents a single apartment from monopolizing all available slots

### 4. Odd Hours Only
- Reservations can only be made at odd hours: 07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00
- Even hours (08:00, 10:00, etc.) are automatically rejected
- This helps organize and space out reservations

### 5. No Duplicate Bookings
- Each time slot can only be booked once per floor (andar)
- Different floors can have the same time slot booked by different apartments

### 6. Automatic End Time Calculation
- `hora_saida` (end time) is automatically calculated based on `hora` (start time) + `duracao_reserva_minutos` (from configuration)
- Default duration: 120 minutes (2 hours)
- Users don't need to specify the end time when creating a reservation

## Architecture

### Service Layer (`apps/core/services.py`)
All business logic is centralized in the `ReservaService` class:

- `validate_reserva()` - Validates all business rules before creation
- `create_reserva()` - Creates a reservation with automatic end time calculation
- `get_current_week_range()` - Helper to get Monday-Sunday range
- `is_odd_hour()` - Validates if a time is on an odd hour
- `reset_weekly_reservas()` - Deletes previous week's reservations

### Serializer (`apps/core/api/serializers.py`)
- `ReservaSerializer` uses the service layer for validation and creation
- `hora_saida` is marked as read-only since it's calculated automatically
- The `create()` method delegates to `ReservaService.create_reserva()`

### API Endpoints

#### Create Reservation
```bash
POST /api/reservas/
Content-Type: application/json

{
  "data": "2025-11-18",
  "hora": "09:00:00",
  "apartamento": 1,
  "andar": 0
}
```

Response includes the automatically calculated `hora_saida`:
```json
{
  "id": 1,
  "data": "2025-11-18",
  "hora": "09:00:00",
  "hora_saida": "11:00:00",
  "apartamento": 1,
  "andar": 0
}
```

#### List Available Slots
```bash
GET /api/slots/?data=2025-11-18&andar=0
```

Returns all time slots with availability information based on business rules.

## Testing

Run all tests:
```bash
python manage.py test apps.core.tests_services apps.core.tests_serializers apps.core.tests_api
```

- **Service tests**: Verify business logic implementation
- **Serializer tests**: Verify integration between serializer and service layer
- **API tests**: Verify end-to-end functionality

Total: 14 tests covering all business rules ✅

## Configuration

All configurable values are stored in the `Configuracao` model:

- `hora_inicio`: Start of business hours (default: 07:00)
- `hora_fim`: End of business hours (default: 19:00)
- `duracao_reserva_minutos`: Duration of each reservation (default: 120 minutes)
- `quantidade_agendamento_por_apartamento`: Max reservations per apartment per day (default: 2)

## Maintenance

### Weekly Reset (Cron Job)
Add to crontab to run every Monday at 00:00:
```bash
0 0 * * 1 cd /path/to/project && /path/to/venv/bin/python manage.py reset_weekly_reservas
```

