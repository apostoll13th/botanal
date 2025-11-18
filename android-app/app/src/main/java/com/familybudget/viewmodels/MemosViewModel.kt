package com.familybudget.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.familybudget.models.CreateMemoRequest
import com.familybudget.models.Memo
import com.familybudget.models.UpdateMemoRequest
import com.familybudget.network.ApiConfig
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class MemosUiState(
    val isLoading: Boolean = false,
    val memos: List<Memo> = emptyList(),
    val error: String? = null,
    val successMessage: String? = null
)

class MemosViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(MemosUiState())
    val uiState: StateFlow<MemosUiState> = _uiState.asStateFlow()

    init {
        loadMemos()
    }

    fun loadMemos() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            try {
                val response = ApiConfig.apiService.getMemos()

                if (response.isSuccessful) {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        memos = response.body() ?: emptyList()
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

    fun addMemo(title: String, content: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            try {
                val request = CreateMemoRequest(
                    title = title,
                    content = content
                )

                val response = ApiConfig.apiService.createMemo(request)

                if (response.isSuccessful) {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        successMessage = "Запись успешно добавлена"
                    )
                    loadMemos()
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

    fun updateMemo(id: Int, title: String, content: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            try {
                val request = UpdateMemoRequest(
                    title = title,
                    content = content
                )

                val response = ApiConfig.apiService.updateMemo(id, request)

                if (response.isSuccessful) {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        successMessage = "Запись обновлена"
                    )
                    loadMemos()
                } else {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = "Ошибка обновления: ${response.code()}"
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

    fun deleteMemo(id: Int) {
        viewModelScope.launch {
            try {
                val response = ApiConfig.apiService.deleteMemo(id)
                if (response.isSuccessful) {
                    loadMemos()
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
