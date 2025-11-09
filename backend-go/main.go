package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"database/sql"
	"encoding/base64"
	"encoding/json"
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
	"golang.org/x/crypto/bcrypt"
)

var (
	db        *sql.DB
	jwtSecret []byte
)

var defaultAppUserSeeds = []appUserRequest{
	{
		Login:          "admin",
		Password:       "adminStrongPass!",
		FullName:       "Администратор",
		Role:           "admin",
		TelegramUserID: 101010,
	},
	{
		Login:          "analyst",
		Password:       "analystGo#2024",
		FullName:       "Финансовый аналитик",
		Role:           "analyst",
		TelegramUserID: 202020,
	},
}

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

type AppUser struct {
	ID             int
	Login          string
	PasswordHash   string
	FullName       *string
	Role           string
	TelegramUserID int64
}

type tokenPayload struct {
	UserID         int    `json:"uid"`
	TelegramUserID int64  `json:"tid"`
	Login          string `json:"login"`
	Role           string `json:"role"`
	ExpiresAt      int64  `json:"exp"`
}

type Category struct {
	ID          int     `json:"id"`
	Name        string  `json:"name"`
	Type        string  `json:"type"`
	Description *string `json:"description,omitempty"`
}

type createExpenseRequest struct {
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

type loginRequest struct {
	Login    string `json:"login" binding:"required"`
	Password string `json:"password" binding:"required"`
}

type loginResponse struct {
	Token string `json:"token"`
	User  any    `json:"user"`
}

type appUserRequest struct {
	Login          string `json:"login" binding:"required"`
	Password       string `json:"password"`
	FullName       string `json:"full_name"`
	Role           string `json:"role" binding:"required"`
	TelegramUserID int64  `json:"telegram_user_id" binding:"required"`
}

type appUserResponse struct {
	ID             int     `json:"id"`
	Login          string  `json:"login"`
	FullName       *string `json:"full_name,omitempty"`
	Role           string  `json:"role"`
	TelegramUserID int64   `json:"telegram_user_id"`
}

type appUserUpdateRequest struct {
	Login          *string `json:"login"`
	Password       *string `json:"password"`
	FullName       *string `json:"full_name"`
	Role           *string `json:"role"`
	TelegramUserID *int64  `json:"telegram_user_id"`
}

type createBudgetRequest struct {
	Category string  `json:"category" binding:"required"`
	Amount   float64 `json:"amount" binding:"required"`
	Period   string  `json:"period" binding:"required"`
}

type createGoalRequest struct {
	Name          string  `json:"name" binding:"required"`
	Description   string  `json:"description"`
	TargetAmount  float64 `json:"target_amount" binding:"required"`
	TargetDate    string  `json:"target_date"`
	CurrentAmount float64 `json:"current_amount"`
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
					if seedErr := seedDefaultAppUsers(); seedErr != nil {
						log.Printf("⚠️  Cannot seed default users: %v", seedErr)
					}
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
	userID := getTelegramUserID(c)
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
	userID := getTelegramUserID(c)

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
	userID := getTelegramUserID(c)

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

func createBudgetHandler(c *gin.Context) {
	var req createBudgetRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if req.Amount <= 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Amount must be greater than zero"})
		return
	}

	userID := getTelegramUserID(c)
	if userID == 0 {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Не удалось определить пользователя"})
		return
	}

	period := normalizeBudgetPeriod(req.Period)
	if period == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Некорректный период (daily/weekly/monthly)"})
		return
	}

	startDate := time.Now().Format("2006-01-02")

	tx, err := db.Begin()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	defer tx.Rollback()

	var budgetID int
	err = tx.QueryRow(`
		SELECT id FROM budgets
		WHERE user_id = $1 AND category = $2 AND period = $3
	`, userID, req.Category, period).Scan(&budgetID)

	if err == sql.ErrNoRows {
		_, err = tx.Exec(`
			INSERT INTO budgets (user_id, category, amount, period, start_date)
			VALUES ($1, $2, $3, $4, $5)
		`, userID, req.Category, req.Amount, period, startDate)
	} else if err == nil {
		_, err = tx.Exec(`
			UPDATE budgets
			SET amount = $1, start_date = $2
			WHERE id = $3
		`, req.Amount, startDate, budgetID)
	}

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	if err := tx.Commit(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.Status(http.StatusCreated)
}

// Get savings goals for a user
func getSavingsGoals(c *gin.Context) {
	userID := getTelegramUserID(c)

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

func createSavingsGoalHandler(c *gin.Context) {
	var req createGoalRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if req.TargetAmount <= 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Target amount must be greater than zero"})
		return
	}

	userID := getTelegramUserID(c)
	if userID == 0 {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Не удалось определить пользователя"})
		return
	}

	if err := ensureUserRecord(userID, req.Name); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	var userName string
	err := db.QueryRow(`SELECT user_name FROM users WHERE user_id = $1`, userID).Scan(&userName)
	if err != nil && err != sql.ErrNoRows {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	if userName == "" {
		userName = "Пользователь"
	}

	var targetDate interface{}
	if strings.TrimSpace(req.TargetDate) != "" {
		parsed, err := time.Parse("2006-01-02", req.TargetDate)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Некорректная дата (используйте формат YYYY-MM-DD)"})
			return
		}
		targetDate = parsed
	}

	_, err = db.Exec(`
		INSERT INTO savings_goals (
			user_id, description, target_amount, current_amount,
			target_date, created_date, goal_name, user_name
		) VALUES ($1, NULLIF($2, ''), $3, $4, $5, CURRENT_DATE, $6, $7)
	`, userID, req.Description, req.TargetAmount, req.CurrentAmount, targetDate, req.Name, userName)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.Status(http.StatusCreated)
}

// Get user info
func getCurrentUserInfo(c *gin.Context) {
	userID := getTelegramUserID(c)
	var user User
	user.UserID = int(userID)

	if err := ensureUserRecord(userID, ""); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	err := db.QueryRow("SELECT user_name, created_date FROM users WHERE user_id = $1", userID).Scan(&user.UserName, &user.CreatedDate)
	if err == sql.ErrNoRows {
		user.UserName = "Пользователь"
		user.CreatedDate = nil
	} else if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, user)
}

func loginHandler(c *gin.Context) {
	var req loginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user, err := getAppUserByLogin(strings.TrimSpace(req.Login))
	if err == sql.ErrNoRows || user == nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Неверный логин или пароль"})
		return
	} else if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password)); err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Неверный логин или пароль"})
		return
	}

	token, err := generateToken(*user)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Не удалось выдать токен"})
		return
	}

	responseUser := gin.H{
		"id":               user.ID,
		"login":            user.Login,
		"role":             user.Role,
		"telegram_user_id": user.TelegramUserID,
	}
	if user.FullName != nil {
		responseUser["full_name"] = *user.FullName
	}

	c.JSON(http.StatusOK, loginResponse{
		Token: token,
		User:  responseUser,
	})
}

func currentUserHandler(c *gin.Context) {
	login := c.GetString("app_user_login")
	user, err := getAppUserByLogin(login)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	response := gin.H{
		"id":               user.ID,
		"login":            user.Login,
		"role":             user.Role,
		"telegram_user_id": user.TelegramUserID,
	}
	if user.FullName != nil {
		response["full_name"] = *user.FullName
	}

	c.JSON(http.StatusOK, response)
}

func authMiddleware(c *gin.Context) {
	authHeader := c.GetHeader("Authorization")
	if authHeader == "" || !strings.HasPrefix(authHeader, "Bearer ") {
		c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Требуется авторизация"})
		return
	}

	tokenString := strings.TrimSpace(strings.TrimPrefix(authHeader, "Bearer "))
	parts := strings.Split(tokenString, ".")
	if len(parts) != 2 {
		c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Недействительный токен"})
		return
	}

	payloadBytes, err := base64.RawURLEncoding.DecodeString(parts[0])
	if err != nil {
		c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Недействительный токен"})
		return
	}

	signatureBytes, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Недействительный токен"})
		return
	}

	mac := hmac.New(sha256.New, jwtSecret)
	mac.Write(payloadBytes)
	expectedSig := mac.Sum(nil)

	if !hmac.Equal(signatureBytes, expectedSig) {
		c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Недействительный токен"})
		return
	}

	var payload tokenPayload
	if err := json.Unmarshal(payloadBytes, &payload); err != nil {
		c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Недействительный токен"})
		return
	}

	if time.Now().Unix() > payload.ExpiresAt {
		c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Срок действия токена истёк"})
		return
	}

	c.Set("app_user_id", payload.UserID)
	c.Set("telegram_user_id", payload.TelegramUserID)
	c.Set("app_user_login", payload.Login)
	c.Set("app_user_role", payload.Role)

	c.Next()
}

func getTelegramUserID(c *gin.Context) int64 {
	if v, exists := c.Get("telegram_user_id"); exists {
		if id, ok := v.(int64); ok {
			return id
		}
	}
	return 0
}

func requireAdminRole(c *gin.Context) {
	role := c.GetString("app_user_role")
	if role != "admin" {
		c.AbortWithStatusJSON(http.StatusForbidden, gin.H{"error": "Недостаточно прав"})
		return
	}
	c.Next()
}

func getAppUserByLogin(login string) (*AppUser, error) {
	var (
		user     AppUser
		fullName sql.NullString
	)

	err := db.QueryRow(`
		SELECT id, login, password_hash, full_name, role, telegram_user_id
		FROM app_users
		WHERE login = $1
	`, login).Scan(&user.ID, &user.Login, &user.PasswordHash, &fullName, &user.Role, &user.TelegramUserID)
	if err != nil {
		return nil, err
	}

	if fullName.Valid {
		user.FullName = &fullName.String
	}

	return &user, nil
}

func generateToken(user AppUser) (string, error) {
	payload := tokenPayload{
		UserID:         user.ID,
		TelegramUserID: user.TelegramUserID,
		Login:          user.Login,
		Role:           user.Role,
		ExpiresAt:      time.Now().Add(24 * time.Hour).Unix(),
	}

	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}

	mac := hmac.New(sha256.New, jwtSecret)
	mac.Write(payloadBytes)
	signature := mac.Sum(nil)

	encodedPayload := base64.RawURLEncoding.EncodeToString(payloadBytes)
	encodedSignature := base64.RawURLEncoding.EncodeToString(signature)

	return fmt.Sprintf("%s.%s", encodedPayload, encodedSignature), nil
}

func listAppUsersHandler(c *gin.Context) {
	rows, err := db.Query(`
		SELECT id, login, full_name, role, telegram_user_id
		FROM app_users
		ORDER BY id
	`)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var users []appUserResponse
	for rows.Next() {
		var (
			u       appUserResponse
			fullRaw sql.NullString
		)
		if err := rows.Scan(&u.ID, &u.Login, &fullRaw, &u.Role, &u.TelegramUserID); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		if fullRaw.Valid {
			full := fullRaw.String
			u.FullName = &full
		}
		users = append(users, u)
	}

	if users == nil {
		users = []appUserResponse{}
	}

	c.JSON(http.StatusOK, users)
}

func createAppUserHandler(c *gin.Context) {
	var req appUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if strings.TrimSpace(req.Password) == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Пароль обязателен"})
		return
	}
	if err := validateRole(req.Role); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user, err := insertAppUser(req)
	if err != nil {
		if strings.Contains(err.Error(), "duplicate key value") {
			c.JSON(http.StatusConflict, gin.H{"error": "Логин уже существует"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, appUserToResponse(*user))
}

func updateAppUserHandler(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Некорректный идентификатор"})
		return
	}

	existing, err := getAppUserByID(id)
	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": "Пользователь не найден"})
		return
	} else if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	var req appUserUpdateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	login := existing.Login
	if req.Login != nil && strings.TrimSpace(*req.Login) != "" {
		login = strings.TrimSpace(*req.Login)
	}

	role := existing.Role
	if req.Role != nil && strings.TrimSpace(*req.Role) != "" {
		role = strings.TrimSpace(*req.Role)
	}
	if err := validateRole(role); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	passwordHash := existing.PasswordHash
	if req.Password != nil && strings.TrimSpace(*req.Password) != "" {
		passwordHash, err = hashPassword(*req.Password)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
	}

	fullName := existing.FullName
	if req.FullName != nil {
		if strings.TrimSpace(*req.FullName) == "" {
			fullName = nil
		} else {
			value := strings.TrimSpace(*req.FullName)
			fullName = &value
		}
	}

	telegramID := existing.TelegramUserID
	if req.TelegramUserID != nil && *req.TelegramUserID != 0 {
		telegramID = *req.TelegramUserID
	}

	_, err = db.Exec(`
		UPDATE app_users
		SET login = $1,
		    password_hash = $2,
		    full_name = NULLIF($3, ''),
		    role = $4,
		    telegram_user_id = $5
		WHERE id = $6
	`, login, passwordHash, nullableStringValue(fullName), role, telegramID, id)
	if err != nil {
		if strings.Contains(err.Error(), "duplicate key value") {
			c.JSON(http.StatusConflict, gin.H{"error": "Логин уже существует"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	if err := ensureUserRecord(telegramID, nullableStringValue(fullName)); err != nil {
		log.Printf("warning: couldn't sync users table: %v", err)
	}

	updated := AppUser{
		ID:             id,
		Login:          login,
		PasswordHash:   passwordHash,
		FullName:       fullName,
		Role:           role,
		TelegramUserID: telegramID,
	}

	c.JSON(http.StatusOK, appUserToResponse(updated))
}

func deleteAppUserHandler(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Некорректный идентификатор"})
		return
	}

	if _, err := db.Exec(`DELETE FROM app_users WHERE id = $1`, id); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.Status(http.StatusNoContent)
}

func appUserToResponse(user AppUser) appUserResponse {
	resp := appUserResponse{
		ID:             user.ID,
		Login:          user.Login,
		Role:           user.Role,
		TelegramUserID: user.TelegramUserID,
	}
	if user.FullName != nil {
		resp.FullName = user.FullName
	}
	return resp
}

func hashPassword(password string) (string, error) {
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", err
	}
	return string(hash), nil
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

	userID := getTelegramUserID(c)
	if userID == 0 {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Не удалось определить пользователя"})
		return
	}

	if err := ensureUserRecord(userID, req.UserName); err != nil {
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
		userID, req.Amount, req.Category, txDate, req.Description, req.UserName, txType,
	).Scan(&inserted.ID, &inserted.Date)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	inserted.UserID = int(userID)
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

	if err := upsertUser(int64(req.UserID), req.UserName); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"user_id": req.UserID, "user_name": req.UserName})
}

func ensureUserRecord(userID int64, userName string) error {
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

func upsertUser(userID int64, userName string) error {
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

func nullableStringValue(value *string) string {
	if value == nil {
		return ""
	}
	return *value
}

func validateRole(role string) error {
	switch role {
	case "admin", "analyst":
		return nil
	default:
		return errors.New("Некорректная роль (поддерживаются admin, analyst)")
	}
}

func normalizeBudgetPeriod(period string) string {
	switch strings.ToLower(strings.TrimSpace(period)) {
	case "daily", "day", "день", "дневной":
		return "daily"
	case "weekly", "week", "неделя", "недельный":
		return "weekly"
	case "monthly", "month", "месяц", "месячный":
		return "monthly"
	default:
		return ""
	}
}

func insertAppUser(req appUserRequest) (*AppUser, error) {
	login := strings.TrimSpace(req.Login)
	role := strings.TrimSpace(req.Role)
	if err := validateRole(role); err != nil {
		return nil, err
	}
	passwordHash, err := hashPassword(req.Password)
	if err != nil {
		return nil, err
	}

	fullName := strings.TrimSpace(req.FullName)
	var fullPtr *string
	if fullName != "" {
		fullPtr = &fullName
	}

	var id int
	err = db.QueryRow(`
		INSERT INTO app_users (login, password_hash, full_name, role, telegram_user_id)
		VALUES ($1, $2, NULLIF($3, ''), $4, $5)
		RETURNING id
	`, login, passwordHash, fullName, role, req.TelegramUserID).Scan(&id)
	if err != nil {
		return nil, err
	}

	if err := ensureUserRecord(req.TelegramUserID, fullName); err != nil {
		return nil, err
	}

	return &AppUser{
		ID:             id,
		Login:          login,
		PasswordHash:   passwordHash,
		FullName:       fullPtr,
		Role:           role,
		TelegramUserID: req.TelegramUserID,
	}, nil
}

func getAppUserByID(id int) (*AppUser, error) {
	var (
		user    AppUser
		fullRaw sql.NullString
	)
	err := db.QueryRow(`
		SELECT id, login, password_hash, full_name, role, telegram_user_id
		FROM app_users
		WHERE id = $1
	`, id).Scan(&user.ID, &user.Login, &user.PasswordHash, &fullRaw, &user.Role, &user.TelegramUserID)
	if err != nil {
		return nil, err
	}
	if fullRaw.Valid {
		value := fullRaw.String
		user.FullName = &value
	}
	return &user, nil
}

func seedDefaultAppUsers() error {
	for _, seed := range defaultAppUserSeeds {
		_, err := getAppUserByLogin(seed.Login)
		if err == sql.ErrNoRows {
			if _, err := insertAppUser(seed); err != nil {
				return err
			}
			continue
		} else if err != nil {
			return err
		}
	}
	return nil
}

func main() {
	// Load .env file if exists
	godotenv.Load()

	authSecret := os.Getenv("AUTH_SECRET")
	if strings.TrimSpace(authSecret) == "" {
		authSecret = "change-me"
	}
	jwtSecret = []byte(authSecret)

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
	router.GET("/api/health", healthCheck)
	router.POST("/api/auth/login", loginHandler)

	api := router.Group("/api")
	api.Use(authMiddleware)
	{
		api.GET("/me", currentUserHandler)
		api.GET("/user", getCurrentUserInfo)
		api.GET("/expenses", getExpenses)
		api.GET("/expenses-summary", getExpensesSummary)
		api.GET("/budgets", getBudgets)
		api.POST("/budgets", createBudgetHandler)
		api.GET("/goals", getSavingsGoals)
		api.POST("/goals", createSavingsGoalHandler)
		api.GET("/categories", listCategories)
		api.POST("/categories", createCategory)
		api.POST("/expenses", createExpense)
		api.POST("/users", createOrUpdateUser)
	}

	admin := api.Group("/admin")
	admin.Use(requireAdminRole)
	{
		admin.GET("/users", listAppUsersHandler)
		admin.POST("/users", createAppUserHandler)
		admin.PUT("/users/:id", updateAppUserHandler)
		admin.DELETE("/users/:id", deleteAppUserHandler)
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
