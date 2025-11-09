package main

import (
	"database/sql"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
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
	Type        string  `json:"transaction_type"`
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

type Category struct {
	ID          int     `json:"id"`
	Name        string  `json:"name"`
	Type        string  `json:"type"`
	Description *string `json:"description,omitempty"`
}

type createExpenseRequest struct {
	UserID          int     `json:"user_id" binding:"required"`
	Amount          float64 `json:"amount" binding:"required"`
	Category        string  `json:"category" binding:"required"`
	Date            string  `json:"date"`
	Description     string  `json:"description"`
	UserName        string  `json:"user_name"`
	TransactionType string  `json:"transaction_type"`
}

type categoryRequest struct {
	Name        string `json:"name" binding:"required"`
	Type        string `json:"type" binding:"required"`
	Description string `json:"description"`
}

type userRequest struct {
	UserID   int    `json:"user_id" binding:"required"`
	UserName string `json:"user_name" binding:"required"`
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
				if schemaErr := ensureSchema(db); schemaErr != nil {
					log.Printf("⚠️  Schema initialization error: %v", schemaErr)
				} else {
					log.Println("✅ Database schema ready")
					return
				}
			}
		}
		log.Printf("⏳ Waiting for database... (attempt %d/10): %v", i+1, err)
		time.Sleep(3 * time.Second)
	}

	log.Fatal("❌ Failed to connect to database after 10 attempts:", err)
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
	txType := strings.ToLower(c.DefaultQuery("type", "expense"))

	query := "SELECT id, user_id, amount, category, date, description, user_name, transaction_type FROM expenses WHERE user_id = $1"
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

	if txType != "all" {
		if txType != "expense" && txType != "income" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid transaction type"})
			return
		}
		argCount++
		query += fmt.Sprintf(" AND transaction_type = $%d", argCount)
		args = append(args, txType)
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
		err := rows.Scan(&e.ID, &e.UserID, &e.Amount, &e.Category, &e.Date, &e.Description, &e.UserName, &e.Type)
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
		WHERE user_id = $1 AND date >= $2 AND transaction_type = 'expense'
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
		WHERE user_id = $1 AND date >= $2 AND transaction_type = 'expense'
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
			WHERE user_id = $1 AND category = $2 AND date >= $3 AND transaction_type = 'expense'
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

	if err := ensureUserRecord(userID, ""); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

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

// List categories
func listCategories(c *gin.Context) {
	rows, err := db.Query(`SELECT id, name, type, description FROM categories ORDER BY type, name`)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var categories []Category
	for rows.Next() {
		var cat Category
		err := rows.Scan(&cat.ID, &cat.Name, &cat.Type, &cat.Description)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		categories = append(categories, cat)
	}

	if categories == nil {
		categories = []Category{}
	}

	c.JSON(http.StatusOK, categories)
}

// Create or update category
func createCategory(c *gin.Context) {
	var req categoryRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	txType, err := normalizeTransactionType(req.Type)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := ensureCategoryRecord(req.Name, txType, req.Description); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"name":        req.Name,
		"type":        txType,
		"description": req.Description,
	})
}

// Create expense (expense or income)
func createExpense(c *gin.Context) {
	var req createExpenseRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if req.Amount <= 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Amount must be greater than zero"})
		return
	}

	txType := req.TransactionType
	if txType == "" {
		txType = "expense"
	}

	txType, err := normalizeTransactionType(txType)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	txDate := req.Date
	if txDate == "" {
		txDate = time.Now().Format("2006-01-02")
	}

	if err := ensureUserRecord(req.UserID, req.UserName); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	if err := ensureCategoryRecord(req.Category, txType, ""); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	var inserted Expense
	err = db.QueryRow(
		`INSERT INTO expenses (user_id, amount, category, date, description, user_name, transaction_type)
		 VALUES ($1, $2, $3, $4, NULLIF($5, ''), NULLIF($6, ''), $7)
		 RETURNING id, date`,
		req.UserID, req.Amount, req.Category, txDate, req.Description, req.UserName, txType,
	).Scan(&inserted.ID, &inserted.Date)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	inserted.UserID = req.UserID
	inserted.Amount = req.Amount
	inserted.Category = req.Category
	inserted.Description = nullableString(req.Description)
	inserted.UserName = nullableString(req.UserName)
	inserted.Type = txType

	c.JSON(http.StatusCreated, inserted)
}

// Create or update user info
func createOrUpdateUser(c *gin.Context) {
	var req userRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if err := upsertUser(req.UserID, req.UserName); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"user_id": req.UserID, "user_name": req.UserName})
}

func ensureUserRecord(userID int, userName string) error {
	if userName == "" {
		// Try to keep existing name
		var existing string
		err := db.QueryRow(`SELECT user_name FROM users WHERE user_id = $1`, userID).Scan(&existing)
		if err == nil {
			userName = existing
		} else {
			userName = "Пользователь"
		}
	}

	return upsertUser(userID, userName)
}

func upsertUser(userID int, userName string) error {
	if userName == "" {
		userName = "Пользователь"
	}

	_, err := db.Exec(`
		INSERT INTO users (user_id, user_name)
		VALUES ($1, $2)
		ON CONFLICT (user_id) DO UPDATE SET user_name = EXCLUDED.user_name
	`, userID, userName)
	return err
}

func ensureCategoryRecord(name, catType, description string) error {
	if name == "" {
		return errors.New("category name is required")
	}

	_, err := db.Exec(`
		INSERT INTO categories (name, type, description)
		VALUES ($1, $2, NULLIF($3, ''))
		ON CONFLICT (name) DO UPDATE SET type = EXCLUDED.type, description = COALESCE(EXCLUDED.description, categories.description)
	`, name, catType, description)
	return err
}

func normalizeTransactionType(value string) (string, error) {
	switch strings.ToLower(strings.TrimSpace(value)) {
	case "expense", "расход":
		return "expense", nil
	case "income", "доход":
		return "income", nil
	default:
		return "", errors.New("transaction type must be expense or income")
	}
}

func nullableString(value string) *string {
	if strings.TrimSpace(value) == "" {
		return nil
	}
	return &value
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
		api.GET("/categories", listCategories)
		api.POST("/categories", createCategory)
		api.POST("/expenses", createExpense)
		api.POST("/users", createOrUpdateUser)
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
