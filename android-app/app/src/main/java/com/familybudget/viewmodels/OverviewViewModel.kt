package com.familybudget.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.familybudget.models.Expense
import com.familybudget.models.ExpenseSummary
import com.familybudget.network.ApiConfig
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class OverviewUiState(
    val isLoading: Boolean = false,
    val expenses: List<Expense> = emptyList(),
    val summary: ExpenseSummary? = null,
    val totalIncome: Double = 0.0,
    val totalExpense: Double = 0.0,
    val balance: Double = 0.0,
    val error: String? = null
)

class OverviewViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(OverviewUiState())
    val uiState: StateFlow<OverviewUiState> = _uiState.asStateFlow()

    init {
        loadData()
    }

    fun loadData() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            try {
                // Load recent expenses
                val expensesResponse = ApiConfig.apiService.getExpenses(period = "monthly")

                if (expensesResponse.isSuccessful) {
                    val expenses = expensesResponse.body() ?: emptyList()

                    // Calculate totals
                    val totalIncome = expenses
                        .filter { it.transactionType == "income" }
                        .sumOf { it.amount }

                    val totalExpense = expenses
                        .filter { it.transactionType == "expense" }
                        .sumOf { it.amount }

                    val balance = totalIncome - totalExpense

                    // Get recent transactions (last 5)
                    val recentExpenses = expenses
                        .sortedByDescending { it.date }
                        .take(5)

                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        expenses = recentExpenses,
                        totalIncome = totalIncome,
                        totalExpense = totalExpense,
                        balance = balance
                    )
                } else {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = "Ошибка загрузки: ${expensesResponse.code()}"
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "Ошибка сети: ${e.message}"
                )
            }
        }
    }

    fun retry() {
        loadData()
    }
}
