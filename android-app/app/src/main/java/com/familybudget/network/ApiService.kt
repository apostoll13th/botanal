package com.familybudget.network

import com.familybudget.models.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    // ============ Authentication ============

    @POST("login")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>

    @GET("profile")
    suspend fun getProfile(): Response<AppUser>

    // ============ Expenses/Transactions ============

    @GET("expenses")
    suspend fun getExpenses(
        @Query("period") period: String? = null,
        @Query("category") category: String? = null
    ): Response<List<Expense>>

    @POST("expenses")
    suspend fun createExpense(@Body request: CreateExpenseRequest): Response<Expense>

    @PUT("expenses/{id}")
    suspend fun updateExpense(
        @Path("id") id: Int,
        @Body request: CreateExpenseRequest
    ): Response<Expense>

    @DELETE("expenses/{id}")
    suspend fun deleteExpense(@Path("id") id: Int): Response<Unit>

    @GET("expenses/summary")
    suspend fun getExpenseSummary(
        @Query("period") period: String? = null
    ): Response<ExpenseSummary>

    // ============ Budgets ============

    @GET("budgets")
    suspend fun getBudgets(): Response<List<Budget>>

    @POST("budgets")
    suspend fun createBudget(@Body request: CreateBudgetRequest): Response<Budget>

    @PUT("budgets/{id}")
    suspend fun updateBudget(
        @Path("id") id: Int,
        @Body request: CreateBudgetRequest
    ): Response<Budget>

    @DELETE("budgets/{id}")
    suspend fun deleteBudget(@Path("id") id: Int): Response<Unit>

    // ============ Memos ============

    @GET("memos")
    suspend fun getMemos(): Response<List<Memo>>

    @POST("memos")
    suspend fun createMemo(@Body request: CreateMemoRequest): Response<Memo>

    @PUT("memos/{id}")
    suspend fun updateMemo(
        @Path("id") id: Int,
        @Body request: UpdateMemoRequest
    ): Response<Memo>

    @DELETE("memos/{id}")
    suspend fun deleteMemo(@Path("id") id: Int): Response<Unit>

    // ============ Wishlist ============

    @GET("wishlist")
    suspend fun getWishlist(): Response<List<Wishlist>>

    @POST("wishlist")
    suspend fun createWishlistItem(@Body request: CreateWishlistRequest): Response<Wishlist>

    @PUT("wishlist/{id}")
    suspend fun updateWishlistItem(
        @Path("id") id: Int,
        @Body request: UpdateWishlistRequest
    ): Response<Wishlist>

    @DELETE("wishlist/{id}")
    suspend fun deleteWishlistItem(@Path("id") id: Int): Response<Unit>

    // ============ Categories ============

    @GET("categories")
    suspend fun getCategories(): Response<List<Category>>

    @POST("categories")
    suspend fun createCategory(@Body request: Category): Response<Category>

    // ============ Users ============

    @GET("users")
    suspend fun getUsers(): Response<List<User>>

    @POST("users")
    suspend fun createUser(@Body request: User): Response<User>

    // ============ Savings Goals ============

    @GET("savings-goals")
    suspend fun getSavingsGoals(): Response<List<SavingsGoal>>

    @POST("savings-goals")
    suspend fun createSavingsGoal(@Body request: CreateGoalRequest): Response<SavingsGoal>

    @PUT("savings-goals/{id}")
    suspend fun updateSavingsGoal(
        @Path("id") id: Int,
        @Body request: CreateGoalRequest
    ): Response<SavingsGoal>

    @DELETE("savings-goals/{id}")
    suspend fun deleteSavingsGoal(@Path("id") id: Int): Response<Unit>
}
