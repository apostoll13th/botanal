package com.familybudget.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.familybudget.models.Budget
import com.familybudget.models.CreateBudgetRequest
import com.familybudget.network.ApiConfig
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class BudgetsUiState(
    val isLoading: Boolean = false,
    val budgets: List<Budget> = emptyList(),
    val error: String? = null,
    val successMessage: String? = null
)

class BudgetsViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(BudgetsUiState())
    val uiState: StateFlow<BudgetsUiState> = _uiState.asStateFlow()

    init {
        loadBudgets()
    }

    fun loadBudgets() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            try {
                val response = ApiConfig.apiService.getBudgets()

                if (response.isSuccessful) {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        budgets = response.body() ?: emptyList()
                    )
                } else {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = "Ошибка загрузки: ${response.code()}"
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

    fun addBudget(category: String, amount: Double, period: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            try {
                val request = CreateBudgetRequest(
                    category = category,
                    amount = amount,
                    period = period
                )

                val response = ApiConfig.apiService.createBudget(request)

                if (response.isSuccessful) {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        successMessage = "Бюджет успешно добавлен"
                    )
                    loadBudgets()
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

    fun deleteBudget(id: Int) {
        viewModelScope.launch {
            try {
                val response = ApiConfig.apiService.deleteBudget(id)
                if (response.isSuccessful) {
                    loadBudgets()
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
