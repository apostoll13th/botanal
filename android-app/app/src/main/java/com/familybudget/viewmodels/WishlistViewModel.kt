package com.familybudget.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.familybudget.models.CreateWishlistRequest
import com.familybudget.models.UpdateWishlistRequest
import com.familybudget.models.Wishlist
import com.familybudget.network.ApiConfig
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class WishlistUiState(
    val isLoading: Boolean = false,
    val wishlist: List<Wishlist> = emptyList(),
    val error: String? = null,
    val successMessage: String? = null
)

class WishlistViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(WishlistUiState())
    val uiState: StateFlow<WishlistUiState> = _uiState.asStateFlow()

    init {
        loadWishlist()
    }

    fun loadWishlist() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            try {
                val response = ApiConfig.apiService.getWishlist()

                if (response.isSuccessful) {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        wishlist = response.body() ?: emptyList()
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

    fun addWishlistItem(
        title: String,
        description: String?,
        url: String?,
        imageUrl: String?,
        priority: Int
    ) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            try {
                val request = CreateWishlistRequest(
                    title = title,
                    description = description,
                    url = url,
                    imageUrl = imageUrl,
                    priority = priority
                )

                val response = ApiConfig.apiService.createWishlistItem(request)

                if (response.isSuccessful) {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        successMessage = "Желание добавлено"
                    )
                    loadWishlist()
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

    fun toggleCompleted(id: Int, isCompleted: Boolean) {
        viewModelScope.launch {
            try {
                val request = UpdateWishlistRequest(isCompleted = !isCompleted)
                val response = ApiConfig.apiService.updateWishlistItem(id, request)

                if (response.isSuccessful) {
                    loadWishlist()
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    error = "Ошибка обновления: ${e.message}"
                )
            }
        }
    }

    fun deleteWishlistItem(id: Int) {
        viewModelScope.launch {
            try {
                val response = ApiConfig.apiService.deleteWishlistItem(id)
                if (response.isSuccessful) {
                    loadWishlist()
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
