package com.familybudget.models

import com.google.gson.annotations.SerializedName

// Expense/Transaction models
data class Expense(
    val id: Int = 0,
    @SerializedName("user_id")
    val userId: Int = 0,
    val amount: Double,
    val category: String,
    val date: String,
    val description: String? = null,
    @SerializedName("user_name")
    val userName: String? = null,
    @SerializedName("transaction_type")
    val transactionType: String = "expense" // "expense" or "income"
)

data class CreateExpenseRequest(
    val amount: Double,
    val category: String,
    val date: String? = null,
    val description: String = "",
    @SerializedName("user_name")
    val userName: String = "",
    @SerializedName("transaction_type")
    val transactionType: String = "expense"
)

data class ExpenseSummary(
    val categories: List<CategoryTotal>,
    val daily: List<DailyTotal>,
    val total: Double
)

data class CategoryTotal(
    val category: String,
    val amount: Double
)

data class DailyTotal(
    val date: String,
    val amount: Double
)

// Budget models
data class Budget(
    val id: Int = 0,
    val category: String,
    val amount: Double,
    val period: String,
    val spent: Double = 0.0,
    val remaining: Double = 0.0,
    val percentage: Double = 0.0
)

data class CreateBudgetRequest(
    val category: String,
    val amount: Double,
    val period: String
)

// Memos models
data class Memo(
    val id: Int = 0,
    @SerializedName("user_id")
    val userId: Int = 0,
    val title: String,
    val content: String,
    @SerializedName("created_at")
    val createdAt: String,
    @SerializedName("updated_at")
    val updatedAt: String
)

data class CreateMemoRequest(
    val title: String = "",
    val content: String
)

data class UpdateMemoRequest(
    val title: String? = null,
    val content: String? = null
)

// Wishlist models
data class Wishlist(
    val id: Int = 0,
    @SerializedName("user_id")
    val userId: Int = 0,
    val title: String,
    val description: String? = null,
    val url: String? = null,
    @SerializedName("image_url")
    val imageUrl: String? = null,
    val priority: Int = 2, // 1=High, 2=Medium, 3=Low
    @SerializedName("is_completed")
    val isCompleted: Boolean = false,
    @SerializedName("created_at")
    val createdAt: String,
    @SerializedName("updated_at")
    val updatedAt: String
)

data class CreateWishlistRequest(
    val title: String,
    val description: String? = null,
    val url: String? = null,
    @SerializedName("image_url")
    val imageUrl: String? = null,
    val priority: Int = 2
)

data class UpdateWishlistRequest(
    val title: String? = null,
    val description: String? = null,
    val url: String? = null,
    @SerializedName("image_url")
    val imageUrl: String? = null,
    val priority: Int? = null,
    @SerializedName("is_completed")
    val isCompleted: Boolean? = null
)

// Category models
data class Category(
    val id: Int = 0,
    val name: String,
    val type: String, // "expense" or "income"
    val description: String? = null
)

// User models
data class User(
    @SerializedName("user_id")
    val userId: Int,
    @SerializedName("user_name")
    val userName: String,
    @SerializedName("created_date")
    val createdDate: String? = null
)

// Auth models
data class LoginRequest(
    val login: String,
    val password: String
)

data class LoginResponse(
    val token: String,
    val user: AppUser
)

data class AppUser(
    val id: Int = 0,
    val login: String,
    @SerializedName("full_name")
    val fullName: String? = null,
    val role: String = "user",
    @SerializedName("telegram_user_id")
    val telegramUserId: Long = 0
)

// Savings Goal models
data class SavingsGoal(
    val id: Int = 0,
    val name: String,
    val description: String,
    @SerializedName("target_amount")
    val targetAmount: Double,
    @SerializedName("current_amount")
    val currentAmount: Double,
    @SerializedName("target_date")
    val targetDate: String? = null,
    @SerializedName("created_date")
    val createdDate: String,
    val percentage: Double = 0.0
)

data class CreateGoalRequest(
    val name: String,
    val description: String = "",
    @SerializedName("target_amount")
    val targetAmount: Double,
    @SerializedName("target_date")
    val targetDate: String? = null,
    @SerializedName("current_amount")
    val currentAmount: Double = 0.0
)

// API Response wrappers
data class ApiResponse<T>(
    val data: T? = null,
    val error: String? = null
)
