package main

import (
	"database/sql"
	"fmt"
	"log"
	"strings"
)

type migration struct {
	version     int
	description string
	up          func(tx *sql.Tx) error
}

func ensureSchema(database *sql.DB) error {
	if err := createBaseTables(database); err != nil {
		return fmt.Errorf("create base tables: %w", err)
	}

	if err := runMigrations(database); err != nil {
		return fmt.Errorf("run migrations: %w", err)
	}

	return nil
}

func createBaseTables(database *sql.DB) error {
	statements := []string{
		`
		CREATE TABLE IF NOT EXISTS migrations (
			id SERIAL PRIMARY KEY,
			version INTEGER UNIQUE NOT NULL,
			description TEXT,
			applied_at TIMESTAMP NOT NULL
		)
		`,
		`
		CREATE TABLE IF NOT EXISTS users (
			user_id BIGINT PRIMARY KEY,
			user_name TEXT NOT NULL,
			created_date DATE NOT NULL DEFAULT CURRENT_DATE
		)
		`,
		`
		CREATE TABLE IF NOT EXISTS expenses (
			id SERIAL PRIMARY KEY,
			user_id BIGINT NOT NULL,
			amount NUMERIC(12, 2) NOT NULL,
			category TEXT NOT NULL,
			date DATE NOT NULL,
			user_name TEXT,
			description TEXT
		)
		`,
		`
		CREATE TABLE IF NOT EXISTS budgets (
			id SERIAL PRIMARY KEY,
			user_id BIGINT NOT NULL,
			category TEXT NOT NULL,
			amount NUMERIC(12, 2) NOT NULL,
			period TEXT NOT NULL,
			start_date DATE NOT NULL,
			user_name TEXT
		)
		`,
		`
		CREATE TABLE IF NOT EXISTS savings_goals (
			id SERIAL PRIMARY KEY,
			user_id BIGINT NOT NULL,
			description TEXT NOT NULL,
			target_amount NUMERIC(12, 2) NOT NULL,
			current_amount NUMERIC(12, 2) DEFAULT 0,
			target_date DATE,
			created_date DATE NOT NULL,
			goal_name TEXT,
			user_name TEXT
		)
		`,
		`
		CREATE TABLE IF NOT EXISTS reminders (
			id SERIAL PRIMARY KEY,
			user_id BIGINT NOT NULL,
			message TEXT NOT NULL,
			frequency TEXT NOT NULL,
			next_reminder_date DATE NOT NULL,
			created_date DATE NOT NULL
		)
		`,
		`
		CREATE TABLE IF NOT EXISTS categories (
			id SERIAL PRIMARY KEY,
			name TEXT UNIQUE NOT NULL,
			type TEXT NOT NULL CHECK (type IN ('expense', 'income')),
			description TEXT,
			created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
		)
		`,
		`
		CREATE TABLE IF NOT EXISTS app_users (
			id SERIAL PRIMARY KEY,
			login TEXT UNIQUE NOT NULL,
			password_hash TEXT NOT NULL,
			full_name TEXT,
			role TEXT NOT NULL DEFAULT 'analyst',
			telegram_user_id BIGINT NOT NULL,
			created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
		)
		`,
	}

	for _, stmt := range statements {
		cleanStmt := strings.TrimSpace(stmt)
		if cleanStmt == "" {
			continue
		}

		if _, err := database.Exec(cleanStmt); err != nil {
			return fmt.Errorf("exec schema statement %q: %w", cleanStmt, err)
		}
	}

	return nil
}

func runMigrations(database *sql.DB) error {
	ensureVersionSQL := `
		INSERT INTO migrations (version, description, applied_at)
		SELECT $1, $2, NOW()
		WHERE NOT EXISTS (SELECT 1 FROM migrations WHERE version = $1)
	`

	migrations := []migration{
		{
			version:     1,
			description: "Add transaction_type column to expenses",
			up: func(tx *sql.Tx) error {
				if _, err := tx.Exec(`ALTER TABLE expenses ADD COLUMN IF NOT EXISTS transaction_type TEXT NOT NULL DEFAULT 'expense'`); err != nil {
					return err
				}
				if _, err := tx.Exec(`UPDATE expenses SET transaction_type = 'expense' WHERE transaction_type IS NULL OR transaction_type = ''`); err != nil {
					return err
				}
				return nil
			},
		},
		{
			version:     2,
			description: "Seed categories table from existing expenses",
			up: func(tx *sql.Tx) error {
				_, err := tx.Exec(`
					INSERT INTO categories (name, type)
					SELECT DISTINCT category, 'expense'
					FROM expenses
					WHERE category IS NOT NULL AND category <> ''
					ON CONFLICT (name) DO NOTHING
				`)
				return err
			},
		},
		{
			version:     3,
			description: "Seed default app users",
			up: func(tx *sql.Tx) error {
				if _, err := tx.Exec(`
					INSERT INTO users (user_id, user_name, created_date)
					VALUES
						(101010, 'Admin', CURRENT_DATE),
						(202020, 'Lead Analyst', CURRENT_DATE)
					ON CONFLICT (user_id) DO NOTHING
				`); err != nil {
					return err
				}

				_, err := tx.Exec(`
					INSERT INTO app_users (login, password_hash, full_name, role, telegram_user_id)
					VALUES
						('admin', '$2a$10$es8RMLseezG07WLrP2nbcuUVHtDHyGtdInIHD51bDu4JRPR70i3V2', 'Администратор', 'admin', 101010),
						('analyst', '$2a$10$6fx5LKhApNPGgW994lFiYO8sP691iYiADU9UVDybasM6jWFuWHdp2', 'Финансовый аналитик', 'analyst', 202020)
					ON CONFLICT (login) DO NOTHING
				`)
				return err
			},
		},
	}

	for _, m := range migrations {
		if applied, err := migrationApplied(database, m.version); err != nil {
			return err
		} else if applied {
			continue
		}

		log.Printf("Applying migration %d: %s", m.version, m.description)
		tx, err := database.Begin()
		if err != nil {
			return fmt.Errorf("start migration tx: %w", err)
		}

		if err := m.up(tx); err != nil {
			tx.Rollback()
			return fmt.Errorf("run migration %d: %w", m.version, err)
		}

		if _, err := tx.Exec(ensureVersionSQL, m.version, m.description); err != nil {
			tx.Rollback()
			return fmt.Errorf("record migration %d: %w", m.version, err)
		}

		if err := tx.Commit(); err != nil {
			return fmt.Errorf("commit migration %d: %w", m.version, err)
		}

		log.Printf("Migration %d applied", m.version)
	}

	return nil
}

func migrationApplied(database *sql.DB, version int) (bool, error) {
	var count int
	if err := database.QueryRow(`SELECT COUNT(1) FROM migrations WHERE version = $1`, version).Scan(&count); err != nil {
		return false, err
	}
	return count > 0, nil
}
