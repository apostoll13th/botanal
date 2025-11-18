package com.familybudget

import android.app.Application
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.familybudget.ui.screens.*
import com.familybudget.ui.components.BottomNavigationBar

class FamilyBudgetApp : Application() {
    override fun onCreate() {
        super.onCreate()
        instance = this
    }

    companion object {
        lateinit var instance: FamilyBudgetApp
            private set
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FamilyBudgetApp() {
    val navController = rememberNavController()
    var currentRoute by remember { mutableStateOf("overview") }

    Scaffold(
        bottomBar = {
            BottomNavigationBar(
                currentRoute = currentRoute,
                onNavigate = { route ->
                    currentRoute = route
                    navController.navigate(route) {
                        popUpTo("overview") { saveState = true }
                        launchSingleTop = true
                        restoreState = true
                    }
                }
            )
        }
    ) { paddingValues ->
        NavHost(
            navController = navController,
            startDestination = "overview",
            modifier = Modifier.padding(paddingValues)
        ) {
            composable("overview") { OverviewScreen() }
            composable("expenses") { ExpensesScreen() }
            composable("budgets") { BudgetsScreen() }
            composable("memos") { MemosScreen() }
            composable("wishlist") { WishlistScreen() }
        }
    }
}
