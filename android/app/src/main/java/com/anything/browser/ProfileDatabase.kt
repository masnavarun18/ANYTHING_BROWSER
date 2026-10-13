package com.anything.browser

import android.content.Context
import androidx.room.*

@Entity(tableName = "users")
data class UserProfile(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val username: String,
    val passwordHash: String,
    val fullName: String,
    val isActive: Boolean = false,
    val createdAt: Long = System.currentTimeMillis()
)

@Entity(tableName = "history")
data class BrowserHistory(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val url: String,
    val title: String,
    val visitTime: Long = System.currentTimeMillis()
)

@Entity(tableName = "bookmarks")
data class BrowserBookmark(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val url: String,
    val title: String,
    val createdAt: Long = System.currentTimeMillis()
)

@Entity(tableName = "settings")
data class BrowserSetting(
    @PrimaryKey val key: String,
    val value: String
)

@Dao
interface BrowserDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertUser(user: UserProfile)

    @Query("SELECT * FROM users WHERE isActive = 1 LIMIT 1")
    suspend fun getActiveUser(): UserProfile?

    @Query("UPDATE users SET isActive = 0")
    suspend fun clearActiveUsers()

    @Query("SELECT * FROM users WHERE username = :username AND passwordHash = :hash LIMIT 1")
    suspend fun authenticate(username: String, hash: String): UserProfile?

    @Insert
    suspend fun addHistory(history: BrowserHistory)

    @Query("SELECT * FROM history ORDER BY visitTime DESC LIMIT 100")
    suspend fun getHistory(): List<BrowserHistory>

    @Query("DELETE FROM history")
    suspend fun clearHistory()

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun addBookmark(bookmark: BrowserBookmark)

    @Query("SELECT * FROM bookmarks ORDER BY createdAt DESC")
    suspend fun getBookmarks(): List<BrowserBookmark>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun setSetting(setting: BrowserSetting)

    @Query("SELECT value FROM settings WHERE `key` = :key LIMIT 1")
    suspend fun getSetting(key: String): String?
}

@Database(entities = [UserProfile::class, BrowserHistory::class, BrowserBookmark::class, BrowserSetting::class], version = 1)
abstract class ProfileDatabase : RoomDatabase() {
    abstract fun dao(): BrowserDao

    companion object {
        @Volatile
        private var INSTANCE: ProfileDatabase? = null

        fun getDatabase(context: Context): ProfileDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    ProfileDatabase::class.java,
                    "anything_browser.db"
                ).build()
                INSTANCE = instance
                instance
            }
        }
    }
}
