## 2026-02-16 - N+1 Query in BookingService
**Learning:** `BookingService.get_member_bookings` used `join(Class)` but accessed `b.gym_class` attributes inside the loop, causing N+1 queries because SQLAlchemy's default loading strategy is lazy.
**Action:** Use `.options(contains_eager(ClassBooking.gym_class))` when the joined entity is accessed in a loop to fetch everything in a single query.
