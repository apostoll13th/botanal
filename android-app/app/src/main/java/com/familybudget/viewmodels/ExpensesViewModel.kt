package com.familybudget.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.familybudget.models.Category
import com.familybudget.models.CreateExpenseRequest
import com.familybudget.models.Expense
import com.familybudget.network.ApiConfig
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

data class ExpensesUiState(
    val isLoading: Boolean = false,
    val expenses: List<Expense> = emptyList(),
    val categories: List<Category> = emptyList(),
    val error: String? = null,
    val successMessage: String? = null
)

class ExpensesViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(ExpensesUiState())
    val uiState: StateFlow<ExpensesUiState> = _uiState.asStateFlow()

    init {
        loadData()
    }

    fun loadData() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            try {
                // Load expenses
                val expensesResponse = ApiConfig.apiService.getExpenses()
                val categoriesResponse = ApiConfig.apiService.getCategories()

                if (expensesResponse.isSuccessful && categoriesResponse.isSuccessful) {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        expenses = expensesResponse.body() ?: emptyList(),
                        categories = categoriesResponse.body() ?: emptyList()
                    )
                } else {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = "Ошибка загрузки данных"
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

    fun addExpense(
        amount: Double,
        category: String,
        description: String,
        transactionType: String
    ) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            try {
                val dateFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
                val currentDate = dateFormat.format(Date())

                val request = CreateExpenseRequest(
                    amount = amount,
                    category = category,
                    date = currentDate,
                    description = description,
                    transactionType = transactionType
                )

                val response = ApiConfig.apiService.createExpense(request)

                if (response.isSuccessful) {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        successMessage = "Операция успешно добавлена"
                    )
                    loadData() // Reload the list
                } else {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = "Ошибка при добавлении: ${response.code()}"
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

    fun deleteExpense(id: Int) {
        viewModelScope.launch {
            try {
                val response = ApiConfig.apiService.deleteExpense(id)
                if (response.isSuccessful) {
                    loadData() // Reload the list
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    error = "Ошибка удаления: ${e.message}"
                )
            }
        }
    }

    fun clearMessages() {
        _uiState.value = _uiState.value.copy(error = null, successMessage = null)
    }
}
