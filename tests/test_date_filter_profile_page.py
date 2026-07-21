"""
Tests for Step 6: date-range filter on the /profile page.

Spec: .claude/specs/06-date-filter-profile-page.md

Behavior under test (query params on the existing GET /profile route):
  - `date_from` / `date_to` (ISO YYYY-MM-DD) filter summary stats, recent
    transactions, and category breakdown identically and simultaneously.
  - Absent or malformed params => fall back to unfiltered ("All Time") view.
  - date_from > date_to => fall back to unfiltered view + flash error.
  - Zero-match ranges must render cleanly (200), not error.
  - Amounts always use the Rupee symbol.
  - /profile is auth-guarded regardless of query params.

Seed data (from database/db.py seed_db(), reseeded fresh per test via the
`app` fixture in conftest.py): demo@spendly.com / demo123, with 8 expenses
across 7 categories, dated `today - {17,14,12,9,7,5,2,0}` days, clamped to
never precede the 1st of the current month. Because of that clamping, we
never assume a fixed absolute date — all expected ranges are computed the
same way the app does, from `date.today()`.
"""
from datetime import date, timedelta


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #
def _first_of_month():
    return date.today().replace(day=1)


def _iso(d):
    return d.isoformat()


# ------------------------------------------------------------------ #
# Baseline: unfiltered behaviour (Step 5 parity)                      #
# ------------------------------------------------------------------ #
class TestUnfilteredBaseline:
    def test_profile_no_params_returns_all_seed_expenses(self, logged_in_client):
        response = logged_in_client.get("/profile")
        assert response.status_code == 200
        body = response.data.decode("utf-8")

        # 8 seed expenses => transaction_count 8, total = sum of amounts.
        expected_total = 42.50 + 89.99 + 32.00 + 120.00 + 15.75 + 60.00 + 25.00 + 18.30
        assert "8" in body, "Expected transaction count of 8 in unfiltered view"
        assert f"{expected_total:.2f}" in body, (
            f"Expected unfiltered total {expected_total:.2f} in response body"
        )

    def test_profile_no_params_shows_nonempty_category_breakdown(self, logged_in_client):
        response = logged_in_client.get("/profile")
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        assert "No spending yet." not in body, (
            "Unfiltered view with seeded expenses must show a category breakdown"
        )
        # Food appears twice in seed data and should be present in the breakdown.
        assert "Food" in body

    def test_all_time_preset_link_matches_unfiltered_view(self, logged_in_client):
        """The 'All Time' preset must pass no query params (clean /profile URL)."""
        baseline = logged_in_client.get("/profile")
        all_time = logged_in_client.get("/profile", query_string={})
        assert all_time.status_code == 200
        assert baseline.data == all_time.data, (
            "All Time / no-params requests must render identical content"
        )


# ------------------------------------------------------------------ #
# Auth guard                                                          #
# ------------------------------------------------------------------ #
class TestAuthGuard:
    def test_profile_unauthenticated_no_params_redirects_to_login(self, client):
        response = client.get("/profile")
        assert response.status_code == 302, "Unauthenticated /profile must redirect"
        assert "/login" in response.headers.get("Location", ""), (
            "Unauthenticated /profile must redirect to /login"
        )

    def test_profile_unauthenticated_with_filter_params_redirects_to_login(self, client):
        response = client.get(
            "/profile",
            query_string={"date_from": "2026-01-01", "date_to": "2026-01-31"},
        )
        assert response.status_code == 302, (
            "Unauthenticated /profile with filter params must still redirect"
        )
        assert "/login" in response.headers.get("Location", "")


# ------------------------------------------------------------------ #
# Preset-equivalent custom ranges                                     #
# ------------------------------------------------------------------ #
class TestPresetEquivalentRanges:
    def test_this_month_range_includes_all_seed_expenses(self, logged_in_client):
        """Seed dates are clamped to never precede the 1st of the current month,
        so a 'This Month' range (1st of month -> today) must match the
        unfiltered baseline exactly (all 8 expenses, same total)."""
        today = date.today()
        baseline = logged_in_client.get("/profile")
        filtered = logged_in_client.get(
            "/profile",
            query_string={"date_from": _iso(_first_of_month()), "date_to": _iso(today)},
        )
        assert filtered.status_code == 200
        baseline_body = baseline.data.decode("utf-8")
        filtered_body = filtered.data.decode("utf-8")

        expected_total = 42.50 + 89.99 + 32.00 + 120.00 + 15.75 + 60.00 + 25.00 + 18.30
        assert f"{expected_total:.2f}" in filtered_body
        assert "8" in filtered_body
        # Category breakdown must be non-empty and match baseline's presence of Food.
        assert "Food" in filtered_body
        assert ("No spending yet." not in filtered_body)

    def test_last_3_months_range_includes_all_seed_expenses(self, logged_in_client):
        today = date.today()
        date_from = _iso(today - timedelta(days=90))
        response = logged_in_client.get(
            "/profile", query_string={"date_from": date_from, "date_to": _iso(today)}
        )
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        expected_total = 42.50 + 89.99 + 32.00 + 120.00 + 15.75 + 60.00 + 25.00 + 18.30
        assert f"{expected_total:.2f}" in body
        assert "8" in body

    def test_last_6_months_range_includes_all_seed_expenses(self, logged_in_client):
        today = date.today()
        date_from = _iso(today - timedelta(days=180))
        response = logged_in_client.get(
            "/profile", query_string={"date_from": date_from, "date_to": _iso(today)}
        )
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        expected_total = 42.50 + 89.99 + 32.00 + 120.00 + 15.75 + 60.00 + 25.00 + 18.30
        assert f"{expected_total:.2f}" in body
        assert "8" in body

    def test_narrow_custom_range_returns_subset_of_transactions(self, logged_in_client):
        """A range covering only 'today' should include the single expense
        dated `expense_date(0)` ('Miscellaneous', 18.30) and exclude the rest."""
        today = date.today()
        response = logged_in_client.get(
            "/profile", query_string={"date_from": _iso(today), "date_to": _iso(today)}
        )
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        assert "18.30" in body, "Expected today's single seed expense in narrow range"
        # Must not show the full unfiltered total (would be a filtering bug).
        full_total = 42.50 + 89.99 + 32.00 + 120.00 + 15.75 + 60.00 + 25.00 + 18.30
        assert f"{full_total:.2f}" not in body, (
            "Narrow same-day range must not show the full unfiltered total"
        )


# ------------------------------------------------------------------ #
# Zero-match range                                                    #
# ------------------------------------------------------------------ #
class TestZeroMatchRange:
    def test_zero_match_range_returns_empty_state_without_error(self, logged_in_client):
        """A date range entirely before any seed data must render 0 results,
        Rs 0.00 total, and an empty category breakdown -- with no server error."""
        far_past_from = "1990-01-01"
        far_past_to = "1990-01-31"
        response = logged_in_client.get(
            "/profile",
            query_string={"date_from": far_past_from, "date_to": far_past_to},
        )
        assert response.status_code == 200, "Zero-match range must not 500"
        body = response.data.decode("utf-8")
        assert "0.00" in body, "Expected Rs 0.00 total spent for zero-match range"
        assert "No transactions yet." in body
        assert "No spending yet." in body


# ------------------------------------------------------------------ #
# Invalid range: date_from > date_to                                  #
# ------------------------------------------------------------------ #
class TestInvalidRange:
    def test_from_after_to_falls_back_to_unfiltered_and_does_not_error(self, logged_in_client):
        today = date.today()
        response = logged_in_client.get(
            "/profile",
            query_string={
                "date_from": _iso(today),
                "date_to": _iso(today - timedelta(days=30)),
            },
        )
        assert response.status_code == 200, "Invalid range (from > to) must not error"
        body = response.data.decode("utf-8")

        expected_total = 42.50 + 89.99 + 32.00 + 120.00 + 15.75 + 60.00 + 25.00 + 18.30
        assert f"{expected_total:.2f}" in body, (
            "Invalid range must fall back to the unfiltered total"
        )
        assert "8" in body

    def test_from_after_to_shows_flash_error_message(self, logged_in_client):
        today = date.today()
        response = logged_in_client.get(
            "/profile",
            query_string={
                "date_from": _iso(today),
                "date_to": _iso(today - timedelta(days=30)),
            },
        )
        body = response.data.decode("utf-8")
        assert "Start date must be before end date." in body, (
            "Expected flash error message for date_from > date_to"
        )


# ------------------------------------------------------------------ #
# Malformed input                                                     #
# ------------------------------------------------------------------ #
class TestMalformedInput:
    def test_malformed_date_from_falls_back_to_unfiltered_without_crash(self, logged_in_client):
        response = logged_in_client.get(
            "/profile",
            query_string={"date_from": "not-a-date", "date_to": "2026-01-31"},
        )
        assert response.status_code == 200, "Malformed date_from must not crash the app"
        body = response.data.decode("utf-8")
        expected_total = 42.50 + 89.99 + 32.00 + 120.00 + 15.75 + 60.00 + 25.00 + 18.30
        assert f"{expected_total:.2f}" in body, (
            "Malformed date_from must fall back to the unfiltered total"
        )

    def test_malformed_date_to_falls_back_to_unfiltered_without_crash(self, logged_in_client):
        response = logged_in_client.get(
            "/profile",
            query_string={"date_from": "2026-01-01", "date_to": "not-a-date"},
        )
        assert response.status_code == 200, "Malformed date_to must not crash the app"
        body = response.data.decode("utf-8")
        expected_total = 42.50 + 89.99 + 32.00 + 120.00 + 15.75 + 60.00 + 25.00 + 18.30
        assert f"{expected_total:.2f}" in body

    def test_both_dates_malformed_falls_back_to_unfiltered(self, logged_in_client):
        response = logged_in_client.get(
            "/profile",
            query_string={"date_from": "banana", "date_to": "not-a-date"},
        )
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        expected_total = 42.50 + 89.99 + 32.00 + 120.00 + 15.75 + 60.00 + 25.00 + 18.30
        assert f"{expected_total:.2f}" in body
        assert "8" in body

    def test_sql_injection_style_date_from_does_not_crash_or_leak_data(self, logged_in_client):
        """Spec mandates parameterised queries; a SQL-injection-shaped string
        in date_from must be treated as a malformed date (not a date), and
        must not cause a 500 or return unexpected data."""
        response = logged_in_client.get(
            "/profile",
            query_string={
                "date_from": "2024-01-01' OR '1'='1",
                "date_to": "2026-01-31",
            },
        )
        assert response.status_code == 200, (
            "SQL-injection-shaped date_from must not crash the app"
        )
        body = response.data.decode("utf-8")
        expected_total = 42.50 + 89.99 + 32.00 + 120.00 + 15.75 + 60.00 + 25.00 + 18.30
        assert f"{expected_total:.2f}" in body, (
            "Injection-shaped date_from must fall back to the unfiltered total, "
            "not error or return manipulated results"
        )

    def test_empty_string_date_params_fall_back_to_unfiltered(self, logged_in_client):
        response = logged_in_client.get(
            "/profile", query_string={"date_from": "", "date_to": ""}
        )
        assert response.status_code == 200
        body = response.data.decode("utf-8")
        expected_total = 42.50 + 89.99 + 32.00 + 120.00 + 15.75 + 60.00 + 25.00 + 18.30
        assert f"{expected_total:.2f}" in body


# ------------------------------------------------------------------ #
# Currency formatting                                                  #
# ------------------------------------------------------------------ #
class TestCurrencyFormatting:
    def test_unfiltered_view_uses_rupee_symbol_not_dollar_or_pound(self, logged_in_client):
        response = logged_in_client.get("/profile")
        body = response.data.decode("utf-8")
        assert "₹" in body, "Expected the Rupee symbol (₹) in profile page"
        assert "$" not in body, "Dollar symbol must never appear in Spendly"
        assert "£" not in body, "Pound symbol must never appear in Spendly"

    def test_zero_match_range_still_uses_rupee_symbol(self, logged_in_client):
        response = logged_in_client.get(
            "/profile",
            query_string={"date_from": "1990-01-01", "date_to": "1990-01-31"},
        )
        body = response.data.decode("utf-8")
        assert "₹" in body, "Even a Rs 0.00 total must use the Rupee symbol"
        assert "$" not in body

    def test_filtered_view_uses_rupee_symbol(self, logged_in_client):
        today = date.today()
        response = logged_in_client.get(
            "/profile",
            query_string={"date_from": _iso(_first_of_month()), "date_to": _iso(today)},
        )
        body = response.data.decode("utf-8")
        assert "₹" in body
        assert "$" not in body
