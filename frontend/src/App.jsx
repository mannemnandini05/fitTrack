
import React, { useEffect, useState } from "react";
import { api, logout } from "./api";

export default function App() {
  const [token, setToken] = useState(
    localStorage.getItem("fittrack_token")
  );

  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("fittrack_user") || "null");
    } catch {
      return null;
    }
  });

  const [page, setPage] = useState("Dashboard");
  const [rows, setRows] = useState([]);
  const [sum, setSum] = useState({});
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const [auth, setAuth] = useState({
    username: "",
    email: "",
    password: ""
  });

  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({});
  const [goalValues, setGoalValues] = useState({});
  const [search, setSearch] = useState("");

  const [weekly, setWeekly] = useState({});
  const [monthly, setMonthly] = useState({});
  const [comparison, setComparison] = useState({});

  const inputStyle = {
    padding: "10px",
    margin: "6px",
    border: "1px solid #ccc",
    borderRadius: "6px"
  };

  const buttonStyle = {
    padding: "10px 16px",
    margin: "6px",
    background: "#1769d2",
    color: "white",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer"
  };

  const cardStyle = {
    background: "white",
    padding: "18px",
    margin: "12px 0",
    borderRadius: "10px",
    boxShadow: "0 2px 8px #ddd"
  };

  function formatError(error) {
    return error?.message || "Something went wrong.";
  }

  function getArray(data, keys = []) {
    if (Array.isArray(data)) return data;

    if (data && typeof data === "object") {
      for (const key of keys) {
        if (Array.isArray(data[key])) return data[key];
      }
    }

    return [];
  }

  async function get(path) {
    return api(path);
  }

  // Load the selected page
  async function loadPage() {
    if (!token) return;

    setLoading(true);
    setErr("");

    try {
      if (page === "Dashboard") {
        const data = await get("/dashboard/summary");
        setSum(data || {});
      }

      else if (page === "Workouts") {
        const data = await get("/workouts");
        setRows(getArray(data, ["workouts", "items", "results"]));
      }

      else if (page === "Goals") {
        const data = await get("/goals");
        setRows(getArray(data, ["goals", "items", "results"]));
      }

      else if (page === "Workout Plans") {
        const data = await get("/workout-plans");
        setRows(
          getArray(data, ["plans", "workout_plans", "items", "results"])
        );
      }

      else if (page === "Exercise Library") {
        const data = await get(
          `/exercises?search=${encodeURIComponent(search)}`
        );

        setRows(
          getArray(data, ["exercises", "items", "results"])
        );
      }

      else if (page === "Reports") {
        const [w, m, c1, c2] = await Promise.all([
          get("/reports/weekly"),
          get("/reports/monthly"),
          get("/progress/compare/weekly"),
          get("/progress/compare/monthly")
        ]);

        setWeekly(w || {});
        setMonthly(m || {});

        setComparison({
          weekly: c1 || {},
          monthly: c2 || {}
        });
      }

      else if (page === "Streaks & Badges") {
        const [s, b] = await Promise.all([
          get("/streak"),
          get("/badges")
        ]);

        setSum({
          streak: s || {},
          badges: getArray(b, ["badges", "items", "results"])
        });
      }

      else if (page === "Notifications") {
        const data = await get("/notifications");

        setRows(
          getArray(data, ["notifications", "items", "results"])
        );
      }

    } catch (error) {
      setErr(formatError(error));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPage();
  }, [page, token]);

  // Common create, update and delete function
  async function act(path, method = "POST", body = null) {
    try {
      setErr("");

      await api(path, method, body);

      setForm({});
      await loadPage();

    } catch (error) {
      setErr(formatError(error));
    }
  }

  // LOGIN AND REGISTRATION
  async function handleAuth(e) {
    e.preventDefault();

    try {
      setErr("");

      if (isRegister) {
        await api("/auth/register", "POST", {
          username: auth.username,
          email: auth.email,
          password: auth.password
        });

        alert("Registration successful. Please log in.");

        setIsRegister(false);

        setAuth({
          username: auth.username,
          email: "",
          password: ""
        });

      } else {
        const data = await api("/auth/login", "POST", {
          username_or_email: auth.username,
          password: auth.password
        });

        localStorage.setItem("fittrack_token", data.access_token);
        localStorage.setItem("fittrack_user", JSON.stringify(data.user));

        setToken(data.access_token);
        setUser(data.user);
      }

    } catch (error) {
      setErr(formatError(error));
    }
  }

  // LOGOUT
  function handleLogout() {
    logout();

    setToken(null);
    setUser(null);
    setRows([]);
    setSum({});
    setErr("");
    setPage("Dashboard");
  }

  // LOGIN PAGE
  if (!token) {
    return (
      <div style={{
        maxWidth: "400px",
        margin: "80px auto",
        padding: "30px",
        boxShadow: "0 2px 12px #ccc",
        borderRadius: "12px",
        background: "white"
      }}>
        <h1 style={{ color: "#1769d2" }}>🏃 FitTrack</h1>

        <h2>{isRegister ? "Create Account" : "Login"}</h2>

        <form onSubmit={handleAuth}>
          <input
            style={inputStyle}
            placeholder="Username or Email"
            value={auth.username}
            onChange={e =>
              setAuth({ ...auth, username: e.target.value })
            }
            required
          />

          {isRegister && (
            <input
              style={inputStyle}
              type="email"
              placeholder="Email"
              value={auth.email}
              onChange={e =>
                setAuth({ ...auth, email: e.target.value })
              }
              required
            />
          )}

          <input
            style={inputStyle}
            type="password"
            placeholder="Password"
            value={auth.password}
            onChange={e =>
              setAuth({ ...auth, password: e.target.value })
            }
            required
          />

          <button style={buttonStyle} type="submit">
            {isRegister ? "Register" : "Login"}
          </button>
        </form>

        <button
          style={{ ...buttonStyle, background: "#555" }}
          onClick={() => {
            setIsRegister(!isRegister);
            setErr("");
          }}
        >
          {isRegister ? "Go to Login" : "Create Account"}
        </button>

        {err && <p style={{ color: "red" }}>{err}</p>}
      </div>
    );
  }

  // DASHBOARD
  function renderDashboard() {
    const daily = sum.daily_summary || {};
    const weeklyData = sum.weekly_summary || {};
    const streak = sum.streak || {};
    const badges = Array.isArray(sum.earned_badges)
      ? sum.earned_badges
      : [];

    return (
      <>
        <h2>Dashboard</h2>

        <div style={cardStyle}>
          <h3>Today's Summary</h3>
          <p>Workouts: {daily.total_workouts ?? 0}</p>
          <p>Calories: {daily.total_calories ?? 0}</p>
          <p>Duration: {daily.total_duration ?? 0} minutes</p>
        </div>

        <div style={cardStyle}>
          <h3>Weekly Summary</h3>
          <p>Workouts: {weeklyData.total_workouts ?? 0}</p>
          <p>Calories: {weeklyData.total_calories ?? 0}</p>
          <p>Duration: {weeklyData.total_duration ?? 0} minutes</p>
        </div>

        <div style={cardStyle}>
          <h3>Current Streak</h3>
          <h2>{streak.current_streak ?? 0} days</h2>
        </div>

        <div style={cardStyle}>
          <h3>Earned Badges</h3>

          {badges.length === 0
            ? <p>No badges earned yet.</p>
            : badges.map((badge, index) => (
                <p key={badge.id || index}>
                  {badge.name || badge.title || "Achievement"}
                </p>
              ))}
        </div>
      </>
    );
  }

  // WORKOUTS
  function renderWorkouts() {
    return (
      <>
        <h2>Workouts</h2>

        <div style={cardStyle}>
          <h3>Add Workout</h3>

          <input
            style={inputStyle}
            placeholder="Workout Name"
            value={form.workout_name || ""}
            onChange={e =>
              setForm({ ...form, workout_name: e.target.value })
            }
          />

          <select
  style={inputStyle}
  value={form.category || ""}
  onChange={e =>
    setForm({ ...form, category: e.target.value })
  }
  required
>
  <option value="">Select Category</option>
  <option value="Cardio">Cardio</option>
  <option value="Strength">Strength</option>
  <option value="Yoga">Yoga</option>
</select>

          <input
            style={inputStyle}
            type="number"
            min="1"
            placeholder="Duration (minutes)"
            value={form.duration ?? ""}
            onChange={e =>
              setForm({ ...form, duration: e.target.value })
            }
          />

          <input
            style={inputStyle}
            type="number"
            min="0"
            placeholder="Calories Burned"
            value={form.calories_burned ?? ""}
            onChange={e =>
              setForm({ ...form, calories_burned: e.target.value })
            }
          />

          <input
            style={inputStyle}
            type="date"
            value={form.workout_date || ""}
            onChange={e =>
              setForm({ ...form, workout_date: e.target.value })
            }
          />

          <button
            style={buttonStyle}
            onClick={() => {
              if (
                !form.workout_name?.trim() ||
                !form.category?.trim() ||
                form.duration === "" ||
                form.duration === undefined ||
                Number(form.duration) <= 0 ||
                form.calories_burned === "" ||
                form.calories_burned === undefined ||
                Number(form.calories_burned) < 0 ||
                !form.workout_date
              ) {
                setErr("Please enter valid values in all workout fields.");
                return;
              }

              act("/workouts", "POST", {
                workout_name: form.workout_name.trim(),
                category: form.category.trim(),
                duration: Number(form.duration),
                calories_burned: Number(form.calories_burned),
                workout_date: form.workout_date
              });
            }}
          >
            Add Workout
          </button>
        </div>

        {rows.length === 0 && (
          <p>No workouts found. Add your first workout.</p>
        )}

        {rows.map(workout => (
          <div style={cardStyle} key={workout.id}>
            <h3>{workout.workout_name}</h3>
            <p>Category: {workout.category}</p>
            <p>Duration: {workout.duration} minutes</p>
            <p>Calories: {workout.calories_burned}</p>
            <p>Date: {workout.workout_date}</p>

            <button
              style={{ ...buttonStyle, background: "#d32f2f" }}
              onClick={() =>
                act(`/workouts/${workout.id}`, "DELETE")
              }
            >
              Delete
            </button>
          </div>
        ))}
      </>
    );
  }

  // GOALS
  function renderGoals() {
    return (
      <>
        <h2>Goals</h2>

        <div style={cardStyle}>
          <h3>Set Goal</h3>

         
<select
  style={inputStyle}
  value={form.goal_type || ""}
  onChange={e =>
    setForm({ ...form, goal_type: e.target.value })
  }
  required
>
  <option value="">Select Goal Type</option>
  <option value="Weight Loss">Weight Loss</option>
  <option value="Muscle Gain">Muscle Gain</option>
  <option value="Steps">Steps</option>
</select>


          <input
            style={inputStyle}
            type="number"
            min="1"
            placeholder="Target Value"
            value={form.target_value ?? ""}
            onChange={e =>
              setForm({
                ...form,
                target_value: e.target.value
              })
            }
          />

          <input
            style={inputStyle}
            type="date"
            value={form.deadline || ""}
            onChange={e =>
              setForm({ ...form, deadline: e.target.value })
            }
          />

          <button
            style={buttonStyle}
            onClick={() => {
              if (
                !form.goal_type?.trim() ||
                form.target_value === "" ||
                form.target_value === undefined ||
                Number(form.target_value) <= 0 ||
                !form.deadline
              ) {
                setErr("Please enter valid goal details.");
                return;
              }

              act("/goals", "POST", {
                goal_type: form.goal_type.trim(),
                target_value: Number(form.target_value),
                current_value: 0,
                deadline: form.deadline
              });
            }}
          >
            Create Goal
          </button>
        </div>

        {rows.length === 0 && <p>No goals found. Create your first goal.</p>}

        {rows.map(goal => (
          <div style={cardStyle} key={goal.id}>
            <h3>{goal.goal_type}</h3>

            <p>
              Progress: {goal.current_value}/{goal.target_value}
            </p>

            <p>Status: {goal.status}</p>
            <p>Deadline: {goal.deadline}</p>

            <input
              style={inputStyle}
              type="number"
              min="0"
              placeholder="Update value"
              value={goalValues[goal.id] ?? ""}
              onChange={e =>
                setGoalValues({
                  ...goalValues,
                  [goal.id]: e.target.value
                })
              }
            />

            <button
              style={buttonStyle}
              onClick={() => {
                const value = goalValues[goal.id];

                if (value === undefined || value === "" || Number(value) < 0) {
                  setErr("Please enter a valid progress value.");
                  return;
                }

                // Backend goal update uses PUT.
                act(`/goals/${goal.id}`, "PUT", {
                  goal_type: goal.goal_type,
                  target_value: goal.target_value,
                  current_value: Number(value),
                  deadline: goal.deadline
                });
              }}
            >
              Update
            </button>

            <button
              style={{ ...buttonStyle, background: "#d32f2f" }}
              onClick={() =>
                act(`/goals/${goal.id}`, "DELETE")
              }
            >
              Delete
            </button>
          </div>
        ))}
      </>
    );
  }

  // WORKOUT PLANS
  function renderPlans() {
    return (
      <>
        <h2>Workout Plans</h2>

        <div style={cardStyle}>
          <h3>Create Workout Plan</h3>

          <input
            style={inputStyle}
            placeholder="Plan Name"
            value={form.title || ""}
            onChange={e =>
              setForm({ ...form, title: e.target.value })
            }
          />

          <input
            style={inputStyle}
            placeholder="Description"
            value={form.description || ""}
            onChange={e =>
              setForm({ ...form, description: e.target.value })
            }
          />

          <input
            style={inputStyle}
            type="date"
            value={form.scheduled_date || ""}
            onChange={e =>
              setForm({ ...form, scheduled_date: e.target.value })
            }
          />

          <button
            style={buttonStyle}
            onClick={() => {
              if (!form.title?.trim() || !form.scheduled_date) {
                setErr("Please enter plan name and scheduled date.");
                return;
              }

              act("/workout-plans", "POST", {
                title: form.title.trim(),
                description: form.description || "",
                scheduled_date: form.scheduled_date
              });
            }}
          >
            Create Plan
          </button>
        </div>

        {rows.length === 0 && <p>No workout plans found.</p>}

        {rows.map(plan => (
          <div style={cardStyle} key={plan.id}>
            <h3>{plan.title}</h3>
            <p>{plan.description}</p>
            <p>Scheduled Date: {plan.scheduled_date}</p>

            <button
              style={{ ...buttonStyle, background: "#d32f2f" }}
              onClick={() =>
                act(`/workout-plans/${plan.id}`, "DELETE")
              }
            >
              Delete
            </button>
          </div>
        ))}
      </>
    );
  }

  // EXERCISE LIBRARY
  function renderExercises() {
    return (
      <>
        <h2>Exercise Library</h2>

        <input
          style={inputStyle}
          placeholder="Search exercises"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />

        <button
          style={buttonStyle}
          onClick={loadPage}
        >
          Search
        </button>

        {rows.length === 0 && <p>No exercises found.</p>}

        {rows.map(exercise => (
          <div style={cardStyle} key={exercise.id}>
            <h3>{exercise.name}</h3>
            <p>Category: {exercise.category}</p>
            <p>Muscle Group: {exercise.muscle_group}</p>
            <p>Equipment: {exercise.equipment}</p>
          </div>
        ))}
      </>
    );
  }

  // REPORTS
  function renderReports() {
    return (
      <>
        <h2>Reports & Analytics</h2>

        <div style={cardStyle}>
          <h3>Weekly Report</h3>
          <p>Workouts: {weekly.total_workouts ?? 0}</p>
          <p>Calories: {weekly.total_calories ?? 0}</p>
          <p>Duration: {weekly.total_duration ?? 0} minutes</p>
        </div>

        <div style={cardStyle}>
          <h3>Monthly Report</h3>
          <p>Workouts: {monthly.total_workouts ?? 0}</p>
          <p>Calories: {monthly.total_calories ?? 0}</p>
          <p>Duration: {monthly.total_duration ?? 0} minutes</p>
        </div>

        <div style={cardStyle}>
          <h3>Weekly Comparison</h3>

          <p>
            Current Week:{" "}
            {comparison.weekly?.current_week?.total_workouts ?? 0}
          </p>

          <p>
            Previous Week:{" "}
            {comparison.weekly?.previous_week?.total_workouts ?? 0}
          </p>
        </div>

        <div style={cardStyle}>
          <h3>Monthly Comparison</h3>

          <p>
            Current Month:{" "}
            {comparison.monthly?.current_month?.total_workouts ?? 0}
          </p>

          <p>
            Previous Month:{" "}
            {comparison.monthly?.previous_month?.total_workouts ?? 0}
          </p>
        </div>
      </>
    );
  }

  // STREAKS AND BADGES
  function renderStreaks() {
    const streak = sum.streak || {};
    const badges = Array.isArray(sum.badges) ? sum.badges : [];

    return (
      <>
        <h2>Streaks & Badges</h2>

        <div style={cardStyle}>
          <h3>Current Streak</h3>
          <h2>{streak.current_streak ?? 0} days</h2>
          <p>Longest Streak: {streak.longest_streak ?? 0} days</p>
        </div>

        <div style={cardStyle}>
          <h3>Badges</h3>

          {badges.length === 0
            ? <p>No badges available yet.</p>
            : badges.map((badge, index) => (
                <p key={badge.id || index}>
                  {badge.name || badge.title || "Achievement"}
                </p>
              ))}
        </div>
      </>
    );
  }

  // NOTIFICATIONS
  function renderNotifications() {
    return (
      <>
        <h2>Notifications</h2>

        <div style={cardStyle}>
          <h3>Create Notification</h3>

          <input
            style={inputStyle}
            placeholder="Title"
            value={form.title || ""}
            onChange={e =>
              setForm({ ...form, title: e.target.value })
            }
          />

          <input
            style={inputStyle}
            placeholder="Message"
            value={form.message || ""}
            onChange={e =>
              setForm({ ...form, message: e.target.value })
            }
          />

          <button
            style={buttonStyle}
            onClick={() => {
              if (!form.title?.trim() || !form.message?.trim()) {
                setErr("Please enter notification title and message.");
                return;
              }

              act("/notifications", "POST", {
                title: form.title.trim(),
                message: form.message.trim()
              });
            }}
          >
            Add Notification
          </button>
        </div>

        {rows.length === 0 && <p>No notifications found.</p>}

        {rows.map(notification => (
          <div style={cardStyle} key={notification.id}>
            <h3>{notification.title}</h3>
            <p>{notification.message}</p>

            <p>
              Status: {notification.is_read ? "Read" : "Unread"}
            </p>

            {!notification.is_read && (
              <button
                style={buttonStyle}
                onClick={() =>
                  act(
                    `/notifications/${notification.id}/read`,
                    "PATCH"
                  )
                }
              >
                Mark as Read
              </button>
            )}
          </div>
        ))}
      </>
    );
  }

  // PAGE ROUTING
  function renderContent() {
    switch (page) {
      case "Dashboard":
        return renderDashboard();

      case "Workouts":
        return renderWorkouts();

      case "Goals":
        return renderGoals();

      case "Workout Plans":
        return renderPlans();

      case "Exercise Library":
        return renderExercises();

      case "Reports":
        return renderReports();

      case "Streaks & Badges":
        return renderStreaks();

      case "Notifications":
        return renderNotifications();

      default:
        return <h2>Page Not Found</h2>;
    }
  }

  const menu = [
    "Dashboard",
    "Workouts",
    "Goals",
    "Workout Plans",
    "Exercise Library",
    "Reports",
    "Streaks & Badges",
    "Notifications"
  ];

  return (
    <div style={{
      display: "flex",
      minHeight: "100vh",
      background: "#f4f6fa",
      fontFamily: "Arial, sans-serif"
    }}>
      <aside style={{
        width: "220px",
        background: "#fff",
        padding: "20px",
        boxShadow: "2px 0 8px #ddd"
      }}>
        <h2 style={{ color: "#1769d2" }}>🏃 FitTrack</h2>
        <p style={{ color: "#777" }}>FITNESS PLATFORM</p>

        {menu.map(item => (
          <button
            key={item}
            onClick={() => {
              setPage(item);
              setForm({});
              setRows([]);
              setErr("");
            }}
            style={{
              display: "block",
              width: "100%",
              textAlign: "left",
              padding: "12px",
              margin: "8px 0",
              border: "none",
              borderRadius: "7px",
              cursor: "pointer",
              background: page === item ? "#1769d2" : "white",
              color: page === item ? "white" : "#333"
            }}
          >
            {item}
          </button>
        ))}

        <hr />

        <p>{user?.username || user?.email || "User"}</p>

        <button
          style={{ ...buttonStyle, background: "#d32f2f" }}
          onClick={handleLogout}
        >
          Sign Out
        </button>
      </aside>

      <main style={{
        flex: 1,
        padding: "30px",
        minWidth: 0
      }}>
        <h4 style={{ color: "#777" }}>
          FITTRACK / PERSONAL
        </h4>

        {err && (
          <div style={{
            padding: "12px",
            background: "#ffe5e5",
            color: "#b00020",
            borderRadius: "6px",
            marginBottom: "15px"
          }}>
            {err}
          </div>
        )}

        {loading ? (
          <p>Loading...</p>
        ) : (
          renderContent()
        )}
      </main>
    </div>
  );
}
