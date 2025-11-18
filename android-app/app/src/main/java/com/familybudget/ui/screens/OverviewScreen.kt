package com.familybudget.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.familybudget.models.Expense
import com.familybudget.ui.components.AnimatedGradientCard
import com.familybudget.ui.components.GlassmorphicCard
import com.familybudget.ui.theme.*
import com.familybudget.viewmodels.OverviewViewModel
import java.text.NumberFormat
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OverviewScreen(
    viewModel: OverviewViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val gradientColors = listOf(
        Color(0xFF667eea),
        Color(0xFF764ba2),
        Color(0xFFf093fb)
    )

    Box(modifier = Modifier.fillMaxSize()) {
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    brush = Brush.verticalGradient(
                        colors = listOf(
                            Color(0xFFF8F9FA),
                            Color(0xFFE9ECEF)
                        )
                    )
                )
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Header
            item {
                AnimatedGradientCard(
                    colors = gradientColors,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                text = "💰 Семейный бюджет",
                                style = MaterialTheme.typography.headlineMedium,
                                color = Color.White,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                text = "Добро пожаловать!",
                                style = MaterialTheme.typography.bodyLarge,
                                color = Color.White.copy(alpha = 0.9f)
                            )
                        }
                        Icon(
                            imageVector = Icons.Filled.AccountBalance,
                            contentDescription = null,
                            modifier = Modifier.size(48.dp),
                            tint = Color.White.copy(alpha = 0.8f)
                        )
                    }
                }
            }

            // Error message
            if (uiState.error != null) {
                item {
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = ErrorRed.copy(alpha = 0.1f)
                        ),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier.padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                text = uiState.error ?: "",
                                color = ErrorRed,
                                modifier = Modifier.weight(1f)
                            )
                            TextButton(onClick = { viewModel.retry() }) {
                                Text("Повторить")
                            }
                        }
                    }
                }
            }

            // Summary Cards
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    SummaryCard(
                        modifier = Modifier.weight(1f),
                        title = "Доходы",
                        amount = formatCurrency(uiState.totalIncome),
                        icon = Icons.Filled.TrendingUp,
                        color = SuccessGreen
                    )
                    SummaryCard(
                        modifier = Modifier.weight(1f),
                        title = "Расходы",
                        amount = formatCurrency(uiState.totalExpense),
                        icon = Icons.Filled.TrendingDown,
                        color = ErrorRed
                    )
                }
            }

            item {
                SummaryCard(
                    modifier = Modifier.fillMaxWidth(),
                    title = "Баланс",
                    amount = formatCurrency(uiState.balance),
                    icon = Icons.Filled.AccountBalanceWallet,
                    color = GradientPurpleMiddle,
                    isLarge = true
                )
            }

            // Recent Transactions
            item {
                Text(
                    text = "Последние операции",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(vertical = 8.dp)
                )
            }

            if (uiState.expenses.isEmpty() && !uiState.isLoading) {
                item {
                    Text(
                        text = "Нет операций",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(16.dp)
                    )
                }
            }

            items(uiState.expenses) { expense ->
                TransactionItem(expense = expense)
            }
        }

        // Loading indicator
        if (uiState.isLoading) {
            CircularProgressIndicator(
                modifier = Modifier.align(Alignment.Center)
            )
        }
    }
}

@Composable
fun SummaryCard(
    modifier: Modifier = Modifier,
    title: String,
    amount: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    color: Color,
    isLarge: Boolean = false
) {
    GlassmorphicCard(
        modifier = modifier,
        backgroundColor = MaterialTheme.colorScheme.surface
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
            modifier = Modifier.fillMaxWidth()
        ) {
            Column {
                Text(
                    text = title,
                    style = if (isLarge) MaterialTheme.typography.titleMedium
                           else MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = amount,
                    style = if (isLarge) MaterialTheme.typography.headlineMedium
                           else MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = color
                )
            }
            Box(
                modifier = Modifier
                    .size(if (isLarge) 56.dp else 48.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(color.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = color,
                    modifier = Modifier.size(if (isLarge) 32.dp else 28.dp)
                )
            }
        }
    }
}

@Composable
fun TransactionItem(expense: Expense) {
    val isExpense = expense.transactionType == "expense"

    GlassmorphicCard(
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(48.dp)
                        .clip(RoundedCornerShape(12.dp))
                        .background(
                            if (isExpense) ErrorRed.copy(alpha = 0.15f)
                            else SuccessGreen.copy(alpha = 0.15f)
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = if (isExpense) Icons.Filled.RemoveCircle
                                     else Icons.Filled.AddCircle,
                        contentDescription = null,
                        tint = if (isExpense) ErrorRed else SuccessGreen
                    )
                }
                Column {
                    Text(
                        text = expense.description ?: expense.category,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Medium
                    )
                    Text(
                        text = "${expense.category} • ${expense.date}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            Text(
                text = if (isExpense) "-${formatCurrency(expense.amount)}"
                       else "+${formatCurrency(expense.amount)}",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = if (isExpense) ErrorRed else SuccessGreen
            )
        }
    }
}

private fun formatCurrency(amount: Double): String {
    val format = NumberFormat.getCurrencyInstance(Locale("ru", "RU"))
    format.maximumFractionDigits = 0
    return format.format(amount).replace("RUB", "₽")
}
