package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
)

var db *sql.DB

// Database models
type Expense struct {
	ID          int     `json:"id"`
	UserID      int     `json:"user_id"`
	Amount      float64 `json:"amount"`
	Category    string  `json:"category"`
	Date        string  `json:"date"`
	Description *string `json:"description,omitempty"`
	UserName    *string `json:"user_name,omitempty"`
}

type ExpenseSummary struct {
	Categories []CategoryTotal `json:"categories"`
	Daily      []DailyTotal    `json:"daily"`
	Total      float64         `json:"total"`
}

type CategoryTotal struct {
	Category string  `json:"category"`
	Amount   float64 `json:"amount"`
}

type DailyTotal struct {
	Date   string  `json:"date"`
	Amount float64 `json:"amount"`
}

type Budget struct {
	ID         int     `json:"id"`
	Category   string  `json:"category"`
	Amount     float64 `json:"amount"`
	Period     string  `json:"period"`
	Spent      float64 `json:"spent"`
	Remaining  float64 `json:"remaining"`
	Percentage float64 `json:"percentage"`
}

type SavingsGoal struct {
	ID            int     `json:"id"`
	Name          string  `json:"name"`
	Description   string  `json:"description"`
	TargetAmount  float64 `json:"target_amount"`
	CurrentAmount float64 `json:"current_amount"`
	TargetDate    *string `json:"target_date,omitempty"`
	CreatedDate   string  `json:"created_date"`
	Percentage    float64 `json:"percentage"`
}

type User struct {
	UserID      int     `json:"user_id"`
	UserName    string  `json:"user_name"`
	CreatedDate *string `json:"created_date,omitempty"`
}

// Initialize database connection
func initDB() {
	var err error
	databaseURL := os.Getenv("DATABASE_URL")
	if databaseURL == "" {
		databaseURL = "postgresql://postgres:postgres@localhost:5432/expenses?sslmode=disable"
	}

	// Wait for database to be ready
	for i := 0; i < 10; i++ {
		db, err = sql.Open("postgres", databaseURL)
		if err == nil {
			err = db.Ping()
			if err == nil {
				log.Println("✅ Successfully connected to database")

				// Check if tables exist (wait for bot to create them)
				if checkTablesExist() {
					log.Println("✅ Database tables found")
					return
				}
				log.Printf("⏳ Waiting for database tables... (attempt %d/10)", i+1)
			}
		}
		log.Printf("⏳ Waiting for database... (attempt %d/10): %v", i+1, err)
		time.Sleep(3 * time.Second)
	}

	log.Fatal("❌ Failed to connect to database after 10 attempts:", err)
}

// Check if required tables exist
func checkTablesExist() bool {
	var exists bool
	query := `
		SELECT EXISTS (
			SELECT FROM information_schema.tables
			WHERE table_schema = 'public'
			AND table_name = 'expenses'
		)
	`
	err := db.QueryRow(query).Scan(&exists)
	return err == nil && exists
}

// Health check endpoint
func healthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

// Get expenses for a user with optional filters
func getExpenses(c *gin.Context) {
	userID, err := strconv.Atoi(c.Param("user_id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id"})
		return
	}

	startDate := c.Query("start_date")
	endDate := c.Query("end_date")
	category := c.Query("category")

	query := "SELECT id, user_id, amount, category, date, description, user_name FROM expenses WHERE user_id = $1"
	args := []interface{}{userID}
	argCount := 1

	if startDate != "" {
		argCount++
		query += fmt.Sprintf(" AND date >= $%d", argCount)
		args = append(args, startDate)
	}

	if endDate != "" {
		argCount++
		query += fmt.Sprintf(" AND date <= $%d", argCount)
		args = append(args, endDate)
	}

	if category != "" {
		argCount++
		query += fmt.Sprintf(" AND category = $%d", argCount)
		args = append(args, category)
	}

	query += " ORDER BY date DESC"

	rows, err := db.Query(query, args...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var expenses []Expense
	for rows.Next() {
		var e Expense
		err := rows.Scan(&e.ID, &e.UserID, &e.Amount, &e.Category, &e.Date, &e.Description, &e.UserName)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		expenses = append(expenses, e)
	}

	if expenses == nil {
		expenses = []Expense{}
	}

	c.JSON(http.StatusOK, expenses)
}

// Get expenses summary (last 30 days)
func getExpensesSummary(c *gin.Context) {
	userID, err := strconv.Atoi(c.Param("user_id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id"})
		return
	}

	// Date 30 days ago
	date30DaysAgo := time.Now().AddDate(0, 0, -30).Format("2006-01-02")

	// Get aggregated expenses by category
	rows, err := db.Query(`
		SELECT category, SUM(amount) as total
		FROM expenses
		WHERE user_id = $1 AND date >= $2
		GROUP BY category
		ORDER BY total DESC
	`, userID, date30DaysAgo)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var categories []CategoryTotal
	var total float64

	for rows.Next() {
		var ct CategoryTotal
		err := rows.Scan(&ct.Category, &ct.Amount)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		categories = append(categories, ct)
		total += ct.Amount
	}

	// Get daily expenses for chart
	rows2, err := db.Query(`
		SELECT date, SUM(amount) as daily_total
		FROM expenses
		WHERE user_id = $1 AND date >= $2
		GROUP BY date
		ORDER BY date
	`, userID, date30DaysAgo)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows2.Close()

	var daily []DailyTotal
	for rows2.Next() {
		var dt DailyTotal
		err := rows2.Scan(&dt.Date, &dt.Amount)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		daily = append(daily, dt)
	}

	if categories == nil {
		categories = []CategoryTotal{}
	}
	if daily == nil {
		daily = []DailyTotal{}
	}

	summary := ExpenseSummary{
		Categories: categories,
		Daily:      daily,
		Total:      total,
	}

	c.JSON(http.StatusOK, summary)
}

// Get budgets for a user
func getBudgets(c *gin.Context) {
	userID, err := strconv.Atoi(c.Param("user_id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id"})
		return
	}

	rows, err := db.Query(`
		SELECT id, category, amount, period
		FROM budgets
		WHERE user_id = $1
		ORDER BY category
	`, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var budgets []Budget
	for rows.Next() {
		var b Budget
		err := rows.Scan(&b.ID, &b.Category, &b.Amount, &b.Period)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		// Calculate period start date
		now := time.Now()
		var periodStart time.Time

		switch b.Period {
		case "daily":
			periodStart = time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, now.Location())
		case "weekly":
			weekday := int(now.Weekday())
			if weekday == 0 {
				weekday = 7
			}
			periodStart = now.AddDate(0, 0, -(weekday - 1))
			periodStart = time.Date(periodStart.Year(), periodStart.Month(), periodStart.Day(), 0, 0, 0, 0, periodStart.Location())
		case "monthly":
			periodStart = time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, now.Location())
		}

		// Get spent amount for this budget
		var spent sql.NullFloat64
		err = db.QueryRow(`
			SELECT SUM(amount)
			FROM expenses
			WHERE user_id = $1 AND category = $2 AND date >= $3
		`, userID, b.Category, periodStart.Format("2006-01-02")).Scan(&spent)
		if err != nil && err != sql.ErrNoRows {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		b.Spent = 0
		if spent.Valid {
			b.Spent = spent.Float64
		}

		b.Remaining = b.Amount - b.Spent
		if b.Amount > 0 {
			b.Percentage = (b.Spent / b.Amount) * 100
		}

		budgets = append(budgets, b)
	}

	if budgets == nil {
		budgets = []Budget{}
	}

	c.JSON(http.StatusOK, budgets)
}

// Get savings goals for a user
func getSavingsGoals(c *gin.Context) {
	userID, err := strconv.Atoi(c.Param("user_id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id"})
		return
	}

	rows, err := db.Query(`
		SELECT id, COALESCE(goal_name, description) as name, description,
		       target_amount, COALESCE(current_amount, 0) as current_amount,
		       target_date, created_date
		FROM savings_goals
		WHERE user_id = $1
		ORDER BY created_date DESC
	`, userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var goals []SavingsGoal
	for rows.Next() {
		var g SavingsGoal
		err := rows.Scan(&g.ID, &g.Name, &g.Description, &g.TargetAmount, &g.CurrentAmount, &g.TargetDate, &g.CreatedDate)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		if g.TargetAmount > 0 {
			g.Percentage = (g.CurrentAmount / g.TargetAmount) * 100
		}

		goals = append(goals, g)
	}

	if goals == nil {
		goals = []SavingsGoal{}
	}

	c.JSON(http.StatusOK, goals)
}

// Get user info
func getUserInfo(c *gin.Context) {
	userID, err := strconv.Atoi(c.Param("user_id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id"})
		return
	}

	var user User
	user.UserID = userID

	err = db.QueryRow("SELECT user_name, created_date FROM users WHERE user_id = $1", userID).Scan(&user.UserName, &user.CreatedDate)
	if err == sql.ErrNoRows {
		// User not found, return default
		user.UserName = "Пользователь"
		user.CreatedDate = nil
	} else if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, user)
}

func main() {
	// Load .env file if exists
	godotenv.Load()

	// Initialize database
	initDB()
	defer db.Close()

	// Set Gin to release mode in production
	if os.Getenv("GIN_MODE") == "" {
		gin.SetMode(gin.ReleaseMode)
	}

	// Create router
	router := gin.Default()

	// CORS middleware
	config := cors.DefaultConfig()
	config.AllowAllOrigins = true
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	config.AllowHeaders = []string{"Origin", "Content-Type", "Accept"}
	router.Use(cors.New(config))

	// API routes
	api := router.Group("/api")
	{
		api.GET("/health", healthCheck)
		api.GET("/expenses/:user_id", getExpenses)
		api.GET("/expenses-summary/:user_id", getExpensesSummary)
		api.GET("/budgets/:user_id", getBudgets)
		api.GET("/goals/:user_id", getSavingsGoals)
		api.GET("/user/:user_id", getUserInfo)
	}

	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "5000"
	}

	log.Printf("🚀 Server starting on port %s", port)
	if err := router.Run(":" + port); err != nil {
		log.Fatal("❌ Failed to start server:", err)
	}
}
