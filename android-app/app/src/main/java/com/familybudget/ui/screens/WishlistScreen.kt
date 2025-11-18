package com.familybudget.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
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
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import com.familybudget.ui.components.GlassmorphicCard
import com.familybudget.ui.components.GradientCard
import com.familybudget.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WishlistScreen() {
    var showAddDialog by remember { mutableStateOf(false) }

    Scaffold(
        floatingActionButton = {
            FloatingActionButton(
                onClick = { showAddDialog = true },
                containerColor = WishlistPink,
                contentColor = Color.White
            ) {
                Icon(Icons.Filled.Add, "Добавить желание")
            }
        }
    ) { paddingValues ->
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
                .padding(paddingValues)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                GradientCard(
                    colors = listOf(WishlistPink, WishlistRed),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = "🎁 Список желаний",
                        style = MaterialTheme.typography.headlineMedium,
                        color = Color.White,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "Мечтайте вместе!",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White.copy(alpha = 0.9f)
                    )
                }
            }

            items(4) { index ->
                WishlistItem(
                    title = "Желание ${index + 1}",
                    description = "Описание желания с деталями",
                    priority = when (index % 3) {
                        0 -> "Высокий"
                        1 -> "Средний"
                        else -> "Низкий"
                    },
                    imageUrl = null
                )
            }
        }
    }

    if (showAddDialog) {
        AddWishlistDialog(onDismiss = { showAddDialog = false })
    }
}

@Composable
fun WishlistItem(
    title: String,
    description: String,
    priority: String,
    imageUrl: String?
) {
    GlassmorphicCard(
        modifier = Modifier.fillMaxWidth()
    ) {
        Column {
            if (imageUrl != null) {
                AsyncImage(
                    model = imageUrl,
                    contentDescription = title,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(150.dp)
                        .clip(RoundedCornerShape(12.dp)),
                    contentScale = ContentScale.Crop
                )
                Spacer(modifier = Modifier.height(8.dp))
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold
                )
                AssistChip(
                    onClick = {},
                    label = { Text(priority) },
                    colors = AssistChipDefaults.assistChipColors(
                        containerColor = when (priority) {
                            "Высокий" -> ErrorRed.copy(alpha = 0.2f)
                            "Средний" -> WarningOrange.copy(alpha = 0.2f)
                            else -> SuccessGreen.copy(alpha = 0.2f)
                        },
                        labelColor = when (priority) {
                            "Высокий" -> ErrorRedDark
                            "Средний" -> WarningOrangeDark
                            else -> SuccessGreenDark
                        }
                    )
                )
            }

            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = description,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            Spacer(modifier = Modifier.height(12.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = {},
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = SuccessGreen
                    )
                ) {
                    Icon(Icons.Filled.Check, null, modifier = Modifier.size(18.dp))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Исполнено")
                }
                IconButton(onClick = {}) {
                    Icon(Icons.Filled.Edit, "Редактировать")
                }
                IconButton(onClick = {}) {
                    Icon(Icons.Filled.Delete, "Удалить")
                }
            }
        }
    }
}

@Composable
fun AddWishlistDialog(onDismiss: () -> Unit) {
    var title by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Новое желание") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = title,
                    onValueChange = { title = it },
                    label = { Text("Название") },
                    modifier = Modifier.fillMaxWidth()
                )
                OutlinedTextField(
                    value = description,
                    onValueChange = { description = it },
                    label = { Text("Описание") },
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 2
                )
            }
        },
        confirmButton = {
            Button(onClick = onDismiss) {
                Text("Добавить")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Отмена")
            }
        }
    )
}
