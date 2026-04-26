// ============================================================
// 1. 이벤트 타입별 발생 횟수
// ============================================================
from(bucket: "lk_events")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "events" and r._field == "page")
  |> group(columns: ["event_type"])
  |> count()
  |> group()
  |> rename(columns: {_value: "count"})
  |> sort(columns: ["count"], desc: true)

// ============================================================
// 2. 시간대별 이벤트 추이 (1분 window)
// ============================================================
from(bucket: "lk_events")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "events" and r._field == "page")
  |> group(columns: ["event_type"])
  |> aggregateWindow(every: 1m, fn: count, createEmpty: true)
  |> fill(value: 0)

// ============================================================
// 3. 로그인 실패 원인 분석
// ============================================================
from(bucket: "lk_events")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "events" and r._field == "page")
  |> filter(fn: (r) =>
      r.event_type == "login_fail_duplicate_id" or
      r.event_type == "login_fail_password_policy")
  |> group(columns: ["event_type"])
  |> count()
  |> group()
  |> rename(columns: {_value: "count"})

// ============================================================
// 4. 에러 이벤트 비율
// ============================================================
total = (from(bucket: "lk_events")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "events" and r._field == "page")
  |> count()
  |> findRecord(fn: (key) => true, idx: 0))._value

errors = (from(bucket: "lk_events")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "events" and r._field == "page" and r.event_type == "error")
  |> count()
  |> findRecord(fn: (key) => true, idx: 0))._value

float(v: errors) / float(v: if total == 0 then 1 else total)

// ============================================================
// 5. 유저별 활동 순위 (상위 20명)
// ============================================================
from(bucket: "lk_events")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "events" and r._field == "page")
  |> group(columns: ["user_id"])
  |> count()
  |> group()
  |> rename(columns: {_value: "event_count"})
  |> sort(columns: ["event_count"], desc: true)
  |> limit(n: 20)
  |> keep(columns: ["user_id", "event_count"])
