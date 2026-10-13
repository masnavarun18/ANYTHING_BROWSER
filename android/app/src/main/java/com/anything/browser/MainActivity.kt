package com.anything.browser

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

data class TabInfo(
    var url: String = "https://www.google.com",
    var title: String = "Google"
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    primary = Color(0xFF0078D4),
                    background = Color(0xFF121212),
                    surface = Color(0xFF1E1E1E)
                )
            ) {
                AnythingBrowserApp()
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnythingBrowserApp() {
    var tabs by remember { mutableStateOf(listOf(TabInfo())) }
    var currentTabIndex by remember { mutableIntStateOf(0) }
    var urlInput by remember { mutableStateOf("https://www.google.com") }
    var progress by remember { mutableIntStateOf(0) }

    val currentTab = tabs.getOrNull(currentTabIndex) ?: TabInfo()

    LaunchedEffect(currentTabIndex) {
        urlInput = currentTab.url
    }

    Scaffold(
        topBar = {
            Column(modifier = Modifier.background(Color(0xFF1E1E1E))) {
                // Top Action Toolbar
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // URL Input Bar
                    OutlinedTextField(
                        value = urlInput,
                        onValueChange = { urlInput = it },
                        modifier = Modifier
                            .weight(1f)
                            .height(52.dp),
                        singleLine = true,
                        placeholder = { Text("Search or enter URL...", fontSize = 14.sp) },
                        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Go),
                        keyboardActions = KeyboardActions(onGo = {
                            var formatted = urlInput.trim()
                            if (!formatted.startsWith("http://") && !formatted.startsWith("https://")) {
                                formatted = if (formatted.contains(".") && !formatted.contains(" ")) {
                                    "https://$formatted"
                                } else {
                                    "https://www.google.com/search?q=${java.net.URLEncoder.encode(formatted, "UTF-8")}"
                                }
                            }
                            currentTab.url = formatted
                            tabs = tabs.toMutableList().apply { set(currentTabIndex, currentTab) }
                        })
                    )

                    Spacer(modifier = Modifier.width(4.dp))

                    // New Tab Button
                    IconButton(onClick = {
                        tabs = tabs + TabInfo()
                        currentTabIndex = tabs.size - 1
                    }) {
                        Text("+", fontSize = 20.sp, color = Color.White)
                    }
                }

                // Tab Bar
                LazyRow(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 4.dp, vertical = 2.dp)
                ) {
                    itemsIndexed(tabs) { index, tab ->
                        FilterChip(
                            selected = index == currentTabIndex,
                            onClick = { currentTabIndex = index },
                            label = { Text(tab.title, maxLines = 1, fontSize = 12.sp) },
                            modifier = Modifier.padding(end = 4.dp)
                        )
                    }
                }

                if (progress in 1..99) {
                    LinearProgressIndicator(
                        progress = { progress / 100f },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            BrowserWebView(
                url = currentTab.url,
                onTitleChanged = { newTitle ->
                    currentTab.title = newTitle
                    tabs = tabs.toMutableList().apply { set(currentTabIndex, currentTab) }
                },
                onUrlChanged = { newUrl ->
                    currentTab.url = newUrl
                    urlInput = newUrl
                    tabs = tabs.toMutableList().apply { set(currentTabIndex, currentTab) }
                },
                onProgressChanged = { progress = it },
                modifier = Modifier.fillMaxSize()
            )
        }
    }
}
